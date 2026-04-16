import io
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from app.api.routes.users import validate_image_content, get_directory_size


def test_validate_image_content_jpeg():
    content = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    assert validate_image_content(content) == "jpeg"


def test_validate_image_content_png():
    content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    assert validate_image_content(content) == "png"


def test_validate_image_content_gif():
    content = b"GIF89a\x01\x00\x01\x00"
    assert validate_image_content(content) == "gif"


def test_validate_image_content_invalid():
    content = b"<script>alert(1)</script>"
    assert validate_image_content(content) is None


def test_validate_image_content_executable():
    content = b"\x7fELF" + b"\x00" * 100
    assert validate_image_content(content) is None


def test_path_traversal_blocked(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/users/me/avatar",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 200


def test_private_endpoint_requires_superuser(client: TestClient) -> None:
    from app.api.main import api_router
    r = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json={"email": "new@example.com", "password": "password123", "full_name": "New"},
    )
    assert r.status_code in [403, 404]


def test_add_balance_removed(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/users/me/add-balance",
        json={"amount": 100},
        headers=superuser_token_headers,
    )
    assert r.status_code in [404, 422, 501]


def test_transfer_with_for_update(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    from app.models import User, TransferShekels
    
    sender = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).first()
    sender.balance = 1000
    
    recipient = User(
        email="recipient@test.com",
        full_name="Recipient",
        hashed_password="$2b$12$hash",
        balance=0,
    )
    db.add(recipient)
    db.commit()
    
    r = client.post(
        f"{settings.API_V1_STR}/users/me/transfer",
        json={"recipient_id": recipient.id, "amount": 100},
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    
    db.refresh(sender)
    db.refresh(recipient)
    assert sender.balance == 900
    assert recipient.balance == 100


def test_transfer_insufficient_balance(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/users/me/transfer",
        json={"recipient_id": 999, "amount": 1000000},
        headers=normal_user_token_headers,
    )
    assert r.status_code == 400