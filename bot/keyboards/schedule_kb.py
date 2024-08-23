from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from bot.keyboards.base_keyboards import BaseKeyboard
from bot.utils.buttons import BUTTONS


class ScheduleKeyboard(BaseKeyboard):

    def change_btn(self, address_id: str) -> InlineKeyboardMarkup:
        """Кнопка 'изменить' на расписание адреса"""

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text='изменить',
                                 callback_data=f'change_period_{address_id}')
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def change_schedule_btn(self) -> ReplyKeyboardMarkup:
        """Кпопки для изменения расписаний вызова"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text='По запросу'),
            KeyboardButton(text='По дням')
        )

        builder.row(
            KeyboardButton(text=BUTTONS['BACK_SCHEDULE_ADDRESS_LIST']),
        )
        builder.row(
            KeyboardButton(text=BUTTONS['MENU'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def back_schedule_address(self) -> ReplyKeyboardMarkup:

        builder = ReplyKeyboardBuilder()

        builder.row(
            KeyboardButton(text=BUTTONS['BACK_SCHEDULE_ADDRESS']),
        )
        builder.row(
            KeyboardButton(text=BUTTONS['MENU'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def schedule_period_btn(self) -> ReplyKeyboardMarkup:
        """Выбор периода для создания пользовательского расписания"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text='Дни недели'),
            KeyboardButton(text='Дни месяца')
        )

        builder.row(
            KeyboardButton(text=BUTTONS['BACK_SETTINGS']),
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def day_of_week_btn(self, work_days: list[dict], selected_day_of_week: list[str]) -> InlineKeyboardMarkup:
        """Кнопки для отображения дней недели"""

        builder = InlineKeyboardBuilder()
        days = {
            'monday': 'Понедельник',
            'tuesday': 'Вторник',
            'wednesday': 'Среда',
            'thursday': 'Четверг',
            'friday': 'Пятница',
            'saturday': 'Суббота',
            'sunday': 'Воскресенье'}
        unique_work_days = set([day.get('weekday') for day in work_days])

        for day in days:
            if day in selected_day_of_week:
                builder.row(
                    InlineKeyboardButton(
                        text=f'✅  {days[day]}',
                        callback_data=f'day_of_week_{day}'
                    )
                )

            else:
                if day in unique_work_days:
                    builder.row(
                        InlineKeyboardButton(
                            text=f'🟢  {days[day]}',
                            callback_data=f'day_of_week_{day}'
                        )
                    )
                else:
                    builder.row(
                        InlineKeyboardButton(
                            text=f'🔴 {days[day]}',
                            callback_data=f'error_day_of_week'
                        )
                    )

        builder.row(
            InlineKeyboardButton(
                text='Сохранить',
                callback_data=f'save_day_of_week'
            )
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def day_of_month_btn(self, total_days: int, selected_day_of_month: list[str]) -> InlineKeyboardMarkup:
        """Кнопки для отображения дней месяца"""

        builder = InlineKeyboardBuilder()
        for day in range(1, total_days + 1):
            if str(day) in selected_day_of_month:
                builder.add(
                    InlineKeyboardButton(
                        text=f'✔️ {str(day)}',
                        callback_data=f'day_of_month_{day}'
                    )
                )
            else:
                builder.add(
                    InlineKeyboardButton(
                        text=str(day),
                        callback_data=f'day_of_month_{day}'
                    )
                )

        builder.row(
            InlineKeyboardButton(
                text='Сохранить',
                callback_data=f'save_day_of_month'
            )
        )
        builder.adjust(4)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
