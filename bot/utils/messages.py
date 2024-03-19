start_text = """
Добро пожаловать в бота по удобному сбору и вывозу мусора.
Мы поможем вам легко и быстро сделать свое пространство чище и свободнее.
Работать с ботом просто!

"""

registration_menu_text = """
Приветствуем вас в нашем боте.
Если вы ранее уже пользовались ранее нашими услугами, то вы можете авторизоваться двумя способами:
По номеру телефона, просто отправьте в чат боту свой номер телефона (через кнопку Поделиться номером), либо просто текстом в формате 79124567898, бот проверит и авторизуем вам
Через промокод, вы можете запросить его у менеджера, с которым взаимодействовали ранее. Полученный промокод просто отправьте боту в чат
Если вы ранее не пользовались нашими услугами, то нажмите ниже кнопку Начать использовать бота для перехода к главное меню и выбора услуги

Если по каким-то причинам у вас не получается авторизоваться, то напишите об этом менеджеру, он поможет решить возникшую ситуацию
Контакты менеджера:
@ссылка_на_телеграм_аккаунте_менежера
+79124567899

"""

order_info_text = """
Заявка: № <b>{}</b>
Адрес: <b>{}</b>
День вывоза: <b>{}</b>
Комментарий к заявке: <b>{}</b>
Статус: <b>{}</b>
Тип контейнера: <b>{}</b>
Количество контейнеров: <b>{}</b>
Сумма заказа: <b>{}</b>
Заявка создана: <b>{}</b>

"""

questionnaire_text = """
Анкета:
Имя: <b>{}</b>
Фамилия: <b>{}</b>
Телефон: <b>{}</b>
Е-мейл: <b>{}</b>
"""


schedule_text = """
Есть два варианта:
По запросу - вывезем мусор по вашей заявке. Для этого нужно будет каждый раз создавать заявку
По расписанию - будем вывозить мусор в определенные дни недели/месяца, заявки будут создаваться автоматически, бот будет вас уведомлять

"""


