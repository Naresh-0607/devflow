import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbSession
from app.models import AISummary, Project, SummaryType, utcnow
from app.schemas import InsightFeed, ProjectOut, SummaryGenerate, SummaryOut
from app.serializers import project_out, summary_out
from app.services.ai import describe_event, generate_summary
from app.services.events import events_in_window, project_stats

router = APIRouter(tags=["insights"])

_WINDOW_DAYS = {
    SummaryType.DAILY: 1,
    SummaryType.WEEKLY: 7,
    SummaryType.PROJECT: None,
}


async def _get_project(db: DbSession, user_id, project_id: uuid.UUID) -> Project:
    project = (
        await db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/insights", response_model=InsightFeed)
async def get_insights(
    user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=30, ge=1, le=100),
) -> InsightFeed:
    summaries = (
        await db.execute(
            select(AISummary)
            .join(Project, AISummary.project_id == Project.id)
            .where(Project.user_id == user.id)
            .order_by(AISummary.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()

    projects = (
        await db.execute(
            select(Project).where(Project.user_id == user.id).order_by(Project.updated_at.desc())
        )
    ).scalars().all()

    project_outputs: list[ProjectOut] = []
    for project in projects:
        last_activity, event_count, repo_count = await project_stats(db, project.id)
        project_outputs.append(project_out(project, last_activity, event_count, repo_count))

    return InsightFeed(
        summaries=[summary_out(summary) for summary in summaries],
        projects=project_outputs,
    )


@router.get("/projects/{project_id}/summaries", response_model=list[SummaryOut])
async def list_summaries(
    project_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> list[SummaryOut]:
    await _get_project(db, user.id, project_id)
    summaries = (
        await db.execute(
            select(AISummary)
            .where(AISummary.project_id == project_id)
            .order_by(AISummary.created_at.desc())
        )
    ).scalars().all()
    return [summary_out(summary) for summary in summaries]


@router.post("/projects/{project_id}/summaries", response_model=SummaryOut, status_code=201)
async def create_summary(
    project_id: uuid.UUID,
    payload: SummaryGenerate,
    user: CurrentUser,
    db: DbSession,
) -> SummaryOut:
    project = await _get_project(db, user.id, project_id)
    days = payload.days if payload.summary_type == SummaryType.WEEKLY else _WINDOW_DAYS[payload.summary_type]
    events = await events_in_window(db, project.id, days)

    lines = [describe_event(event) for event in events][-100:]
    text = await generate_summary(project.name, lines, payload.summary_type)

    summary = AISummary(
        project_id=project.id,
        summary=text,
        summary_type=payload.summary_type,
        created_at=utcnow(),
    )
    db.add(summary)
    project.updated_at = utcnow()
    await db.commit()
    await db.refresh(summary)
    return summary_out(summary)
