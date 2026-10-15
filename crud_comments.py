from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Comment, Post, User

# создать комментарий к посту
# комментировать можно только опубликованный пост
def create_comment(session: Session, post_id: int, user_id: int, body: str) -> Comment:
    post = session.get(Post, post_id)
    if post is None or post.status != "published":
        raise ValueError("Комментировать можно только опубликованный пост")
    if session.get(User, user_id) is None:
        raise ValueError("Пользователь не найден")
    comment = Comment(post_id=post_id, user_id=user_id, body=body)
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment

# получить все комментарии поста, старые сверху
def get_comments(session: Session, post_id: int) -> list[Comment]:
    query = (
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at, Comment.id)
    )
    return list(session.scalars(query))

# редактировать комментарий
# менять может только автор
def change_comment(session: Session, comment_id: int, user_id: int, body: str) -> Comment:
    comment = session.get(Comment, comment_id)
    if comment is None:
        raise ValueError("Комментарий не найден")
    if comment.user_id != user_id:
        raise PermissionError("Нельзя менять чужой комментарий")
    comment.body = body
    session.commit()
    return comment

# удалить комментарий
# удалять может автор или модератор
def delete_comment(session: Session, comment_id: int, user_id: int) -> None:
    comment = session.get(Comment, comment_id)
    if comment is None:
        raise ValueError("Комментарий не найден")
    user = session.get(User, user_id)
    if comment.user_id != user_id and (user is None or user.role != "moderator"):
        raise PermissionError("Удалять чужой комментарий может только модератор")
    session.delete(comment)
    session.commit()
