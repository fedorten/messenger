from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models import Chat, ChatMember, ChatMessage, User, UserPublic


def _as_aware_utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def sync_user_ultra_status(user: User | None) -> bool:
    """Apply Ultra expiration rules to a user object before it is exposed."""
    if not user:
        return False

    expires_at = _as_aware_utc(getattr(user, "ultra_expires_at", None))
    is_expired = bool(
        getattr(user, "is_ultra", False)
        and expires_at
        and expires_at <= datetime.now(timezone.utc)
    )
    if not is_expired:
        return False

    user.is_ultra = False
    user.ultra_expires_at = None
    user.ultra_badge = None
    user.ultra_profile_color = None
    user.ultra_avatar_style = None
    return True


def build_user_public(user: User, *, is_online: bool | None = None) -> UserPublic:
    """Build a full UserPublic payload from a SQLModel user."""
    sync_user_ultra_status(user)
    public_user = UserPublic.model_validate(user, from_attributes=True)
    if is_online is not None:
        public_user.is_online = is_online
    return public_user


def get_chat_member(
    session: Session, chat_id: int, user_id: int
) -> ChatMember | None:
    statement = select(ChatMember).where(
        ChatMember.chat_id == chat_id, ChatMember.user_id == user_id
    )
    return session.exec(statement).first()


def get_chat_members(session: Session, chat_id: int) -> list[ChatMember]:
    statement = select(ChatMember).where(ChatMember.chat_id == chat_id)
    return list(session.exec(statement).all())


def compute_message_is_read(
    session: Session,
    chat: Chat,
    message: ChatMessage,
    current_user_id: int,
) -> bool:
    """Compute read state for the message from the current user's perspective."""
    members = get_chat_members(session, chat.id)

    current_member = next(
        (member for member in members if member.user_id == current_user_id), None
    )
    if not current_member:
        return False

    if message.sender_id == current_user_id:
        other_members = [member for member in members if member.user_id != current_user_id]
        if not other_members:
            return False
        return any(
            member.last_read_at is not None and member.last_read_at >= message.created_at
            for member in other_members
        )

    if current_member.last_read_at is None:
        return False

    return message.created_at <= current_member.last_read_at
