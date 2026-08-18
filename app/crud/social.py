from sqlalchemy.orm import Session

from app.models.achievements import Achievement
from app.models.challenges import Challenge
from app.models.groups import Group, GroupMember
from app.models.posts import Post
from app.models.comments import Comment
from app.models.reactions import Reaction


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


def update_challenge_progress(db: Session, challenge_id: int, amount: int):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        return None

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

def create_group(db: Session, name: str, description: str = None, category: str = None):
    group = Group(name=name, description=description, category=category)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def join_group(db: Session, user_id: int, group_id: int):
    membership = GroupMember(user_id=user_id, group_id=group_id)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def get_group_members(db: Session, group_id: int):
    return db.query(GroupMember).filter(GroupMember.group_id == group_id).all()


def get_user_groups(db: Session, user_id: int):
    return db.query(GroupMember).filter(GroupMember.user_id == user_id).all()


# ---------------------------------------------------------
# Posts
# ---------------------------------------------------------

def create_post(db: Session, user_id: int, content: str, group_id: int = None, media_url: str = None):
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


def get_group_posts(db: Session, group_id: int):
    return db.query(Post).filter(Post.group_id == group_id).all()


def get_user_posts(db: Session, user_id: int):
    return db.query(Post).filter(Post.user_id == user_id).all()


# ---------------------------------------------------------
# Comments
# ---------------------------------------------------------

def create_comment(db: Session, user_id: int, post_id: int, content: str):
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
    return db.query(Comment).filter(Comment.post_id == post_id).all()


# ---------------------------------------------------------
# Reactions
# ---------------------------------------------------------

def create_reaction(db: Session, user_id: int, reaction_type: str,
                    post_id: int = None, comment_id: int = None):
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
