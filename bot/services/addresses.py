from sqlalchemy.orm import Session

from app.models import Address, UsersAddress, engine, Users
from bot.services.base import BaseService
from bot.services.users import UserService


class AddressService(BaseService):

    @classmethod
    def get_address_by_id(cls, address_id: str):
        """Получение адреса по его id"""

        with Session(engine, expire_on_commit=False) as session:
            address = session.query(Address).filter_by(id=address_id).first()
            if address:
                return address

    @classmethod
    def create_user_address(cls, address_text: str, latitude: str, longitude: str, tg_id: int):
        """Создание адреса пользователя"""

        user = cls.get_user_by_tg_id(tg_id)
        with Session(engine, expire_on_commit=False) as session:

            # получаем адрес по координатам и если его нет, создаем новый
            address = session.query(Address).filter_by(
                latitude=latitude,
                longitude=longitude
            ).first()

            if not address:
                # создаем новый адрес
                address = Address(
                    address=address_text,
                    latitude=latitude,
                    longitude=longitude
                )
                session.add(address)

                session.commit()

            user_address = UsersAddress(
                user_id=user.id,
                address_id=address.id
            )
            session.add(user_address)

            session.commit()

    @classmethod
    def mark_address_to_main(cls, address: Address, old_main_address: Address):
        """Помечаем адрес как основной"""

        with Session(engine, expire_on_commit=False) as session:
            address.main = True
            if old_main_address and address != old_main_address:
                old_main_address.main = False
                session.add(old_main_address)

            session.add(address)
            session.commit()

    @classmethod
    def get_main_address(cls, tg_id: int):
        """Получение главного адреса (main=True)"""

        with Session(engine, expire_on_commit=False) as session:
            main_address = session.query(Address).\
                join(UsersAddress, UsersAddress.address_id == Address.id).\
                join(Users, UsersAddress.user_id == Users.id). \
                where(Users.telegram_id == tg_id, Address.main == True).first()

            return main_address

    @classmethod
    def delete_address_by_id(cls, address_id: str):
        """Удаление адреса по его id"""

        with Session(engine, expire_on_commit=False) as session:
            address = cls.get_address_by_id(address_id)
            user_address = UserService.get_users_address_by_address_id(address_id)

            # сначала удаляем запись из таблицы users_address
            session.delete(user_address)
            session.commit()

            # и удаляем сам адрес
            session.delete(address)
            session.commit()

