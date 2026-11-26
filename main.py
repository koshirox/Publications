from fastapi import FastAPI

from auth import jwt_secret
from errors import exception_handlers
from routers import categories, comments, posts, users

jwt_secret()

app = FastAPI(title="Publications", exception_handlers=exception_handlers)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(posts.router)
app.include_router(comments.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
