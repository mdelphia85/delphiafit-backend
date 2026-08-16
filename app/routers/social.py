from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.crud.social import (
    create_achievement,
    get_user_achievements,
    create_challenge,
    update_challenge_progress,
    get_user_challenges,
    create_group,
    join_group,
    get_group_members,
    get_user_groups,
    create_post,
    get_group_posts,
    get_user_posts,
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
    db: Session = Depends(get_db)
):
    return update_challenge_progress(db, challenge_id, amount)


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
    db: Session = Depends(get_db)
):
    return create_group(db, name, description, category)


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
    db: Session = Depends(get_db)
):
    return get_group_members(db, group_id)


@router.get("/groups")
def list_user_groups(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_user_groups(db, user_id)


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
    db: Session = Depends(get_db)
):
    return get_group_posts(db, group_id)


@router.get("/posts")
def list_user_posts(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_user_posts(db, user_id)


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
    db: Session = Depends(get_db)
):
    return get_post_comments(db, post_id)


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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    return get_comment_reactions(db, comment_id)
