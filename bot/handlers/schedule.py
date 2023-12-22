from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.schedule_kb import ScheduleKeyboard
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.messages import MESSAGES


class NotificationHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = ScheduleKeyboard()

    def handle(self):
        @self.router.message(F.text.startswith(BUTTONS['SCHEDULE']))
        async def get_schedule(message: Message, state: FSMContext):
            """Получение расписаний вызова пользователя"""

            # запрос на получение текущего выбранного расписания
            await message.answer(
                MESSAGES['SCHEDULE'],
            )
            await message.answer(
                MESSAGES['CHANGE_SCHEDULE'],
                reply_markup=self.kb.change_schedule_btn()
            )

        @self.router.message(F.text.startswith('По запросу'))
        async def dispatch_upon_request(message: Message, state: FSMContext):
            """Изменение расписания вывоза у пользователя на 'По запросу'"""

            # запрос на изменение расписания отправки на 'По запросу'

            await get_schedule(
                message=message,
                state=state
            )

        @self.router.message(F.text.startswith('По расписанию'))
        async def dispatch_upon_schedule(message: Message, state: FSMContext):
            """Изменение расписания вызова у пользователя по собственному расписанию"""

            await message.answer(
                MESSAGES['CHOOSE_SCHEDULE_PERIOD'],
                reply_markup=self.kb.schedule_period_btn()
            )

        @self.router.message(F.text.startswith('Дни недели'))
        async def choose_day_of_week(message: Message, state: FSMContext):
            """Выбор дня недели"""

            pass

        @self.router.message(F.text.startswith('Дни месяца'))
        async def choose_day_of_month(message: Message, state: FSMContext):
            """Выбор дня месяца"""

            pass