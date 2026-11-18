from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InviteSummary(BaseModel):
    id: int
    email: str
    role: str
    team_id: int | None = None
    accepted: bool
    expires_at: datetime | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PendingInviteSummary(BaseModel):
    id: int
    email: str
    role: str
    team_id: int | None = None
    accepted: bool
    expired: bool
    created_at: datetime | None = None


class PendingInviteList(BaseModel):
    invitations: list[PendingInviteSummary]
