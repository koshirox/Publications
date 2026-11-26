from fastapi import APIRouter, Depends, HTTPException

import crud_likes as likes
import crud_users as users
from auth import CurrentUser, Db, create_token, current_user, password_hash, unauthorized
from models import User
from schemas import (
    Credentials,
    EmailUpdate,
    Id,
    PostOut,
    Profile,
    SubscriptionList,
    Token,
    UserOut,
)

router = APIRouter(tags=["users"])


@router.post("/register", response_model=Profile, status_code=201)
def register(data: Credentials, db: Db):
    if users.get_user_by_email(db, data.email) is not None:
        raise HTTPException(409, "Этот email уже зарегистрирован")
    user = User(email=data.email, password_hash=password_hash.hash(data.password.get_secret_value()))
    db.add(user)
    db.commit()
    return user


@router.post("/login", response_model=Token)
def login(data: Credentials, db: Db):
    user = users.get_user_by_email(db, data.email)
    if user is None or user.password_hash == "not_used_in_lab1":
        raise unauthorized("Неверный email или пароль")
    if not password_hash.verify(data.password.get_secret_value(), user.password_hash):
        raise unauthorized("Неверный email или пароль")
    return Token(access_token=create_token(user))


@router.get("/users/me", response_model=Profile)
def profile(user: CurrentUser):
    return user


@router.patch("/users/me", response_model=Profile)
def change_email(data: EmailUpdate, db: Db, user: CurrentUser):
    return users.change_email(db, user.id, data.email)


@router.get("/users/{user_id}", response_model=UserOut, dependencies=[Depends(current_user)])
def get_user(user_id: Id, db: Db):
    user = users.get_user(db, user_id)
    if user is None:
        raise HTTPException(404, "Пользователь не найден")
    return user


@router.put("/users/{user_id}/moderator", response_model=UserOut)
def grant_moderator(user_id: Id, db: Db, user: CurrentUser):
    users.require_admin(db, user.id)
    get_user(user_id, db)
    return users.grant_moderator(db, user.id, user_id)


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: Id, db: Db, user: CurrentUser):
    users.require_admin(db, user.id)
    get_user(user_id, db)
    users.delete_user(db, user.id, user_id)


@router.put("/subscriptions/{author_id}", status_code=204)
def subscribe(author_id: Id, db: Db, user: CurrentUser):
    get_user(author_id, db)
    users.subscribe(db, user.id, author_id)


@router.delete("/subscriptions/{author_id}", status_code=204)
def unsubscribe(author_id: Id, db: Db, user: CurrentUser):
    users.unsubscribe(db, user.id, author_id)


@router.get("/users/me/subscriptions", response_model=SubscriptionList)
def my_subscriptions(db: Db, user: CurrentUser):
    authors = users.list_subscriptions(db, user.id)
    return {"count": len(authors), "users": authors}


@router.get("/users/me/followers", response_model=SubscriptionList)
def my_followers(db: Db, user: CurrentUser):
    followers = users.list_followers(db, user.id)
    return {"count": len(followers), "users": followers}


@router.get("/feed", response_model=list[PostOut])
def personal_feed(db: Db, user: CurrentUser):
    return users.personal_feed(db, user.id)


@router.get("/users/me/liked-posts", response_model=list[PostOut])
def liked_posts(db: Db, user: CurrentUser):
    return likes.get_user_liked_posts(db, user.id)
