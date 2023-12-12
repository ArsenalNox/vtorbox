from sqlalchemy.orm import Session

from app.models import engine, Address, UsersAddress, Users
from bot.services.base import BaseService


class UserService(BaseService):
    @classmethod
    def create_user(cls, tg_id: int):
        """Создание пользователей"""

        user = cls.get_user_by_tg_id(tg_id)

        with Session(engine, expire_on_commit=False) as session:
            if not user:
                user = Users(
                    telegram_id=tg_id
                )
                session.add(user)
                session.commit()

    @classmethod
    def get_users_addresses(cls, tg_id):
        """Получение всех адресов данного пользователя"""

        with Session(engine, expire_on_commit=False) as session:
            addresses = session.query(Address). \
                join(UsersAddress, UsersAddress.address_id == Address.id). \
                join(Users, UsersAddress.user_id == Users.id). \
                where(Users.telegram_id == tg_id).all()

            return addresses

    @classmethod
    def get_users_addresses_without_main(cls, tg_id):
        """Получение всех адресов данного пользователя"""

        with Session(engine, expire_on_commit=False) as session:
            addresses = session.query(Address). \
                join(UsersAddress, UsersAddress.address_id == Address.id). \
                join(Users, UsersAddress.user_id == Users.id). \
                where(Users.telegram_id == tg_id, Address.main == False).all()

            return addresses

    @classmethod
    def get_users_address_by_address_id(cls, address_id: str):
        with Session(engine, expire_on_commit=False) as session:
            users_address = session.query(UsersAddress).filter_by(
                address_id=address_id
            ).first()

            if users_address:
                return users_address
