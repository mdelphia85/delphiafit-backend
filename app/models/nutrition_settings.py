from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String

from app.database.connection import Base


class NutritionSettings(Base):
    """Per-user goals, nutrition preferences and manual target overrides."""

    __tablename__ = "nutrition_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    goal_type = Column(String, nullable=True)  # lose | maintain | gain
    target_weight = Column(Float, nullable=True)
    weekly_rate = Column(Float, nullable=True)
    goal_unit = Column(String, default="lbs", nullable=False)

    calorie_override = Column(Integer, nullable=True)
    protein_override = Column(Integer, nullable=True)
    carbs_override = Column(Integer, nullable=True)
    fat_override = Column(Integer, nullable=True)

    diet = Column(String, default="none", nullable=False)
    avoid_json = Column(JSON, nullable=True)
    meals_per_day = Column(Integer, default=5, nullable=False)

    # Non-nutrition fields from the Goals page (custom goal, mood, habits, reminder).
    extras_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GeneratedMealPlan(Base):
    """A saved generated plan. Generating one never records food as consumed."""

    __tablename__ = "generated_meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
