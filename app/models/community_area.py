from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from app.database.connection import Base


class AcademyProgress(Base):
    __tablename__ = "academy_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sport = Column(String(80), nullable=False)
    drill = Column(String(160), nullable=False)
    completed = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "sport", "drill", name="uq_academy_progress_user_drill"),)


class CompetitionRegistration(Base):
    __tablename__ = "competition_registrations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "competition_id", name="uq_competition_registration_user"),)


class FederationMembership(Base):
    __tablename__ = "federation_memberships"
    id = Column(Integer, primary_key=True, index=True)
    federation_id = Column(Integer, ForeignKey("federations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="member")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("federation_id", "user_id", name="uq_federation_membership_user"),)


class RecruitingProfile(Base):
    __tablename__ = "recruiting_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    sport = Column(String(80), nullable=False)
    position = Column(String(80), nullable=True)
    bio = Column(Text, nullable=True)
    public = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ListingInterest(Base):
    __tablename__ = "listing_interests"
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("listing_id", "user_id", name="uq_listing_interest_user"),)


class ChildProfile(Base):
    __tablename__ = "child_profiles"
    id = Column(Integer, primary_key=True, index=True)
    parent_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    nickname = Column(String(40), nullable=False)
    parent_controls_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ChildProgress(Base):
    __tablename__ = "child_progress"
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("child_profiles.id"), nullable=False, index=True)
    activity_key = Column(String(80), nullable=False)
    completed = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint("child_id", "activity_key", name="uq_child_activity"),)


class SocialFollow(Base):
    __tablename__ = "social_follows"
    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    followed_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("follower_id", "followed_id", name="uq_social_follow"),)


class TournamentRegistration(Base):
    __tablename__ = "tournament_registrations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "tournament_id", name="uq_tournament_registration_user"),)
