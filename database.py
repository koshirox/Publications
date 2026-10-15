from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

url = URL.create(
    "postgresql+psycopg",
    username="postgres",
    password=input("Пароль PostgreSQL: "),
    host="localhost",
    port=5432,
    database="Publications",
)

engine = create_engine(url)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
