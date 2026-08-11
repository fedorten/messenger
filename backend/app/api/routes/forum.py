from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.api.serialization import build_user_public
from app.models import (
    ForumComment,
    ForumCommentCreate,
    ForumCommentPublic,
    ForumCommentsPublic,
    ForumPost,
    ForumPostCreate,
    ForumPostPublic,
    ForumPostsPublic,
)

router = APIRouter(prefix="/forum", tags=["forum"])


@router.get("/posts", response_model=ForumPostsPublic)
def get_posts(
    session: SessionDep,
    _current_user: CurrentUser,
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
):
    """Получить все посты форума"""
    statement = (
        select(ForumPost)
        .order_by(ForumPost.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    posts = session.exec(statement).all()

    # Проверяем, какие посты лайкнул пользователь
    # (упрощенно - без отдельной таблицы лайков, просто считаем по количеству)

    result = []
    for post in posts:
        post_data = ForumPostPublic(
            id=post.id,
            author_id=post.author_id,
            author=build_user_public(post.author, is_online=False),
            title=post.title,
            content=post.content,
            media_type=post.media_type,
            media_url=post.media_url,
            media_filename=post.media_filename,
            created_at=post.created_at,
            updated_at=post.updated_at,
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            is_liked=False,
        )
        result.append(post_data)

    return ForumPostsPublic(data=result, count=len(result))


@router.get("/posts/{post_id}", response_model=ForumPostPublic)
def get_post(post_id: int, session: SessionDep, _current_user: CurrentUser):
    """Получить один пост"""
    post = session.get(ForumPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    return ForumPostPublic(
        id=post.id,
        author_id=post.author_id,
        author=build_user_public(post.author, is_online=False),
        title=post.title,
        content=post.content,
        media_type=post.media_type,
        media_url=post.media_url,
        media_filename=post.media_filename,
        created_at=post.created_at,
        updated_at=post.updated_at,
        likes_count=post.likes_count,
        comments_count=post.comments_count,
        is_liked=False,
    )


@router.post("/posts", response_model=ForumPostPublic)
def create_post(
    post_data: ForumPostCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    """Создать новый пост"""
    post = ForumPost(
        author_id=current_user.id,
        title=post_data.title,
        content=post_data.content,
        media_type=post_data.media_type,
        media_url=post_data.media_url,
        media_filename=post_data.media_filename,
    )
    session.add(post)
    session.commit()
    session.refresh(post)

    return ForumPostPublic(
        id=post.id,
        author_id=post.author_id,
        author=build_user_public(post.author, is_online=False),
        title=post.title,
        content=post.content,
        media_type=post.media_type,
        media_url=post.media_url,
        media_filename=post.media_filename,
        created_at=post.created_at,
        updated_at=post.updated_at,
        likes_count=0,
        comments_count=0,
        is_liked=False,
    )


@router.delete("/posts/{post_id}")
def delete_post(post_id: int, session: SessionDep, current_user: CurrentUser):
    """Удалить пост (только автор)"""
    post = session.get(ForumPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    if post.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Нет прав")

    session.delete(post)
    session.commit()
    return {"ok": True}


@router.post("/posts/{post_id}/like")
def like_post(post_id: int, session: SessionDep, _current_user: CurrentUser):
    """Лайкнуть пост"""
    post = session.get(ForumPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    post.likes_count += 1
    session.commit()
    return {"likes_count": post.likes_count}


@router.get("/posts/{post_id}/comments", response_model=ForumCommentsPublic)
def get_comments(
    post_id: int,
    session: SessionDep,
    _current_user: CurrentUser,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Получить комментарии поста"""
    post = session.get(ForumPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    statement = (
        select(ForumComment)
        .where(ForumComment.post_id == post_id)
        .order_by(ForumComment.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    comments = session.exec(statement).all()

    result = []
    for comment in comments:
        result.append(
            ForumCommentPublic(
                id=comment.id,
                post_id=comment.post_id,
                author_id=comment.author_id,
                author=build_user_public(comment.author, is_online=False),
                content=comment.content,
                created_at=comment.created_at,
            )
        )

    return ForumCommentsPublic(data=result, count=len(result))


@router.post("/posts/{post_id}/comments", response_model=ForumCommentPublic)
def create_comment(
    post_id: int,
    comment_data: ForumCommentCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    """Добавить комментарий к посту"""
    post = session.get(ForumPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    comment = ForumComment(
        post_id=post_id,
        author_id=current_user.id,
        content=comment_data.content,
    )
    session.add(comment)

    # Обновляем счётчик комментариев
    post.comments_count += 1
    session.commit()
    session.refresh(comment)

    return ForumCommentPublic(
        id=comment.id,
        post_id=comment.post_id,
        author_id=comment.author_id,
        author=build_user_public(comment.author, is_online=False),
        content=comment.content,
        created_at=comment.created_at,
    )


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, session: SessionDep, current_user: CurrentUser):
    """Удалить комментарий"""
    comment = session.get(ForumComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Комментарий не найден")

    if comment.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Нет прав")

    # Уменьшаем счётчик комментариев
    post = session.get(ForumPost, comment.post_id)
    if post:
        post.comments_count = max(0, post.comments_count - 1)

    session.delete(comment)
    session.commit()
    return {"ok": True}
