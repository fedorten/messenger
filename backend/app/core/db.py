from sqlalchemy import event, inspect, text
from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate

ADDITIONAL_SUPERUSER_EMAILS = {"feedoor.feedoot@gmail.com"}

# SQLite требует connect_args для работы в многопоточном режиме
connect_args = {}
if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    connect_args=connect_args,
    echo=False,
)

# Настройка для работы с UUID в SQLite
if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        # Включаем поддержку внешних ключей
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # Создаем таблицы для тестов (в продакшене используются миграции Alembic)
    SQLModel.metadata.create_all(engine)
    ensure_sqlite_schema_compatibility()

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)

    for email in ADDITIONAL_SUPERUSER_EMAILS:
        extra_superuser = session.exec(select(User).where(User.email == email)).first()
        if extra_superuser and not extra_superuser.is_superuser:
            extra_superuser.is_superuser = True
            extra_superuser.is_verified = True
            session.add(extra_superuser)
            session.commit()


def ensure_sqlite_schema_compatibility() -> None:
    """Добавить недостающие колонки в SQLite-базе для старых схем."""
    if not settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        return

    expected_columns = {
        "user": {
            "is_online": "BOOLEAN DEFAULT 0",
            "last_seen_at": "DATETIME",
            "timezone": "VARCHAR(50) DEFAULT 'UTC'",
        },
        "chat": {
            "avatar_url": "VARCHAR(500)",
        },
    }

    with engine.begin() as connection:
        inspector = inspect(connection)
        existing_tables = set(inspector.get_table_names())
        for table_name, columns in expected_columns.items():
            if table_name not in existing_tables:
                continue

            existing_columns = {
                column_info["name"] for column_info in inspector.get_columns(table_name)
            }
            for column_name, column_ddl in columns.items():
                if column_name in existing_columns:
                    continue
                connection.execute(
                    text(
                        f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_ddl}'
                    )
                )
