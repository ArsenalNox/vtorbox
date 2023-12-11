from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.keyboards import Keyboard
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class TextHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = Keyboard()

    def handle(self):
        @self.router.message(F.text.startswith(BUTTONS['CREATE_APPLICATION']))
        async def create_application(message: Message, state: FSMContext):
            """Создание заявки"""

            await message.answer(
                MESSAGES['CREATE_APPLICATION'],
                reply_markup=self.kb.start_menu_btn()
            )

            # async with aiohttp.ClientSession() as session:
            #     async with session.get(settings.base_url + 'users') as resp:
            #         print(resp.status)
            #         print(await resp.text())

        @self.router.message(F.text.startswith(BUTTONS['APPLICATIONS_HISTORY']))
        async def applications_history(message: Message, state: FSMContext):
            """Создание заявки"""

            await message.answer(
                MESSAGES['APPLICATIONS_HISTORY'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['SETTINGS']))
        async def get_settings(message: Message, state: FSMContext):
            """Получение настроек бота"""

            await message.answer(
                MESSAGES['SETTINGS'],
                reply_markup=self.kb.settings_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['MY_ADDRESSES']))
        async def get_my_addresses(message: Message, state: FSMContext):
            """Получение всех адресов пользователя"""

            await message.answer(
                MESSAGES['MY_ADDRESSES'],
                reply_markup=self.kb.add_address_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['PAYMENTS']))
        async def get_payments(message: Message, state: FSMContext):
            """Получение способов оплаты пользователя"""

            await message.answer(
                MESSAGES['PAYMENTS'],
                reply_markup=self.kb.settings_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['QUESTIONNAIRE']))
        async def get_questionnaire(message: Message, state: FSMContext):
            """Получение анкеты пользователя"""

            await message.answer(
                MESSAGES['QUESTIONNAIRE'],
                reply_markup=self.kb.settings_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['NOTIFICATIONS']))
        async def get_notifications(message: Message, state: FSMContext):
            """Получение анкеты пользователя"""

            await message.answer(
                MESSAGES['NOTIFICATIONS'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['ABOUT']))
        async def get_about_info(message: Message, state: FSMContext):
            """Получение анкеты пользователя"""

            await message.answer(
                MESSAGES['ABOUT'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['ADD_ADDRESS']))
        async def get_add_addres(message: Message, state: FSMContext):
            """Получение анкеты пользователя"""

            await message.answer(
                MESSAGES['ADD_ADDRESS'],
                reply_markup=self.kb.start_menu_btn()
            )
