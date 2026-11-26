"""Создать недостающие таблицы и индекс для роли администратора."""

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.schema import CreateIndex

from database import SessionLocal, engine
from models import Base, Category, single_admin_index

Base.metadata.create_all(engine)
with SessionLocal.begin() as session:
    session.execute(CreateIndex(single_admin_index, if_not_exists=True))
    session.execute(insert(Category).values(name="Новости").on_conflict_do_nothing())
print("Таблицы готовы. Добавлена стартовая категория «Новости».")
