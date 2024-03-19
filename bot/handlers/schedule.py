import datetime
import json
import pprint
from calendar import monthrange

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.handlers.base_handler import Handler
from bot.keyboards.schedule_kb import ScheduleKeyboard
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn, format_schedule_text
from bot.utils.messages import MESSAGES
from bot.utils.requests_to_api import req_to_api


class ScheduleHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = ScheduleKeyboard()

    def handle(self):
        @self.router.message(F.text.startswith(BUTTONS['SCHEDULE']))
        async def get_schedule(message: Message, state: FSMContext):
            """Получение расписаний вызова пользователя"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            if data.get('msg_ids'):
                for address_id_temp, msg_id in data.get('msg_ids').items():
                    await message.bot.delete_message(
                        chat_id=data.get('chat_id'),
                        message_id=msg_id
                    )

                await state.update_data(msg_ids={})

            # запрос на получение текущего выбранного расписания
            # по всем адрес для данного пользователя
            # прикрепляем кнопку 'изменить' и вшиваем id адреса или расписания

            await message.answer(
                MESSAGES['SCHEDULE'],
            )

            status_code, address_list = await req_to_api(
                method='get',
                url=f'bot/user/addresses/all?tg_id={message.chat.id}',
            )
            msg_ids = {}
            if address_list:
                for address in address_list:
                    address_text = address.get('address') + address.get('detail') if address.get('detail') else address.get('address')
                    text = format_schedule_text(
                        type_interval=address.get('interval_type'),
                        interval=address.get('interval')
                    )
                    msg = await message.answer(
                        MESSAGES['CHANGE_SCHEDULE'].format(
                            address_text,
                            text
                        ),
                        reply_markup=self.kb.change_btn(address.get('id'))
                    )
                    msg_ids[address['id']] = msg.message_id
                await state.update_data(msg_ids=msg_ids)

            else:
                await message.answer(
                    MESSAGES['NO_SCHEDULE_ADDRESS']
                )

            await message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.callback_query(F.data.startswith('change_period'))
        async def catch_schedule_id(callback: CallbackQuery, state: FSMContext):
            """Отлавливаем у какого именно адреса поменять расписание"""

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            address_id = callback.data.split('_')[-1]

            # удаляем клавиатуру с расписаниями
            if data.get('msg_ids'):
                for address_id_temp, msg_id in data.get('msg_ids').items():
                    await callback.bot.edit_message_reply_markup(
                        chat_id=data.get('chat_id'),
                        message_id=msg_id,
                        reply_markup=None
                    )

                await state.update_data(msg_ids={})

            # запрос на получение адреса по address_id
            status_code, address = await req_to_api(
                method='get',
                url=f'bot/user/addresses/{address_id}?tg_id={callback.message.chat.id}',
            )

            # сохраняем для отправки на бэк
            await state.update_data(address_id=address_id)
            address_text = address.get('address') + address.get('detail', ' ') if address.get('detail') else address.get('address')
            await callback.message.answer(
                MESSAGES['CHANGE_SCHEDULE_ADDRESS'].format(
                    address_text
                ),
                reply_markup=self.kb.change_schedule_btn()
            )

        @self.router.message(F.text.startswith('По запросу'))
        async def dispatch_upon_request(message: Message, state: FSMContext):
            """Изменение расписания вывоза у пользователя на 'По запросу'"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            address_id = data.get('address_id')

            # запрос на изменение расписания отправки на 'По запросу' и address_id
            create_schedule_data = json.dumps(
                {
                    'address_id': address_id,
                    'interval_type': 'on_request'
                }
            )

            status_code, response = await req_to_api(
                method='put',
                url=f'bot/user/addresses/{address_id}/schedule/?tg_id={message.chat.id}',
                data=create_schedule_data
            )

            await get_schedule(
                message=message,
                state=state
            )

        @self.router.message(F.text.startswith('По дням'))
        async def choose_day(message: Message, state: FSMContext):
            """Выбор дня недели"""

            await state.update_data(chat_id=message.chat.id)
            # список выбранных дат
            await state.update_data(selected_day_of_week=[])
            data = await state.get_data()

            address_id = data.get('address_id')
            # запрос на получение адреса по address_id
            status_code, address = await req_to_api(
                method='get',
                url=f'bot/user/addresses/{address_id}?tg_id={message.chat.id}',
            )
            work_days = address.get('work_dates')

            msg = await message.answer(
                MESSAGES['CHOOSE_DAY_OF_WEEK'],
                reply_markup=self.kb.day_of_week_btn(
                    work_days=work_days,
                    selected_day_of_week=data.get('selected_day_of_week')
                )
            )
            await state.update_data(inline_message_id_day_of_week=message.message_thread_id)
            await state.update_data(msg=msg.message_id)
            await state.update_data(work_days=work_days)

        @self.router.callback_query(F.data.startswith('day_of_week'))
        async def get_day_of_week(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            work_days = data.get('work_days')

            selected_date = callback.data.split('_')[-1]

            if selected_date in data['selected_day_of_week']:
                data['selected_day_of_week'].remove(selected_date)
            else:
                data['selected_day_of_week'].append(selected_date)

            await callback.message.edit_reply_markup(
                data['inline_message_id_day_of_week'],
                reply_markup=self.kb.day_of_week_btn(
                    work_days=work_days,
                    selected_day_of_week=data['selected_day_of_week']
                )
            )

        @self.router.callback_query(F.data.startswith('error_day_of_week'))
        async def catch_unavailable_day_schedule(callback: CallbackQuery, state: FSMContext):
            """Отлавливаем не рабочий день для этого адреса"""

            await state.update_data(chat_id=callback.message.chat.id)
            await callback.answer(
                MESSAGES['UNAVAILABLE_DAY'],
                show_alert=True
            )

        @self.router.callback_query(F.data.startswith('save_day_of'))
        async def save_schedule_period(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            address_id = data.get('address_id')
            selected_day_of_week = data.get('selected_day_of_week')
            create_schedule_data = json.dumps(
                {
                    'address_id': address_id,
                    'selected_day_of_week': selected_day_of_week
                }
            )
            await state.update_data(selected_day_of_month=[])
            await state.update_data(selected_day_of_week=[])

            status_code, response = await req_to_api(
                method='put',
                url=f'bot/user/addresses/{address_id}/schedule/?tg_id={callback.message.chat.id}',
                data=create_schedule_data
            )
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
