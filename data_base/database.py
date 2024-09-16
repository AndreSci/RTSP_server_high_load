from sqlalchemy import create_engine, MetaData
from databases import Database
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine

DATABASE_URL = "mysql+aiomysql://username:password@localhost:3306/dbname?charset=cp1251"

DATABASE = Database
METADATA = MetaData()

ENGINE = AsyncEngine


# Асинхронная сессия
async_session = sessionmaker


class GlobControlDatabase:
    @staticmethod
    def set_url(username: str, password: str, url: str, port: Any, dbname: str, charset: str = 'cp1251') -> bool:
        global DATABASE_URL, DATABASE, ENGINE, async_session
        try:
            DATABASE_URL = f"mysql+aiomysql://{username}:{password}@{url}:{port}/{dbname}?charset={charset}"

            DATABASE = Database(DATABASE_URL)
            ENGINE = create_async_engine(DATABASE_URL)  # , echo=True)

            # Асинхронная сессия
            async_session = sessionmaker(
                bind=ENGINE,
                class_=AsyncSession,
                expire_on_commit=False
            )

        except Exception as ex:
            print(f"Exception in: {ex}")

        return True

    @staticmethod
    def get_database() -> Database:
        return DATABASE

    @staticmethod
    def get_engine() -> Engine:
        return ENGINE

    # Функция для получения асинхронной сессии базы данных
    @staticmethod
    async def get_db():
        async with async_session() as session:
            yield session
