from sqlalchemy.orm import Session

from app.models import engine, Users


class Singleton(type):
    """Синглтон для БД"""

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class BaseService(metaclass=Singleton):
    @classmethod
    def get_user_by_tg_id(cls, tg_id: int):
        """Получение пользователя по tg_id"""

        with Session(engine, expire_on_commit=False) as session:
            user = session.query(Users).filter_by(telegram_id=tg_id).first()
            if user:
                return user
