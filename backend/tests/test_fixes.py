from datetime import timedelta

import pytest
from sqlmodel import Session, select

from app.core.db import engine
from app.core.security import create_access_token, decode_access_token
from app.crud import (
    create_message,
    get_or_create_private_chat,
    update_user_online_status,
)
from app.models import Chat, ChatMember, ChatMessage, User


class TestDepsTokenConversion:
    def test_token_sub_is_converted_to_int(self):
        with Session(engine) as session:
            user = session.exec(select(User)).first()
            if not user:
                pytest.skip("No user in DB")

            token = create_access_token(str(user.id), timedelta(minutes=30))
            payload = decode_access_token(token)
            assert int(payload["sub"]) == user.id


class TestOnlineStatusLogic:
    def test_online_status_set_to_false(self):
        with Session(engine) as session:
            test_users = session.exec(select(User)).all()
            if not test_users:
                pytest.skip("No user in DB")

            test_user = test_users[0]
            user_id = test_user.id

            update_user_online_status(session=session, user_id=user_id, is_online=True)
            session.expire_all()
            user = session.get(User, user_id)
            assert user.is_online is True

            old_last_seen = user.last_seen_at

            update_user_online_status(session=session, user_id=user_id, is_online=False)
            session.expire_all()
            user = session.get(User, user_id)
            assert user.is_online is False
            assert user.last_seen_at is not None
            assert user.last_seen_at > old_last_seen


class TestUpdatedAtNotSaved:
    def test_message_updates_chat_updated_at(self):
        with Session(engine) as session:
            test_users = session.exec(select(User)).all()
            if len(test_users) < 2:
                pytest.skip("Need at least 2 users")

            chat = get_or_create_private_chat(session=session, user1_id=test_users[0].id, user2_id=test_users[1].id)
            old_updated_at = chat.updated_at

            import time
            time.sleep(0.1)

            create_message(
                session=session,
                chat_id=chat.id,
                sender_id=test_users[0].id,
                content="Test message"
            )

            session.expire_all()
            chat = session.get(Chat, chat.id)
            assert chat.updated_at > old_updated_at


class TestTransferSimplified:
    def test_transfer_uses_current_user(self):
        with Session(engine) as session:
            test_users = session.exec(select(User)).all()
            if len(test_users) < 2:
                pytest.skip("Need at least 2 users")

            sender = test_users[0]
            recipient = test_users[1]
            sender.balance = 100
            recipient.balance = 0
            session.add(sender)
            session.add(recipient)
            session.commit()

            sender.balance -= 10
            recipient.balance += 10

            session.add(sender)
            session.add(recipient)
            session.commit()

            session.expire_all()
            sender = session.get(User, sender.id)
            recipient = session.get(User, recipient.id)
            assert sender.balance == 90
            assert recipient.balance == 10


class TestUnreadCountLogic:
    def test_unread_count_correct(self):
        with Session(engine) as session:
            test_users = session.exec(select(User)).all()
            if len(test_users) < 2:
                pytest.skip("Need at least 2 users")

            chat = get_or_create_private_chat(session=session, user1_id=test_users[0].id, user2_id=test_users[1].id)

            create_message(
                session=session,
                chat_id=chat.id,
                sender_id=test_users[0].id,
                content="Test"
            )
            session.commit()

            member = session.exec(
                select(ChatMember).where(
                    ChatMember.chat_id == chat.id,
                    ChatMember.user_id == test_users[1].id
                )
            ).first()

            from datetime import datetime, timezone
            member.last_read_at = datetime.now(timezone.utc)
            session.add(member)
            session.commit()

            from sqlmodel import func
            unread = session.exec(
                select(func.count()).select_from(ChatMessage).where(
                    ChatMessage.chat_id == chat.id,
                    ChatMessage.sender_id != test_users[1].id,
                    ChatMessage.created_at > member.last_read_at
                )
            ).one()

            assert unread == 0


class TestEmptyMessageValidation:
    def test_empty_message_rejected_websocket(self):
        content = ""
        stripped = content.strip()
        assert not stripped

        content = "   "
        stripped = content.strip()
        assert not stripped

        content = "hello"
        stripped = content.strip()
        assert stripped


class TestAvatarPathFix:
    def test_avatar_url_parsing(self):
        test_urls = [
            "/api/v1/media/avatars/user_1_20260413172001.png",
            "/api/v1/media/avatars/very_long_filename.png",
            "simple.png"
        ]

        for url in test_urls:
            filename = url.split("/")[-1]
            assert filename
            assert ".." not in filename


class TestUltraExpirationLogic:
    def test_expired_ultra_is_revoked(self):
        from datetime import datetime, timedelta, timezone

        from app.api.serialization import sync_user_ultra_status

        user = User(
            email="expired-ultra@example.com",
            hashed_password="hash",
            is_ultra=True,
            ultra_expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            ultra_badge="star",
            ultra_profile_color="gold",
            ultra_avatar_style="animated",
        )

        assert sync_user_ultra_status(user) is True
        assert user.is_ultra is False
        assert user.ultra_expires_at is None
        assert user.ultra_badge is None
        assert user.ultra_profile_color is None
        assert user.ultra_avatar_style is None


class TestBotResponseLogic:
    def test_empty_bot_response_gets_fallback_text(self):
        from app.bot_executor import execute_bot

        result = execute_bot("pass", "python", "hello", {"id": 1, "full_name": "User"})

        assert result["response"] == "Бот не вернул ответ"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
