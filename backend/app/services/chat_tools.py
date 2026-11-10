"""Read-only chat tools.

Every query is scoped to a single user. The model never receives database
access or arbitrary SQL; it can only call these fixed functions.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AISummary, EventType, GitEvent, Project, ProjectStatus, Repository
from app.services.events import parse_payload, project_metrics_bulk

MAX_EVENTS = 50
MAX_SUMMARIES = 10
MAX_STATS_EVENTS = 5000


def _payload(event: GitEvent) -> dict[str, Any]:
    value = parse_payload(event)
    return value if isinstance(value, dict) else {}


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _event_dict(event: GitEvent) -> dict[str, Any]:
    payload = _payload(event)
    repository = getattr(event, "repository", None)
    project = getattr(repository, "project", None) if repository else None
    return {
        "id": str(event.id),
        "event_type": event.event_type,
        "created_at": _iso(event.created_at),
        "project": project.name if project else None,
        "repository": repository.name if repository else None,
        "message": payload.get("message"),
        "branch": payload.get("branch") or payload.get("to_branch"),
        "from_branch": payload.get("from_branch"),
        "sha": payload.get("sha"),
    }


def _like_pattern(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


async def _resolve_project(
    db: AsyncSession, user_id: uuid.UUID, name_or_id: str | None
) -> Project | None:
    if not name_or_id:
        return None

    candidate_id: uuid.UUID | None = None
    try:
        candidate_id = uuid.UUID(str(name_or_id))
    except (ValueError, AttributeError):
        candidate_id = None

    if candidate_id is not None:
        project = (
            await db.execute(
                select(Project).where(
                    Project.id == candidate_id, Project.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        if project is not None:
            return project

    needle = str(name_or_id).strip()
    if not needle:
        return None

    stmt = (
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.updated_at.desc())
        .limit(1)
    )
    exact = await db.execute(stmt.where(func.lower(Project.name) == needle.lower()))
    project = exact.scalar_one_or_none()
    if project is not None:
        return project
    partial = await db.execute(stmt.where(Project.name.ilike(_like_pattern(needle), escape="\\")))
    return partial.scalar_one_or_none()


async def list_projects(
    db: AsyncSession, user_id: uuid.UUID, status: str | None = None
) -> dict[str, Any]:
    stmt = select(Project).where(Project.user_id == user_id).order_by(Project.updated_at.desc())
    if status:
        wanted = status.upper()
        if wanted not in ProjectStatus.__members__:
            return {"error": f"Unknown status '{status}'", "projects": [], "count": 0}
        stmt = stmt.where(Project.status == ProjectStatus[wanted])
    projects = list((await db.execute(stmt.limit(MAX_EVENTS))).scalars().all())
    metrics = await project_metrics_bulk(db, [project.id for project in projects])

    rows = []
    for project in projects:
        last_activity, event_count, repo_count = metrics.get(project.id, (None, 0, 0))
        rows.append(
            {
                "id": str(project.id),
                "name": project.name,
                "status": project.status,
                "started_at": _iso(project.started_at),
                "last_activity_at": _iso(last_activity),
                "event_count": event_count,
                "repository_count": repo_count,
            }
        )
    return {"projects": rows, "count": len(rows)}


async def get_project(
    db: AsyncSession, user_id: uuid.UUID, name_or_id: str
) -> dict[str, Any]:
    project = await _resolve_project(db, user_id, name_or_id)
    if project is None:
        return {"error": "Project not found", "project": None}

    last_activity = (
        await db.execute(
            select(func.max(GitEvent.created_at))
            .join(Repository, GitEvent.repository_id == Repository.id)
            .where(Repository.project_id == project.id)
        )
    ).scalar_one()
    repository_count = (
        await db.execute(
            select(func.count(Repository.id)).where(Repository.project_id == project.id)
        )
    ).scalar_one()
    summary_count = (
        await db.execute(
            select(func.count(AISummary.id)).where(AISummary.project_id == project.id)
        )
    ).scalar_one()
    latest_event = (
        await db.execute(
            select(GitEvent)
            .join(Repository, GitEvent.repository_id == Repository.id)
            .where(Repository.project_id == project.id)
            .order_by(GitEvent.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    payload = _payload(latest_event) if latest_event else {}
    focus = payload.get("branch") or payload.get("to_branch")

    return {
        "project": {
            "id": str(project.id),
            "name": project.name,
            "status": project.status,
            "started_at": _iso(project.started_at),
            "completed_at": _iso(project.completed_at),
            "last_activity_at": _iso(last_activity),
            "current_branch": focus,
            "repository_count": repository_count,
            "summary_count": summary_count,
        }
    }


async def get_timeline(
    db: AsyncSession,
    user_id: uuid.UUID,
    project: str | None = None,
    since: str | None = None,
    until: str | None = None,
    event_type: str | None = None,
    limit: int = MAX_EVENTS,
) -> dict[str, Any]:
    stmt = (
        select(GitEvent)
        .join(Repository, GitEvent.repository_id == Repository.id)
        .join(Project, Repository.project_id == Project.id)
        .where(Project.user_id == user_id)
        .order_by(GitEvent.created_at.desc())
    )
    if project:
        resolved = await _resolve_project(db, user_id, project)
        if resolved is None:
            return {"error": "Project not found", "events": [], "count": 0}
        stmt = stmt.where(Repository.project_id == resolved.id)
    since_dt = _parse_dt(since)
    until_dt = _parse_dt(until)
    if since_dt:
        stmt = stmt.where(GitEvent.created_at >= since_dt)
    if until_dt:
        stmt = stmt.where(GitEvent.created_at <= until_dt)
    if event_type:
        normalized = event_type.lower()
        if normalized not in EventType._value2member_map_:
            return {"error": f"Unknown event type '{event_type}'", "events": [], "count": 0}
        stmt = stmt.where(GitEvent.event_type == normalized)

    capped = min(max(int(limit), 1), MAX_EVENTS)
    events = (
        await db.execute(
            stmt.limit(capped).options(
                selectinload(GitEvent.repository).selectinload(Repository.project)
            )
        )
    ).scalars().all()
    return {
        "project": project or "all projects",
        "events": [_event_dict(event) for event in events],
        "count": len(events),
    }


async def search_events(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    project: str | None = None,
    limit: int = MAX_EVENTS,
) -> dict[str, Any]:
    needle = (query or "").strip()
    if not needle:
        return {"events": [], "count": 0, "query": query}

    stmt = (
        select(GitEvent)
        .join(Repository, GitEvent.repository_id == Repository.id)
        .join(Project, Repository.project_id == Project.id)
        .where(Project.user_id == user_id)
        .order_by(GitEvent.created_at.desc())
    )
    if project:
        resolved = await _resolve_project(db, user_id, project)
        if resolved is None:
            return {"error": "Project not found", "events": [], "count": 0}
        stmt = stmt.where(Repository.project_id == resolved.id)

    pattern = _like_pattern(needle[:200])
    stmt = stmt.where(
        or_(
            GitEvent.payload_json.ilike(pattern, escape="\\"),
            Repository.name.ilike(pattern, escape="\\"),
            Project.name.ilike(pattern, escape="\\"),
        )
    )

    capped = min(max(int(limit), 1), MAX_EVENTS)
    events = (
        await db.execute(
            stmt.limit(capped).options(
                selectinload(GitEvent.repository).selectinload(Repository.project)
            )
        )
    ).scalars().all()
    return {
        "query": needle,
        "events": [_event_dict(event) for event in events],
        "count": len(events),
    }


async def get_summaries(
    db: AsyncSession,
    user_id: uuid.UUID,
    project: str | None = None,
    summary_type: str | None = None,
    limit: int = MAX_SUMMARIES,
) -> dict[str, Any]:
    stmt = (
        select(AISummary)
        .join(Project, AISummary.project_id == Project.id)
        .where(Project.user_id == user_id)
        .order_by(AISummary.created_at.desc())
    )
    if project:
        resolved = await _resolve_project(db, user_id, project)
        if resolved is None:
            return {"error": "Project not found", "summaries": [], "count": 0}
        stmt = stmt.where(AISummary.project_id == resolved.id)
    if summary_type:
        normalized = summary_type.upper()
        if normalized not in ("DAILY", "WEEKLY", "PROJECT"):
            return {"error": f"Unknown summary type '{summary_type}'", "summaries": [], "count": 0}
        stmt = stmt.where(AISummary.summary_type == normalized)

    capped = min(max(int(limit), 1), MAX_SUMMARIES)
    summaries = (await db.execute(stmt.limit(capped))).scalars().all()
    return {
        "summaries": [
            {
                "id": str(summary.id),
                "project_id": str(summary.project_id),
                "summary": summary.summary,
                "summary_type": summary.summary_type,
                "created_at": _iso(summary.created_at),
            }
            for summary in summaries
        ],
        "count": len(summaries),
    }


async def get_stats(
    db: AsyncSession,
    user_id: uuid.UUID,
    project: str | None = None,
    since: str | None = None,
) -> dict[str, Any]:
    stmt = (
        select(GitEvent)
        .join(Repository, GitEvent.repository_id == Repository.id)
        .join(Project, Repository.project_id == Project.id)
        .where(Project.user_id == user_id)
        .order_by(GitEvent.created_at.desc())
    )
    if project:
        resolved = await _resolve_project(db, user_id, project)
        if resolved is None:
            return {"error": "Project not found", "stats": None}
        stmt = stmt.where(Repository.project_id == resolved.id)

    since_dt = _parse_dt(since)
    if since_dt:
        stmt = stmt.where(GitEvent.created_at >= since_dt)

    events = list((await db.execute(stmt.limit(MAX_STATS_EVENTS))).scalars().all())
    commits = sum(1 for event in events if event.event_type == EventType.COMMIT.value)
    branches: set[str] = set()
    active_days: set[str] = set()
    for event in events:
        payload = _payload(event)
        branch = payload.get("branch") or payload.get("to_branch")
        if isinstance(branch, str) and branch:
            branches.add(branch)
        created = event.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        active_days.add(created.astimezone(timezone.utc).date().isoformat())

    return {
        "stats": {
            "events": len(events),
            "commits": commits,
            "branches_touched": sorted(branches)[:50],
            "branch_count": len(branches),
            "active_days": sorted(active_days)[-90:],
            "active_day_count": len(active_days),
            "first_event_at": _iso(events[-1].created_at) if events else None,
            "last_event_at": _iso(events[0].created_at) if events else None,
        }
    }
