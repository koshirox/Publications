from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Category, Post
from crud_users import require_moderator


# создать категорию (модератор или админ)
# имя должно быть уникальным
def create_category(session: Session, user_id: int, name: str) -> Category:
    require_moderator(session, user_id)
    if session.scalar(select(Category).where(Category.name == name)) is not None:
        raise ValueError("Категория уже существует")
    category = Category(name=name)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


# получить категорию по id
def get_category(session: Session, category_id: int) -> Category | None:
    return session.get(Category, category_id)


# список всех категорий, отсортированных по имени
def list_categories(session: Session) -> list[Category]:
    return list(session.scalars(select(Category).order_by(Category.name)))


# переименовать категорию (модератор или админ)
def rename_category(session: Session, user_id: int, category_id: int, name: str) -> Category:
    require_moderator(session, user_id)   # ← было require_admin
    category = session.get(Category, category_id)
    if category is None:
        raise ValueError("Категория не найдена")
    category.name = name
    session.commit()
    return category


# удалить категорию (модератор или админ)
# нельзя удалить, если в ней есть посты
def delete_category(session: Session, user_id: int, category_id: int) -> None:
    require_moderator(session, user_id)   # ← было require_admin
    category = session.get(Category, category_id)
    if category is None:
        raise ValueError("Категория не найдена")
    if session.scalar(select(Post.id).where(Post.category_id == category_id)) is not None:
        raise ValueError("Нельзя удалить категорию с постами")
    session.delete(category)
    session.commit()