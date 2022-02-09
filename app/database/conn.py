from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import logging


class SQLAlchemy:
    def __init__(self, app: FastAPI = None, **kwargs):
        self._engine = None
        self._session = None
        if app is not None:
            self.init_app(app=app, **kwargs)

    def init_app(self, app: FastAPI, **kwargs):
        """
        DB 초기화 함수
        :param app: FastAPI 인스턴스
        :param kwargs:
        :return:
        """
        database_url = kwargs.get("DB_URL")
        pool_recycle = kwargs.setdefault("DB_POOL_RECYCLE", 900)
        echo = kwargs.setdefault("DB_ECHO", True)

        self._engine = create_engine(
            database_url,
            echo=echo,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,
        )
        self._session = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

        @app.on_event("startup")
        def startup():
            self._engine.connect()
            logging.info("DB connected.")

        @app.on_event("shutdown")
        def shutdown():
            self._session.close_all()
            self._engine.dispose()
            logging.info("DB disconnected")

    def get_db(self):
        """
        요청마다 DB 세션 유지 함수
        :return:
        """
        if self._session is None:
            raise Exception("must be called 'init_app'")
        db_session = None
        try:
            db_session = self._session()
            yield db_session
        finally:
            db_session.close()

    @property
    def session(self):
        return self.get_db

    @property
    def engine(self):
        return self._engine

    @classmethod
    def create(cls, session: Session, auto_commit=False, **kwargs):
        """
        테이블 데이터 적재 전용 함수
        :param session:
        :param auto_commit: 자동 커밋 여부
        :param kwargs: 적재 할 데이터
        :return:
        """
        obj = cls()
        for col in obj.all_columns():
            col_name = col.name
            if col_name in kwargs:
                setattr(obj, col_name, kwargs.get(col_name))
        session.add(obj)
        session.flush()
        if auto_commit:
            session.commit()
        return obj

    @classmethod
    def get(cls, session: Session = None, **kwargs):
        """
        Simply get a Row
        :param session:
        :param kwargs:
        :return:
        """
        sess = next(db.session()) if not session else session
        query = sess.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)

        if query.count() > 1:
            raise Exception("Only one row is supposed to be returned, but got more than one.")

        result = query.first()

        if not session:
            sess.close()

        return result

    @classmethod
    def filter(cls, session: Session = None, **kwargs):
        """
        Simply get a Row

        :param session:
        :param kwargs:
        :return:
        """
        cond = []
        for key, val in kwargs.items():
            key = key.split("__")
            if len(key) > 2:
                raise Exception("No 2 more dunders")
            col = getattr(cls, key[0])

            if len(key) == 1:
                cond.append((col == val))
            elif len(key) == 2 and key[1] == 'gt':
                cond.append((col > val))
            elif len(key) == 2 and key[1] == 'gte':
                cond.append((col >= val))
            elif len(key) == 2 and key[1] == 'lt':
                cond.append((col < val))
            elif len(key) == 2 and key[1] == 'lte':
                cond.append((col <= val))
            elif len(key) == 2 and key[1] == 'in':
                cond.append((col.in_(val)))

        obj = cls()
        if session:
            obj._session = session
            obj.served = True
        else:
            obj._session = next(db.session())
            obj.served = False

        query = obj._session.query(cls)
        query = query.filter(*cond)
        obj._q = query

        return obj


db = SQLAlchemy()
Base = declarative_base()
# target_metadata = Base.metadata
