from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

import crud_likes as likes
import crud_posts as posts
from auth import CurrentUser, Db, current_user
from models import Post
from routers.categories import get_category
from schemas import Id, LikeCount, PostIn, PostOut

router = APIRouter(prefix="/posts", tags=["posts"], dependencies=[Depends(current_user)])


CategoryFilter = Annotated[int | None, Query(gt=0, le=2**63 - 1)]


@router.get("", response_model=list[PostOut])
def list_posts(db: Db, category_id: CategoryFilter = None):
    if category_id is not None:
        get_category(category_id, db)
        return posts.category_feed(db, category_id)
    return posts.general_feed(db)


@router.get("/{post_id}", response_model=PostOut)
def get_post(post_id: Id, db: Db, user: CurrentUser):
    post = posts.get_post(db, post_id)
    if post is None:
        raise HTTPException(404, "Пост не найден")
    if post.status == "published":
        return post
    if user.id == post.author_id or user.role == "moderator":
        return post
    raise HTTPException(404, "Пост не найден")


@router.post("", response_model=PostOut, status_code=201)
def create_post(data: PostIn, db: Db, user: CurrentUser):
    get_category(data.category_id, db)
    return posts.create_draft(db, user.id, **data.model_dump())


@router.put("/{post_id}", response_model=PostOut)
def change_post(post_id: Id, data: PostIn, db: Db, user: CurrentUser):
    get_post(post_id, db, user)
    get_category(data.category_id, db)
    return posts.change_post(db, post_id, user.id, **data.model_dump())


@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: Id, db: Db, user: CurrentUser):
    post = get_post(post_id, db, user)
    if user.role == "moderator" and post.author_id != user.id:
        posts.delete_post_as_moderator(db, post_id, user.id)
    else:
        posts.delete_draft(db, post_id, user.id)


@router.post("/{post_id}/publish", response_model=PostOut)
def publish_post(post_id: Id, db: Db, user: CurrentUser):
    get_post(post_id, db, user)
    return posts.publish_post(db, post_id, user.id)


@router.post("/{post_id}/hide", response_model=PostOut)
def hide_post(post_id: Id, db: Db, user: CurrentUser):
    get_post(post_id, db, user)
    return posts.hide_post(db, post_id, user.id)


def published_post(post_id: int, db: Db) -> Post:
    post = posts.get_post(db, post_id)
    if post is None or post.status != "published":
        raise HTTPException(404, "Пост не найден")
    return post


@router.get("/{post_id}/likes", response_model=LikeCount)
def count_likes(post_id: Id, db: Db):
    published_post(post_id, db)
    return LikeCount(count=likes.get_likes_count(db, post_id))


@router.put("/{post_id}/likes/me", status_code=204)
def add_like(post_id: Id, db: Db, user: CurrentUser):
    published_post(post_id, db)
    likes.like_post(db, user.id, post_id)


@router.delete("/{post_id}/likes/me", status_code=204)
def remove_like(post_id: Id, db: Db, user: CurrentUser):
    likes.unlike_post(db, user.id, post_id)
