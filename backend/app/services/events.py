import json
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import ensure_utc
from app.models import GitEvent, Project, ProjectStatus, Repository, User, utcnow
from app.schemas import EventCreate


class IngestionResult:
    def __init__(
        self,
        event: GitEvent,
        project: Project,
        repository: Repository,
        created_project: bool,
        created_repository: bool,
    ) -> None:
        self.event = event
        self.project = project
        self.repository = repository
        self.created_project = created_project
        self.created_repository = created_repository


async def get_repository_for_user(
    db: AsyncSession, user_id, identifier: str
) -> Repository | None:
    stmt = (
        select(Repository)
        .join(Project, Repository.project_id == Project.id)
        .where(Project.user_id == user_id, Repository.local_identifier == identifier)
        .options(selectinload(Repository.project))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def ingest_event(db: AsyncSession, user: User, data: EventCreate) -> IngestionResult:
    occurred_at = ensure_utc(data.occurred_at) if data.occurred_at else utcnow()
    repo_ref = data.repository

    repository = await get_repository_for_user(db, user.id, repo_ref.local_identifier)
    created_repository = False
    created_project = False

    project: Project
    if repository is None:
        project = Project(
            user_id=user.id,
            name=repo_ref.name,
            status=ProjectStatus.ACTIVE,
            started_at=occurred_at,
        )
        db.add(project)
        await db.flush()
        repository = Repository(
            project_id=project.id,
            name=repo_ref.name,
            remote_url=repo_ref.remote_url,
            local_identifier=repo_ref.local_identifier,
        )
        db.add(repository)
        await db.flush()
        created_project = True
        created_repository = True
    else:
        project = repository.project
        if repo_ref.remote_url and not repository.remote_url:
            repository.remote_url = repo_ref.remote_url
        # A project becomes active again as soon as new work lands.
        if project.status in (ProjectStatus.PAUSED, ProjectStatus.ARCHIVED):
            project.status = ProjectStatus.ACTIVE

    if data.event_type == "repository_created":
        project.started_at = min(ensure_utc(project.started_at), occurred_at)

    event = GitEvent(
        repository_id=repository.id,
        event_type=data.event_type,
        payload_json=json.dumps(data.payload, ensure_ascii=False),
        created_at=occurred_at,
    )
    db.add(event)
    project.updated_at = occurred_at
    await db.commit()
    await db.refresh(event)

    return IngestionResult(event, project, repository, created_project, created_repository)


async def project_stats(db: AsyncSession, project_id) -> tuple[datetime | None, int, int]:
    event_count = (
        await db.execute(
            select(func.count(GitEvent.id))
            .join(Repository, GitEvent.repository_id == Repository.id)
            .where(Repository.project_id == project_id)
        )
    ).scalar_one()
    repo_count = (
        await db.execute(
            select(func.count(Repository.id)).where(Repository.project_id == project_id)
        )
    ).scalar_one()
    last_activity = (
        await db.execute(
            select(func.max(GitEvent.created_at))
            .join(Repository, GitEvent.repository_id == Repository.id)
            .where(Repository.project_id == project_id)
        )
    ).scalar_one()
    return last_activity, event_count, repo_count


async def list_events_for_project(
    db: AsyncSession, project_id, limit: int = 50, offset: int = 0
) -> list[GitEvent]:
    stmt = (
        select(GitEvent)
        .join(Repository, GitEvent.repository_id == Repository.id)
        .where(Repository.project_id == project_id)
        .order_by(GitEvent.created_at.desc())
        .limit(limit)
        .offset(offset)
        .options(selectinload(GitEvent.repository))
    )
    return list((await db.execute(stmt)).scalars().all())


async def recent_events_for_user(db: AsyncSession, user_id, limit: int = 20) -> list[GitEvent]:
    stmt = (
        select(GitEvent)
        .join(Repository, GitEvent.repository_id == Repository.id)
        .join(Project, Repository.project_id == Project.id)
        .where(Project.user_id == user_id)
        .order_by(GitEvent.created_at.desc())
        .limit(limit)
        .options(selectinload(GitEvent.repository).selectinload(Repository.project))
    )
    return list((await db.execute(stmt)).scalars().all())


async def events_in_window(
    db: AsyncSession, project_id, days: int | None
) -> list[GitEvent]:
    stmt = (
        select(GitEvent)
        .join(Repository, GitEvent.repository_id == Repository.id)
        .where(Repository.project_id == project_id)
    )
    if days:
        cutoff = utcnow() - timedelta(days=days)
        stmt = stmt.where(GitEvent.created_at >= cutoff)
    stmt = stmt.order_by(GitEvent.created_at.asc())
    return list((await db.execute(stmt)).scalars().all())


def parse_payload(event: GitEvent) -> dict:
    try:
        value = json.loads(event.payload_json or "{}")
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}
