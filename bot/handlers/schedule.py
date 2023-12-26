import datetime
from calendar import monthrange

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

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
            # по всем адрес для данного пользователя
            # прикрепляем кнопку 'изменить' и вшиваем id адреса или расписания
            await message.answer(
                MESSAGES['SCHEDULE'],
            )
            await message.answer(
                MESSAGES['CHANGE_SCHEDULE'],
                reply_markup=self.kb.change_btn()

            )

        @self.router.callback_query(F.data.startswith('change_period'))
        async def catch_schedule_id(callback: CallbackQuery, state: FSMContext):
            """Отлавливаем у какого именно адреса поменять расписание"""

            address_id = callback.data.split('_')[-1]
            # получаем адрес по его id

            # сохраняем для отправки на бэк
            await state.update_data(address_id=address_id)

            await callback.message.answer(
                'Изменить расписание у "Название адреса"',
                reply_markup=self.kb.change_schedule_btn()
            )

        @self.router.message(F.text.startswith('По запросу'))
        async def dispatch_upon_request(message: Message, state: FSMContext):
            """Изменение расписания вывоза у пользователя на 'По запросу'"""
            data = await state.get_data()

            address_id = data['address_id']

            # запрос на изменение расписания отправки на 'По запросу' и address_id

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

            # список выбранных дат
            await state.update_data(selected_day_of_week=[])

            data = await state.get_data()

            await message.answer(
                MESSAGES['CHOOSE_DAY_OF_WEEK'],
                reply_markup=self.kb.day_of_week_btn(selected_day_of_week=data['selected_day_of_week'])
            )
            await state.update_data(inline_message_id_day_of_week=message.message_thread_id)


        @self.router.callback_query(F.data.startswith('day_of_week'))
        async def get_day_of_week(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            selected_date = callback.data.split('_')[-1]

            if selected_date in data['selected_day_of_week']:
                data['selected_day_of_week'].remove(selected_date)
            else:
                data['selected_day_of_week'].append(selected_date)

            await callback.message.edit_reply_markup(
                data['inline_message_id_day_of_week'],
                reply_markup=self.kb.day_of_week_btn(selected_day_of_week=data['selected_day_of_week'])
            )


        @self.router.message(F.text.startswith('Дни месяца'))
        async def choose_day_of_month(message: Message, state: FSMContext):
            """Выбор дня месяца"""

            # список выбранных дат
            await state.update_data(selected_day_of_month=[])

            data = await state.get_data()

            # получаем количество дней в текущем месяце
            current_year = datetime.datetime.now().year
            current_month = datetime.datetime.now().month
            total_days = monthrange(current_year, current_month)[1]

            await state.update_data(total_days=total_days)

            await message.answer(
                MESSAGES['CHOOSE_DAY_OF_MONTH'],
                reply_markup=self.kb.day_of_month_btn(total_days, data['selected_day_of_month'])
            )
            await state.update_data(inline_message_id_day_of_month=message.message_thread_id)

            await message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.callback_query(F.data.startswith('day_of_month'))
        async def get_day_of_month(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            selected_date = callback.data.split('_')[-1]

            if selected_date in data['selected_day_of_month']:
                data['selected_day_of_month'].remove(selected_date)
            else:
                data['selected_day_of_month'].append(selected_date)

            await callback.message.edit_reply_markup(
                data['inline_message_id_day_of_month'],
                reply_markup=self.kb.day_of_month_btn(
                    selected_day_of_month=data['selected_day_of_month'],
                    total_days=data['total_days'])
            )

        @self.router.callback_query(F.data.startswith('save_day_of'))
        async def save_schedule_period(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            address_id = data['address_id']
            selected_day_of_month = data.get('selected_day_of_month')
            selected_day_of_week = data.get('selected_day_of_week')
            print(data)

            # запрос в бэк на сохранение расписания для текущего пользователя с address_id

            await callback.message.answer(
                MESSAGES['SAVE_SCHEDULE']
            )

            await callback.message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )

            # переход к отображению расписания
            await get_schedule(
                message=callback.message,
                state=state
            )