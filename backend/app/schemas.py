import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import EventType, ProjectStatus, SummaryType


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    created_at: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    user: UserOut
    tokens: TokenPair


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------- Devices ----------
class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, default="My laptop")


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    api_key_prefix: str
    last_seen: datetime | None
    created_at: datetime


class DeviceCreated(DeviceOut):
    api_key: str


# ---------- Projects ----------
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    status: ProjectStatus | None = None


class RepositoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    remote_url: str | None
    local_identifier: str
    created_at: datetime


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    status: ProjectStatus
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime | None = None
    event_count: int = 0
    repository_count: int = 0


# ---------- Events ----------
class RepositoryRef(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    local_identifier: str = Field(min_length=1, max_length=512)
    remote_url: str | None = Field(default=None, max_length=512)


class EventCreate(BaseModel):
    event_type: EventType
    repository: RepositoryRef
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: EventType
    payload: dict[str, Any]
    created_at: datetime
    repository_id: uuid.UUID
    repository_name: str | None = None
    project_id: uuid.UUID | None = None
    project_name: str | None = None


class EventAccepted(BaseModel):
    event_id: uuid.UUID
    project_id: uuid.UUID
    repository_id: uuid.UUID
    created_project: bool = False
    created_repository: bool = False


# ---------- AI summaries ----------
class SummaryGenerate(BaseModel):
    summary_type: SummaryType = SummaryType.PROJECT
    days: int = Field(default=7, ge=1, le=90)


class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    summary: str
    summary_type: SummaryType
    created_at: datetime


class ProjectDetail(ProjectOut):
    repositories: list[RepositoryOut] = Field(default_factory=list)
    recent_events: list[EventOut] = Field(default_factory=list)
    latest_summary: SummaryOut | None = None
    summary_count: int = 0


# ---------- Dashboard / insights ----------
class DashboardOut(BaseModel):
    active_projects: int
    total_projects: int
    total_events: int
    last_active_project: ProjectOut | None
    recent_activity: list[EventOut]
    latest_summary: SummaryOut | None


class InsightFeed(BaseModel):
    summaries: list[SummaryOut]
    projects: list[ProjectOut]
