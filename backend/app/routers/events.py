import uuid

from fastapi import APIRouter, Query, status
from sqlalchemy import select

from app.deps import CurrentDevice, CurrentUser, DbSession
from app.models import GitEvent, Project, Repository, User
from app.schemas import EventAccepted, EventCreate, EventOut
from app.serializers import event_out
from app.services.events import ingest_event
from app.services.rate_limit import event_rate_limiter

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventAccepted, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate, device: CurrentDevice, db: DbSession
) -> EventAccepted:
    # One API key == one device; rate limit by device so a noisy repo cannot
    # exhaust another machine's budget.
    event_rate_limiter.check(str(device.id))

    user = await db.get(User, device.user_id)
    result = await ingest_event(db, user, payload)
    return EventAccepted(
        event_id=result.event.id,
        project_id=result.project.id,
        repository_id=result.repository.id,
        created_project=result.created_project,
        created_repository=result.created_repository,
    )


@router.get("", response_model=list[EventOut])
async def list_events(
    user: CurrentUser,
    db: DbSession,
    project_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[EventOut]:
    stmt = (
        select(GitEvent)
        .join(Repository, GitEvent.repository_id == Repository.id)
        .join(Project, Repository.project_id == Project.id)
        .where(Project.user_id == user.id)
    )
    if project_id is not None:
        stmt = stmt.where(Repository.project_id == project_id)

    stmt = (
        stmt.order_by(GitEvent.created_at.desc())
        .limit(limit)
        .offset(offset)
        .options()
    )

    # Load relations explicitly to keep everything async-safe.
    from sqlalchemy.orm import selectinload

    stmt = stmt.options(selectinload(GitEvent.repository).selectinload(Repository.project))
    events = (await db.execute(stmt)).scalars().all()
    return [event_out(event) for event in events]