MESSAGES = {
    'START': start_text,
    'REGISTRATION_MENU': registration_menu_text,
    'MENU': 'Главное меню',
    'SETTINGS': 'В данном меню вы можете управлять настройками сервиса',
    'CREATE_ORDER': 'В какой день вам удобно принять курьера?',
    'APPLICATIONS_HISTORY': 'HERE История заявок',
    'MY_ADDRESSES': 'HERE Мои адреса',
    'ADD_ADDRESS': 'В данном меню вы можете управлять своими адресами:',
    'PAYMENTS': 'Данный раздел находится в разработке',
    'QUESTIONNAIRE': questionnaire_text,
    'CHANGE_QUESTIONNAIRE': 'Выберите, что хотите изменить:',
    'NOTIFICATIONS': 'HERE Уведомления',
    'ABOUT': 'Для вашего удобства мы записали небольшое видео по использованию бота, не забудьте с ним ознакомится.',
    'GO_TO_MENU': 'Для возврата в главное меню нажмите кнопку ниже',
    'EMPTY_ADDRESS_RESULT': 'К сожалению, по вашему запросу не удалось найти нужный адрес\nПопробуйте еще раз',
    'CHOOSE_DEFAULT_ADDRESS': 'Выберите адрес по умолчанию',
    'CHOOSE_DELETE_ADDRESS': 'Выберите адрес для удаления',
    'DEFAULT_ADDRESS_IS_SELECTED': 'Адрес: <b>{}</b> выбран по умолчанию',
    'ADDRESS_WAS_ADDED': 'Адрес: <b>{}</b> успешно добавлен',
    'WRITE_YOUR_FIRSTNAME': 'Напишите ваше имя',
    'WRITE_YOUR_LASTNAME': 'Напишите вашу фамилию',
    'WRITE_YOUR_PHONE_NUMBER': 'Напишите номер телефон, начиная с 8',
    'WRITE_YOUR_EMAIL': 'Напишите адрес электронный почты',
    'WRITE_YOUR_DETAIL_ADDRESS': 'Введите ваш подъезд и номер квартиры',
    'WRITE_COMMENT_ADDRESS': 'Напишите комментарий к адресу\nЕсли его нет, то нажмите кнопку ниже',
    'WRITE_COMMENT_ORDER': 'Напишите комментарий к заявке\nЕсли его нет, то нажмите кнопку ниже',
    'PHONE_NOT_FOUND': 'Не найден указанный номер телефона\nПопробуйте ввести номер текстом',
    'PROMOCODE_NOT_FOUND': 'Промокод не найден, можете обратиться к менеджеру',
    'ORDER_INFO': order_info_text,
    'SEND_SMS': 'На указанный номер телефона придет код(123)',
    'SEND_EMAIL': 'На указанный email придет код(123)',
    'WRONG_CODE': 'Неверный код',
    'SCHEDULE': schedule_text,
    'CHANGE_SCHEDULE': 'Адрес: <b>{}</b>\nРасписание: <b>{}</b>',
    'CHANGE_SCHEDULE_ADDRESS': 'Изменить расписание у <b>{}</b>',
    'WRONG_PHONE_NUMBER': 'Неверный номер телефона! Введите номер, начиная с 8',
    'WRONG_EMAIL': 'Неверный email!',
    'WRONG_FIRSTNAME': 'Неверное имя! Оно должно состоять из букв',
    'WRONG_LASTNAME': 'Неверная фамилия! Она должно состоять из букв',
    'WRONG_ADDRESS': 'В пределах Москвы ваш адрес не найден\nБот работает только в Москве, пожалуйста, выберите геопозицию или адрес в пределах Москвы',
    'CHOOSE_SCHEDULE_PERIOD': 'Выберите по каким дням вывозить мусор:',
    'CHOOSE_DAY_OF_WEEK': 'Выберите дни недели',
    'CHOOSE_DAY_OF_MONTH': 'Выберите дни месяца',
    'SAVE_SCHEDULE': 'Ваше расписание сохранено',
    'ADD_NEW_ADDRESS': 'Отправьте адрес в виде строки (город улица дом подъезд квартира) или по кнопке с геопозицией',
    'CHOOSE_DATE_ORDER': 'Выберите дату вывоза:',
    'WRONG_ORDER_DATE': 'Неверный формат даты',
    'CHOOSE_ADDRESS_ORDER': 'Выберите адрес:',
    'CHOOSE_CONTAINER': 'Выберите тип контейнера для вывоза:',
    'CHOOSE_COUNT_CONTAINER': 'Введите количество контейнеров:',
    'ORDER_WAS_CREATED': 'Заявка создана! В ближайшее время она будет взята в работу',
    'ADDRESS_INFO_DEDAULT': '<b>Адрес № {}</b> (по умолчанию)\n{}',
    'ADDRESS_INFO_NOT_DEDAULT': '<b>Адрес № {}</b> \n{}',
    'YOU_HAVE_ACTIVE_ORDERS': 'У вас есть активные заявки ({})',
    'PAYMENT_ORDER': 'Для оплаты заказа: {} перейдите по ссылке: {}',
    'ORDER_HISTORY': 'История изменения статуса заказа: <b>{}</b>\n\n {}',
    'QUESTION_YES_NO': 'Уверены?',
    'YOUR_ORDERS': 'Список ваших заявок: ',
    'YOUR_ORDERS_BY_MONTH': 'Список ваших заявок по месяцам: ',
    'WRITE_TO_MANAGER': 'Добрый день!\n У меня есть вопрос по заявке {}',
    'CANCEL_ORDER_MESSAGE': 'Добрый день!\n Хочу отменить заявку {}',
    'CHOOSE_CHANGE_CONTAINER': 'Выберите что изменить: ',
    'ERROR_IN_HANDLER': 'Произошла ошибка! Пожалуйста, перезапустите бота по кнопке или перейдите персональной ссылке',
    'API_ERROR': 'Произошла ошибка на сервере!\nПожалуйста, попробуйте снова',
    'COURIER': 'Вы являетесь курьером сервиса\nДля просмотра маршрута нажмите кнопку ниже:',
    'NO_ROUTES': 'Hа текущий момент маршрута нет',
    'CURRENT_ROUTE': 'Текущий маршрут:',
    'ROUTE_INFO': 'Точка: {}',
    'COMMENT_TO_POINT': 'Причина:',
    'NO_ORDER': 'Список заявок пока пуст...',
    'NO_WORK_DAYS_FOR_ADDRESS': 'По данному адресу нет доступных дат для вывоза',
    'UNAVAILABLE_DAY': 'В данный день мы не можем вывозить(((',
    'YOUR_CHANGE_WAS_ADDED': 'Ваши изменения успешно применены',
    'ORDER_WAS_APPROVED': 'Заявка # <b>{}</b> успешно подтверждена',
    'ANY_TEXT': 'Главное меню',
    'NO_SCHEDULE_ADDRESS': '<b>Адресов пока нет</b>.\nДобавьте адреса, после этого сможете настроить расписание',
    'YOUR_ADD_ADDRESS': 'Адрес: <b>{}</b>',
    'ADDRESS_FOUND_BY_YANDEX': 'Найденный адрес: <b>{}</b>\n\nВерно?',
    'TRY_AGAIN_ADD_ADDRESS': 'Пожалуйста, попробуйте еще раз)',
}
