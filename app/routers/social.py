from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.groups import Group, GroupMember
from app.models.user import User
from app.models.workout_log import WorkoutLog
from app.utils.security import get_current_user_id

from app.crud.social import (
    require_group_member,
    create_achievement,
    get_user_achievements,
    create_challenge,
    update_challenge_progress,
    get_user_challenges,
    create_group,
    join_group,
    get_group_members,
    get_user_groups,
    discover_groups,
    leave_group,
    get_feed_posts,
    update_post,
    delete_post,
    delete_comment,
    update_comment,
    create_post,
    get_group_posts,
    create_comment,
    get_post_comments,
    create_reaction,
    get_post_reactions,
    get_comment_reactions
)

router = APIRouter(prefix="/social", tags=["social"])

# ---------------------------------------------------------
# Achievements
# ---------------------------------------------------------

@router.post("/achievements")
def add_achievement(
    name: str,
    description: str | None = None,
    category: str | None = None,
    icon: str | None = None,
    points: int = 0,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_achievement(db, user_id, name, description, category, icon, points)


@router.get("/achievements")
def list_achievements(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_user_achievements(db, user_id)


# ---------------------------------------------------------
# Challenges
# ---------------------------------------------------------

@router.post("/challenges")
def add_challenge(
    title: str,
    description: str | None = None,
    category: str | None = None,
    target_value: int | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_challenge(db, user_id, title, description, category, target_value)


@router.post("/challenges/{challenge_id}/progress")
def update_challenge(
    challenge_id: int,
    amount: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return update_challenge_progress(db, user_id, challenge_id, amount)


@router.get("/challenges")
def list_challenges(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_user_challenges(db, user_id)


# ---------------------------------------------------------
# Groups
# ---------------------------------------------------------

@router.post("/groups")
def create_new_group(
    name: str,
    description: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_group(db, user_id, name, description, category)


@router.post("/groups/{group_id}/join")
def join_group_route(
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return join_group(db, user_id, group_id)


@router.get("/groups/{group_id}/members")
def list_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_group_members(db, user_id, group_id)


@router.get("/groups/{group_id}/roster")
def group_roster(
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Members of a group the caller belongs to, with their last-7-days workout activity."""
    require_group_member(db, user_id, group_id)
    group = db.query(Group).filter(Group.id == group_id).first()
    member_ids = [row.user_id for row in db.query(GroupMember).filter(GroupMember.group_id == group_id).all()]
    names = {u.id: u.name or u.email for u in db.query(User).filter(User.id.in_(member_ids)).all()}
    week_ago = datetime.utcnow() - timedelta(days=7)
    logs = db.query(WorkoutLog.user_id, WorkoutLog.date).filter(
        WorkoutLog.user_id.in_(member_ids), WorkoutLog.date >= week_ago
    ).all()
    workouts: dict[int, int] = {}
    days: dict[int, set] = {}
    for member_id, when in logs:
        workouts[member_id] = workouts.get(member_id, 0) + 1
        days.setdefault(member_id, set()).add(when.date() if when else None)
    members = [
        {
            "id": member_id,
            "name": names.get(member_id, "Member"),
            "is_you": member_id == user_id,
            "workouts_7d": workouts.get(member_id, 0),
            "active_days_7d": len(days.get(member_id, set())),
        }
        for member_id in member_ids
    ]
    members.sort(key=lambda m: (-m["workouts_7d"], m["name"].lower()))
    return {"group": {"id": group.id, "name": group.name, "category": group.category}, "members": members}


@router.get("/groups")
def list_user_groups(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_user_groups(db, user_id)


@router.get("/groups/discover")
def list_discoverable_groups(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return discover_groups(db, user_id)


@router.delete("/groups/{group_id}/leave")
def leave_group_route(
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return leave_group(db, user_id, group_id)


# ---------------------------------------------------------
# Posts
# ---------------------------------------------------------

@router.post("/posts")
def add_post(
    content: str,
    group_id: int | None = None,
    media_url: str | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_post(db, user_id, content, group_id, media_url)


@router.get("/posts/group/{group_id}")
def list_group_posts(
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_group_posts(db, user_id, group_id)


@router.get("/posts")
def list_user_posts(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_feed_posts(db)


@router.put("/posts/{post_id}")
def edit_post(
    post_id: int,
    content: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return update_post(db, user_id, post_id, content)


@router.delete("/posts/{post_id}")
def remove_post(
    post_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return delete_post(db, user_id, post_id)


# ---------------------------------------------------------
# Comments
# ---------------------------------------------------------

@router.post("/posts/{post_id}/comments")
def add_comment(
    post_id: int,
    content: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_comment(db, user_id, post_id, content)


@router.get("/posts/{post_id}/comments")
def list_comments(
    post_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_post_comments(db, post_id)


@router.put("/comments/{comment_id}")
def edit_comment(
    comment_id: int,
    content: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return update_comment(db, user_id, comment_id, content)


@router.delete("/comments/{comment_id}")
def remove_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return delete_comment(db, user_id, comment_id)


# ---------------------------------------------------------
# Reactions
# ---------------------------------------------------------

@router.post("/posts/{post_id}/reactions")
def react_to_post(
    post_id: int,
    reaction_type: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_reaction(db, user_id, reaction_type, post_id=post_id)


@router.get("/posts/{post_id}/reactions")
def list_post_reactions(
    post_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_post_reactions(db, post_id)


@router.post("/comments/{comment_id}/reactions")
def react_to_comment(
    comment_id: int,
    reaction_type: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_reaction(db, user_id, reaction_type, comment_id=comment_id)


@router.get("/comments/{comment_id}/reactions")
def list_comment_reactions(
    comment_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_comment_reactions(db, comment_id)
