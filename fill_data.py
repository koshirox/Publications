"""Начальные данные. Повторный запуск не создаёт те же записи заново."""

from sqlalchemy import select

from database import SessionLocal
from models import Category, Post, User
from crud_categories import create_category
from crud_comments import create_comment, get_comments
from crud_posts import create_draft, publish_post
from crud_users import subscribe
from crud_users import create_user, get_user_by_email
from crud_likes import like_post, get_likes_count

with SessionLocal() as session:
    # Первый администратор появляется при настройке БД; далее пользователей создаёт он.
    admin = session.scalar(select(User).where(User.role == "admin"))
    if admin is None:
        admin = User(email="admin@example.com", password_hash="not_used_in_lab1", role="admin")
        session.add(admin)
        session.commit()
        session.refresh(admin)

    news = session.scalar(select(Category).where(Category.name == "Новости"))
    if news is None:
        news = create_category(session, admin.id, "Новости")

    author = get_user_by_email(session, "author@example.com")
    if author is None:
        author = create_user(session, admin.id, "author@example.com")
    reader = get_user_by_email(session, "reader@example.com")
    if reader is None:
        reader = create_user(session, admin.id, "reader@example.com")
    moderator = get_user_by_email(session, "moderator@example.com")
    if moderator is None:
        moderator = create_user(session, admin.id, "moderator@example.com", "moderator")

    post = session.scalar(select(Post).where(Post.author_id == author.id, Post.title == "Первый пост"))
    if post is None:
        post = create_draft(session, author.id, news.id, "Первый пост", "# Привет\n\nТекст в **Markdown**.")
    if post.status == "draft":
        publish_post(session, post.id, author.id)

    subscribe(session, reader.id, author.id)
    if not any(comment.user_id == reader.id for comment in get_comments(session, post.id)):
        create_comment(session, post.id, reader.id, "Интересная публикация!")
    like_post(session, reader.id, post.id)

    print(f"Лайков у поста: {get_likes_count(session, post.id)}")
    print(f"Администратор: {admin.email}, модератор: {moderator.email}")
    print(f"Категория: {news.name}; опубликован пост id={post.id}")
    print(f"Подписчик: {reader.email}; комментариев: {len(get_comments(session, post.id))}")
