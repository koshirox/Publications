from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Category, Comment, Post, User

# создаёт черновик поста (только user или moderator)
# проверяет, что автор существует и категория есть
def create_draft(
    session: Session, author_id: int, category_id: int, title: str, body: str
) -> Post:
    author = session.get(User, author_id)
    if author is None or author.role not in ("user", "moderator"):
        raise PermissionError("Посты создают пользователи и модераторы")
    if session.get(Category, category_id) is None:
        raise ValueError("Категория не найдена")
    post = Post(
        author_id=author_id, category_id=category_id,
        title=title, body=body, status="draft",
    )
    session.add(post)
    session.commit()
    session.refresh(post)
    return post

# получить пост по id
def get_post(session: Session, post_id: int) -> Post | None:
    return session.get(Post, post_id)

# редактировать свой пост (title, body, опционально category_id)
# менять может только автор
def change_post(
    session: Session, post_id: int, author_id: int,
    title: str, body: str, category_id: int | None = None,
) -> Post:
    post = session.get(Post, post_id)
    if post is None:
        raise ValueError("Пост не найден")
    if post.author_id != author_id:
        raise PermissionError("Нельзя менять чужой пост")
    if category_id is not None:
        if session.get(Category, category_id) is None:
            raise ValueError("Категория не найдена")
        post.category_id = category_id
    post.title = title
    post.body = body
    session.commit()
    return post

# опубликовать свой черновик
# меняет status с draft на published и ставит published_at
def publish_post(session: Session, post_id: int, author_id: int) -> Post:
    post = session.get(Post, post_id)
    if post is None or post.author_id != author_id:
        raise PermissionError("Публиковать можно только свой пост")
    if post.status != "draft":
        raise ValueError("Опубликовать можно только черновик")
    post.status = "published"
    post.published_at = datetime.now(timezone.utc)
    session.commit()
    return post

# удалить свой черновик (только пока он draft)
def delete_draft(session: Session, post_id: int, author_id: int) -> None:
    post = session.get(Post, post_id)
    if post is None or post.author_id != author_id or post.status != "draft":
        raise PermissionError("Удалить можно только свой черновик")
    session.delete(post)
    session.commit()

# модератор скрывает опубликованный пост (status = hidden)
# может скрыть и свой, и чужой
def hide_post(session: Session, post_id: int, moderator_id: int) -> Post:
    moderator = session.get(User, moderator_id)
    post = session.get(Post, post_id)
    if moderator is None or moderator.role != "moderator":
        raise PermissionError("Скрывать посты может только модератор")
    if post is None or post.status != "published":
        raise ValueError("Скрыть можно только опубликованный пост")
    post.status = "hidden"
    session.commit()
    return post

# модератор удаляет чужой пост вместе со всеми комментариями
# комментарии удаляем вручную, потому что у них FK на пост
def delete_post_as_moderator(session: Session, post_id: int, moderator_id: int) -> None:
    moderator = session.get(User, moderator_id)
    if moderator is None or moderator.role != "moderator":
        raise PermissionError("Удалять чужие посты может только модератор")
    post = session.get(Post, post_id)
    if post is None:
        raise ValueError("Пост не найден")

    # У комментариев FK на пост, поэтому сначала удаляем их.
    for comment in session.scalars(select(Comment).where(Comment.post_id == post_id)).all():
        session.delete(comment)
    session.flush()
    session.delete(post)
    session.commit()

# общая лента: все опубликованные посты, свежие сверху
def general_feed(session: Session) -> list[Post]:
    query = (
        select(Post)
        .where(Post.status == "published")
        .order_by(Post.published_at.desc(), Post.id.desc())
    )
    return list(session.scalars(query))

# лента категории: опубликованные посты конкретной категории, свежие сверху
def category_feed(session: Session, category_id: int) -> list[Post]:
    query = (
        select(Post)
        .where(Post.category_id == category_id, Post.status == "published")
        .order_by(Post.published_at.desc(), Post.id.desc())
    )
    return list(session.scalars(query))
