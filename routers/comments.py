from fastapi import APIRouter, Depends, HTTPException

import crud_comments as comments
from auth import CurrentUser, Db, current_user
from models import Comment
from routers.posts import published_post
from schemas import CommentIn, CommentOut, Id

router = APIRouter(tags=["comments"], dependencies=[Depends(current_user)])


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut])
def list_comments(post_id: Id, db: Db):
    published_post(post_id, db)
    return comments.get_comments(db, post_id)


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=201)
def create_comment(post_id: Id, data: CommentIn, db: Db, user: CurrentUser):
    published_post(post_id, db)
    return comments.create_comment(db, post_id, user.id, data.body)


@router.get("/comments/{comment_id}", response_model=CommentOut)
def get_comment(comment_id: Id, db: Db):
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(404, "Комментарий не найден")
    published_post(comment.post_id, db)
    return comment


@router.put("/comments/{comment_id}", response_model=CommentOut)
def change_comment(comment_id: Id, data: CommentIn, db: Db, user: CurrentUser):
    get_comment(comment_id, db)
    return comments.change_comment(db, comment_id, user.id, data.body)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: Id, db: Db, user: CurrentUser):
    get_comment(comment_id, db)
    comments.delete_comment(db, comment_id, user.id)
