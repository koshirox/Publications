from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Post, Subscription, User

# проверяет, что юзер с данным id существует и у него роль admin
def require_admin(session: Session, admin_id: int) -> None:
    admin = session.get(User, admin_id)
    if admin is None or admin.role != "admin":
        raise PermissionError("Создавать и удалять пользователей может только администратор")

# проверяет, что юзер существует и его роль - admin или moderator
def require_moderator(session: Session, user_id: int) -> None:
    user = session.get(User, user_id)
    if user is None or user.role not in ("moderator", "admin"):
        raise PermissionError("Требуются права модератора или админа")

# ищет юзера по email, возвращает объект или None
def get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email))

# создаёт нового юзера (только от имени админа)
# роль может быть user или moderator, admin создать нельзя
def create_user(session: Session, admin_id: int, email: str, role: str = "user") -> User:
    require_admin(session, admin_id)
    if role not in ("user", "moderator"):
        raise ValueError("Администратор может назначить роль user или moderator")
    if get_user_by_email(session, email) is not None:
        raise ValueError("Пользователь с таким email уже есть")
    user = User(email=email, password_hash="not_used_in_lab1", role=role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# получить юзера по id
def get_user(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)

# меняет email у юзера (UPDATE)
def change_email(session: Session, user_id: int, email: str) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise ValueError("Пользователь не найден")
    user.email = email
    session.commit()
    return user

# повышает юзера до модератора (только админ)
# нельзя менять роль другого админа
def grant_moderator(session: Session, admin_id: int, user_id: int) -> User:
    require_admin(session, admin_id)
    user = session.get(User, user_id)
    if user is None:
        raise ValueError("Пользователь не найден")
    if user.role == "admin":
        raise PermissionError("Нельзя изменить роль администратора")
    user.role = "moderator"
    session.commit()
    return user

# удаляет юзера (только админ)
# нельзя удалить админа
def delete_user(session: Session, admin_id: int, user_id: int) -> None:
    require_admin(session, admin_id)
    user = session.get(User, user_id)
    if user is None:
        raise ValueError("Пользователь не найден")
    if user.role == "admin":
        raise PermissionError("Нельзя удалить администратора")
    session.delete(user)
    session.commit()


# ------ Подписки и персональная лента ------

# подписать follower на author
# нельзя подписаться на себя, нельзя дважды - повторный вызов не создаёт дубликат
def subscribe(session: Session, follower_id: int, author_id: int) -> Subscription:
    if follower_id == author_id:
        raise ValueError("Нельзя подписаться на себя")
    if session.get(User, follower_id) is None or session.get(User, author_id) is None:
        raise ValueError("Пользователь не найден")
    subscription = session.get(Subscription, (follower_id, author_id))
    if subscription is not None:
        return subscription
    subscription = Subscription(follower_id=follower_id, author_id=author_id)
    session.add(subscription)
    session.commit()
    return subscription

# отписаться - если подписки нет, просто ничего не делаем
def unsubscribe(session: Session, follower_id: int, author_id: int) -> None:
    subscription = session.get(Subscription, (follower_id, author_id))
    if subscription is not None:
        session.delete(subscription)
        session.commit()

# лента постов тех, на кого подписан пользователь
# join posts subscriptions, фильтр по follower_id и status=published
def personal_feed(session: Session, follower_id: int) -> list[Post]:
    query = (
        select(Post)
        .join(Subscription, Subscription.author_id == Post.author_id)
        .where(Subscription.follower_id == follower_id, Post.status == "published")
        .order_by(Post.published_at.desc(), Post.id.desc())
    )
    return list(session.scalars(query))
