from sqlalchemy import select, func
from sqlalchemy.orm import Session

from models import Like, Post, User

# Поставить лайк. Если уже стоит - вернуть существующий
def like_post(session: Session, user_id: int, post_id: int) -> Like:
    user = session.get(User, user_id)
    if user is None:
        raise ValueError("Пользователь не найден")

    post = session.get(Post, post_id)
    if post is None or post.status != "published":
        raise ValueError("Лайкать можно только опубликованный пост")

    existing = session.get(Like, (user_id, post_id))
    if existing is not None:
        return existing

    like = Like(user_id=user_id, post_id=post_id)
    session.add(like)
    session.commit()
    return like

# Снять лайк. Если лайка нет — ничего не делаем
def unlike_post(session: Session, user_id: int, post_id: int) -> None:
    like = session.get(Like, (user_id, post_id))
    if like is not None:
        session.delete(like)
        session.commit()

# Количество лайков у поста
def get_likes_count(session: Session, post_id: int) -> int:
    return session.scalar(
        select(func.count()).select_from(Like).where(Like.post_id == post_id)
    ) or 0

# Лайкнул ли пользователь этот пост
def has_liked(session: Session, user_id: int, post_id: int) -> bool:
    return session.get(Like, (user_id, post_id)) is not None

# Все опубликованные посты, которые лайкнул пользователь
def get_user_liked_posts(session: Session, user_id: int) -> list[Post]:
    query = (
        select(Post)
        .join(Like, Like.post_id == Post.id)
        .where(Like.user_id == user_id, Post.status == "published")
        .order_by(Post.published_at.desc(), Post.id.desc())
    )
    return list(session.scalars(query))