from sqlalchemy import create_engine, MetaData
from databases import Database
from sqlalchemy.engine.base import Engine
from typing import Any

DATABASE_URL = "mysql+aiomysql://username:password@localhost:3306/dbname?charset=cp1251"

DATABASE = Database
METADATA = MetaData()

ENGINE = Engine


class GlobControlDatabase:
    @staticmethod
    def set_url(username: str, password: str, url: str, port: Any, dbname: str, charset: str = 'cp1251') -> bool:
        global DATABASE_URL, DATABASE, ENGINE
        try:
            DATABASE_URL = f"mysql+aiomysql://{username}:{password}@{url}:{port}/{dbname}?charset={charset}"
            print(DATABASE_URL)
            DATABASE = Database(DATABASE_URL)
            ENGINE = create_engine(DATABASE_URL)

        except Exception as ex:
            print(f"Exception in: {ex}")

        return True

    @staticmethod
    def get_database() -> Database:
        return DATABASE

    @staticmethod
    def get_engine() -> Engine:
        return ENGINE
