from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.connection import Base


class CoachTeamMembership(Base):
    __tablename__ = "coach_team_memberships"
    __table_args__ = (UniqueConstraint("coach_id", "team_id", name="uq_coach_team_membership"),)

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    role = Column(String, default="assistant_coach", nullable=False)

    coach = relationship("Coach", back_populates="team_memberships")
    team = relationship("Team", back_populates="coach_memberships")
