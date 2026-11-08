from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbSession
from app.models import AISummary, GitEvent, Project, ProjectStatus, Repository
from app.schemas import DashboardOut
from app.serializers import event_out, project_out, summary_out
from app.services.events import project_stats, recent_events_for_user

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
async def get_dashboard(user: CurrentUser, db: DbSession) -> DashboardOut:
    total_projects = (
        await db.execute(select(func.count(Project.id)).where(Project.user_id == user.id))
    ).scalar_one()
    active_projects = (
        await db.execute(
            select(func.count(Project.id)).where(
                Project.user_id == user.id, Project.status == ProjectStatus.ACTIVE
            )
        )
    ).scalar_one()
    total_events = (
        await db.execute(
            select(func.count(GitEvent.id))
            .join(Repository, GitEvent.repository_id == Repository.id)
            .join(Project, Repository.project_id == Project.id)
            .where(Project.user_id == user.id)
        )
    ).scalar_one()

    recent_events = await recent_events_for_user(db, user.id, limit=15)

    latest_summary = (
        await db.execute(
            select(AISummary)
            .join(Project, AISummary.project_id == Project.id)
            .where(Project.user_id == user.id)
            .order_by(AISummary.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    last_project = (
        await db.execute(
            select(Project)
            .where(Project.user_id == user.id)
            .order_by(Project.updated_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    last_project_out = None
    if last_project is not None:
        last_activity, event_count, repo_count = await project_stats(db, last_project.id)
        last_project_out = project_out(last_project, last_activity, event_count, repo_count)

    return DashboardOut(
        active_projects=active_projects,
        total_projects=total_projects,
        total_events=total_events,
        last_active_project=last_project_out,
        recent_activity=[event_out(event) for event in recent_events],
        latest_summary=summary_out(latest_summary) if latest_summary else None,
    )
