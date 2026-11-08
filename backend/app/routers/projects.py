import uuid

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbSession, ensure_utc
from app.models import AISummary, Project, ProjectStatus, Repository, utcnow
from app.schemas import (
    ProjectCreate,
    ProjectDetail,
    ProjectOut,
    ProjectUpdate,
    RepositoryOut,
)
from app.serializers import event_out, project_out, summary_out
from app.services.events import list_events_for_project, project_stats

router = APIRouter(prefix="/projects", tags=["projects"])


async def _get_project(db: DbSession, user_id, project_id: uuid.UUID) -> Project:
    project = (
        await db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=list[ProjectOut])
async def list_projects(user: CurrentUser, db: DbSession) -> list[ProjectOut]:
    projects = (
        await db.execute(
            select(Project)
            .where(Project.user_id == user.id)
            .order_by(Project.updated_at.desc())
        )
    ).scalars()
    result: list[ProjectOut] = []
    for project in projects:
        last_activity, event_count, repo_count = await project_stats(db, project.id)
        result.append(project_out(project, last_activity, event_count, repo_count))
    return result


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate, user: CurrentUser, db: DbSession
) -> ProjectOut:
    project = Project(
        user_id=user.id,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        started_at=utcnow(),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project_out(project)


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: uuid.UUID, user: CurrentUser, db: DbSession) -> ProjectDetail:
    project = await _get_project(db, user.id, project_id)
    repositories = (
        await db.execute(
            select(Repository)
            .where(Repository.project_id == project.id)
            .order_by(Repository.created_at.asc())
        )
    ).scalars().all()
    events = await list_events_for_project(db, project.id, limit=50)
    last_activity, event_count, _ = await project_stats(db, project.id)
    latest_summary = (
        await db.execute(
            select(AISummary)
            .where(AISummary.project_id == project.id)
            .order_by(AISummary.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    base = project_out(project, last_activity, event_count, len(repositories))
    return ProjectDetail(
        **base.model_dump(),
        repositories=[RepositoryOut.model_validate(repo) for repo in repositories],
        recent_events=[event_out(event) for event in events],
        latest_summary=summary_out(latest_summary) if latest_summary else None,
    )


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: uuid.UUID, payload: ProjectUpdate, user: CurrentUser, db: DbSession
) -> ProjectOut:
    project = await _get_project(db, user.id, project_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(project, field, value)

    if payload.status == ProjectStatus.COMPLETED and project.completed_at is None:
        project.completed_at = ensure_utc(utcnow())
    if payload.status is not None and payload.status != ProjectStatus.COMPLETED:
        project.completed_at = None

    await db.commit()
    await db.refresh(project)
    last_activity, event_count, repo_count = await project_stats(db, project.id)
    return project_out(project, last_activity, event_count, repo_count)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: uuid.UUID, user: CurrentUser, db: DbSession) -> Response:
    project = await _get_project(db, user.id, project_id)
    await db.delete(project)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
