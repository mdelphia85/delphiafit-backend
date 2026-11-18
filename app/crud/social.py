from sqlalchemy.orm import Session

from app.models.achievements import Achievement
from app.models.challenges import Challenge
from app.models.groups import Group, GroupMember
from app.models.posts import Post
from app.models.comments import Comment
from app.models.reactions import Reaction
from fastapi import HTTPException


# ---------------------------------------------------------
# Achievements
# ---------------------------------------------------------

def create_achievement(db: Session, user_id: int, name: str, description: str = None,
                       category: str = None, icon: str = None, points: int = 0):
    achievement = Achievement(
        user_id=user_id,
        name=name,
        description=description,
        category=category,
        icon=icon,
        points=points
    )
    db.add(achievement)
    db.commit()
    db.refresh(achievement)
    return achievement


def get_user_achievements(db: Session, user_id: int):
    return db.query(Achievement).filter(Achievement.user_id == user_id).all()


# ---------------------------------------------------------
# Challenges
# ---------------------------------------------------------

def create_challenge(db: Session, user_id: int, title: str, description: str = None,
                     category: str = None, target_value: int = None):
    challenge = Challenge(
        user_id=user_id,
        title=title,
        description=description,
        category=category,
        target_value=target_value
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


def update_challenge_progress(db: Session, user_id: int, challenge_id: int, amount: int):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id, Challenge.user_id == user_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    challenge.current_value += amount

    if challenge.target_value and challenge.current_value >= challenge.target_value:
        challenge.is_completed = True

    db.commit()
    db.refresh(challenge)
    return challenge


def get_user_challenges(db: Session, user_id: int):
    return db.query(Challenge).filter(Challenge.user_id == user_id).all()


# ---------------------------------------------------------
# Groups
# ---------------------------------------------------------

def create_group(db: Session, user_id: int, name: str, description: str = None, category: str = None):
    group = Group(name=name, description=description, category=category)
    db.add(group)
    db.flush()
    db.add(GroupMember(user_id=user_id, group_id=group.id))
    db.commit()
    db.refresh(group)
    return {"id": group.id, "name": group.name, "description": group.description, "category": group.category}


def join_group(db: Session, user_id: int, group_id: int):
    if not db.query(Group).filter(Group.id == group_id).first():
        raise HTTPException(status_code=404, detail="Group not found")
    existing = db.query(GroupMember).filter_by(user_id=user_id, group_id=group_id).first()
    if existing:
        return existing
    membership = GroupMember(user_id=user_id, group_id=group_id)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return {"id": membership.id, "group_id": membership.group_id, "user_id": membership.user_id}


def get_group_members(db: Session, user_id: int, group_id: int):
    require_group_member(db, user_id, group_id)
    return db.query(GroupMember).filter(GroupMember.group_id == group_id).all()


def require_group_member(db: Session, user_id: int, group_id: int):
    if not db.query(GroupMember).filter_by(user_id=user_id, group_id=group_id).first():
        raise HTTPException(status_code=404, detail="Group not found")


def discover_groups(db: Session, user_id: int):
    joined = db.query(GroupMember.group_id).filter(GroupMember.user_id == user_id)
    groups = db.query(Group).filter(~Group.id.in_(joined)).order_by(Group.name).all()
    return [{"id": group.id, "name": group.name, "description": group.description,
             "category": group.category, "member_count": len(group.members)} for group in groups]


def leave_group(db: Session, user_id: int, group_id: int):
    membership = db.query(GroupMember).filter_by(user_id=user_id, group_id=group_id).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Group membership not found")
    db.delete(membership)
    db.commit()
    return {"success": True}


def get_user_groups(db: Session, user_id: int):
    memberships = db.query(GroupMember).filter(GroupMember.user_id == user_id).all()
    return [{"id": m.group.id, "name": m.group.name, "description": m.group.description,
             "category": m.group.category, "member_count": len(m.group.members),
             "role": "member", "membership_id": m.id} for m in memberships]


# ---------------------------------------------------------
# Posts
# ---------------------------------------------------------

def create_post(db: Session, user_id: int, content: str, group_id: int = None, media_url: str = None):
    if group_id is not None:
        require_group_member(db, user_id, group_id)
    post = Post(
        user_id=user_id,
        content=content,
        group_id=group_id,
        media_url=media_url
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_group_posts(db: Session, user_id: int, group_id: int):
    require_group_member(db, user_id, group_id)
    return _serialize_posts(db, db.query(Post).filter(Post.group_id == group_id).order_by(Post.created_at.desc()).all())


def get_feed_posts(db: Session):
    return _serialize_posts(db, db.query(Post).order_by(Post.created_at.desc()).all())


def _serialize_posts(db: Session, posts):
    result = []
    for post in posts:
        result.append({
            "id": post.id, "user_id": post.user_id, "group_id": post.group_id,
            "content": post.content, "media_url": post.media_url, "created_at": post.created_at,
            "comments": [{"id": c.id, "user_id": c.user_id, "content": c.content, "created_at": c.created_at}
                         for c in db.query(Comment).filter(Comment.post_id == post.id).order_by(Comment.created_at.asc()).all()],
            "reactions": [{"id": r.id, "user_id": r.user_id, "reaction_type": r.reaction_type}
                          for r in db.query(Reaction).filter(Reaction.post_id == post.id).all()]
        })
    return result


def update_post(db: Session, user_id: int, post_id: int, content: str):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not the post author")
    post.content = content
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, user_id: int, post_id: int):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not the post author")
    db.delete(post)
    db.commit()
    return {"success": True}


def get_user_posts(db: Session, user_id: int):
    return db.query(Post).filter(Post.user_id == user_id).all()


# ---------------------------------------------------------
# Comments
# ---------------------------------------------------------

def create_comment(db: Session, user_id: int, post_id: int, content: str):
    if not db.query(Post).filter_by(id=post_id).first():
        raise HTTPException(status_code=404, detail="Post not found")
    comment = Comment(
        user_id=user_id,
        post_id=post_id,
        content=content
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_post_comments(db: Session, post_id: int):
    return db.query(Comment).filter(Comment.post_id == post_id).order_by(Comment.created_at.asc()).all()


def update_comment(db: Session, user_id: int, comment_id: int, content: str):
    comment = db.query(Comment).filter_by(id=comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not the comment author")
    comment.content = content
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, user_id: int, comment_id: int):
    comment = db.query(Comment).filter_by(id=comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not the comment author")
    db.delete(comment)
    db.commit()
    return {"success": True}


# ---------------------------------------------------------
# Reactions
# ---------------------------------------------------------

def create_reaction(db: Session, user_id: int, reaction_type: str,
                    post_id: int = None, comment_id: int = None):
    if post_id is not None and not db.query(Post).filter_by(id=post_id).first():
        raise HTTPException(status_code=404, detail="Post not found")
    if comment_id is not None and not db.query(Comment).filter_by(id=comment_id).first():
        raise HTTPException(status_code=404, detail="Comment not found")
    existing = db.query(Reaction).filter_by(user_id=user_id, reaction_type=reaction_type,
                                             post_id=post_id, comment_id=comment_id).first()
    if existing:
        return existing
    reaction = Reaction(
        user_id=user_id,
        reaction_type=reaction_type,
        post_id=post_id,
        comment_id=comment_id
    )
    db.add(reaction)
    db.commit()
    db.refresh(reaction)
    return reaction


def get_post_reactions(db: Session, post_id: int):
    return db.query(Reaction).filter(Reaction.post_id == post_id).all()


def get_comment_reactions(db: Session, comment_id: int):
    return db.query(Reaction).filter(Reaction.comment_id == comment_id).all()
