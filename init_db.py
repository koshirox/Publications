"""Создать недостающие таблицы. Запустить один раз перед заполнением."""

from database import engine
from models import Base


Base.metadata.create_all(engine)
print("Готово: users, categories, posts, comments, subscriptions")
