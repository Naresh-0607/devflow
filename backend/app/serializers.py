import uuid
from datetime import datetime

from app.models import GitEvent, Project
from app.schemas import EventOut, ProjectOut, SummaryOut
from app.services.events import parse_payload


def event_out(event: GitEvent) -> EventOut:
    repository = getattr(event, "repository", None)
    project = getattr(repository, "project", None) if repository else None
    return EventOut(
        id=event.id,
        event_type=event.event_type,
        payload=parse_payload(event),
        created_at=event.created_at,
        repository_id=event.repository_id,
        repository_name=repository.name if repository else None,
        project_id=project.id if project else (repository.project_id if repository else None),
        project_name=project.name if project else None,
    )


def project_out(
    project: Project,
    last_activity: datetime | None = None,
    event_count: int = 0,
    repository_count: int = 0,
) -> ProjectOut:
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        started_at=project.started_at,
        completed_at=project.completed_at,
        created_at=project.created_at,
        updated_at=project.updated_at,
        last_activity_at=last_activity,
        event_count=event_count,
        repository_count=repository_count,
    )


def summary_out(summary) -> SummaryOut:
    return SummaryOut(
        id=summary.id,
        project_id=summary.project_id,
        summary=summary.summary,
        summary_type=summary.summary_type,
        created_at=summary.created_at,
    )
