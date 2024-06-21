import requests, json


MESSAGES = {
 "START": 'Добро пожаловать в бота по удобному сбору и вывозу мусора.\nМы поможем вам легко и быстро сделать свое пространство чище и свободнее.\nРаботать с ботом просто!!',
 "REGISTRATION_MENU": 'Приветствуем вас в нашем боте.\nЕсли вы ранее уже пользовались ранее нашими услугами, то вы можете авторизоваться двумя способами:\nПо номеру телефона, просто отправьте в чат боту свой номер телефона (через кнопку Поделиться номером), либо просто текстом в формате 79124567898, бот проверит и авторизуем вам\nЧерез промокод, вы можете запросить его у менеджера, с которым взаимодействовали ранее. Полученный промокод просто отправьте боту в чат\nЕсли вы ранее не пользовались нашими услугами, то нажмите ниже кнопку Начать использовать бота для перехода к главное меню и выбора услуги\n\nЕсли по каким-то причинам у вас не получается авторизоваться, то напишите об этом менеджеру, он поможет решить возникшую ситуацию\nКонтакты менеджера:\n@ссылка_на_телеграм_аккаунте_менежера +79124567899',
 "MENU": 'Главное меню',
 "SETTINGS": 'В данном меню вы можете управлять настройками сервиса',
 "CREATE_ORDER": 'В какой день вам удобно принять курьера?',
 "APPLICATIONS_HISTORY": 'HERE История заявок',
 "MY_ADDRESSES": 'HERE Мои адреса',
 "ADD_ADDRESS": 'В данном меню вы можете управлять своими адресами:',
 "PAYMENTS": 'Ваши карты:',
 "QUESTIONNAIRE": 'Анкета:\nИмя: <b>{}</b>\nФамилия: <b>{}</b>\nТелефон: <b>{}</b>\nЕ-мейл: <b>{}</b>',
 "CHANGE_QUESTIONNAIRE": 'Выберите, что хотите изменить:',
 "NOTIFICATIONS": 'HERE Уведомления',
 "ABOUT": 'В данном боте вы можете создавать и настраивать заявки в сервисе 🔄  <b>Vtorbox</b>.\n\n - В пункте <i>"📝 Создать заявку"</i> вы выбираете ваш адрес, затем выбираете доступные даты для этого адреса, и также можете оставить комментарий к адресу.\n\n - В пункте <i>"📚 История заявок"</i> вы можете просматривать историю всех ваших заявок.\n\n - В пункте <i>"⚙ Настройки"</i> вы можете настраивать ваши данные: \n\n - 👤 Анкета: Добавьте Имя/Фамилию/Номер телефона/Email\n\n - 📆 Раписание вызова: Здесь вы можете добавить дни, в которые вы хотите, чтобы сервис обрабатывал заявки\n\n - 📍 Мои адреса: Можно добавить или удалить адреса, а также сделать адрес по умолчанию \n\n - 💰 Способы оплаты: Здесь будут храниться данные о ваших привязанных банковских картах',
 "GO_TO_MENU": 'Для возврата в главное меню нажмите кнопку ниже',
 "EMPTY_ADDRESS_RESULT": 'К сожалению, по вашему запросу не удалось найти нужный адрес\nПопробуйте еще раз',
 "CHOOSE_DEFAULT_ADDRESS": 'Выберите адрес по умолчанию',
 "CHOOSE_DELETE_ADDRESS": 'Выберите адрес для удаления',
 "DEFAULT_ADDRESS_IS_SELECTED": 'Адрес: <b>{}</b> выбран по умолчанию',
 "ADDRESS_WAS_ADDED": 'Адрес: <b>{}</b> успешно добавлен',
 "WRITE_YOUR_FIRSTNAME": 'Напишите ваше имя',
 "WRITE_YOUR_LASTNAME": 'Напишите вашу фамилию',
 "WRITE_YOUR_PHONE_NUMBER": 'Напишите номер телефон, начиная с 8',
 "WRITE_YOUR_EMAIL": 'Напишите адрес электронный почты',
 "WRITE_YOUR_DETAIL_ADDRESS": 'Введите ваш подъезд и номер квартиры',
 "WRITE_COMMENT_ADDRESS": 'Напишите комментарий к адресу: подъезд, этаж, квартира, домофон\nЕсли его нет, то нажмите кнопку ниже',
 "WRITE_COMMENT_ORDER": 'Напишите комментарий к заявке\nЕсли его нет, то нажмите кнопку ниже',
 "PHONE_NOT_FOUND": 'Не найден указанный номер телефона\nПопробуйте ввести номер текстом',
 "PROMOCODE_NOT_FOUND": 'Промокод не найден, можете обратиться к менеджеру',
 "ORDER_INFO": 'Заявка: № <b>{}</b>\nАдрес: <b>{}</b>\nКомментарий к адресу: <b>{}</b>\nДень вывоза: <b>{}</b>\nКомментарий к заявке: <b>{}</b>\nСтатус: <b>{}</b>\nТип контейнера: <b>{}</b>\nКоличество контейнеров: <b>{}</b>\nСумма заказа: <b>{}</b>\nЗаявка создана: <b>{}</b>',
 "SEND_SMS": 'На указанный номер телефона придет код(123)',
 "SEND_EMAIL": 'На указанный email придет код(123)',
 "WRONG_CODE": 'Неверный код',
 "SCHEDULE": 'Есть два варианта:\nПо запросу - вывезем мусор по вашей заявке. Для этого нужно будет каждый раз создавать заявку\nПо расписанию - будем вывозить мусор в определенные дни недели/месяца, заявки будут создаваться автоматически, бот будет вас уведомлять',
 "CHANGE_SCHEDULE": 'Адрес: <b>{}</b>\nРасписание: <b>{}</b>',
 "CHANGE_SCHEDULE_ADDRESS": 'Изменить расписание у <b>{}</b>',
 "WRONG_PHONE_NUMBER": 'Неверный номер телефона! Введите номер, начиная с 8',
 "WRONG_EMAIL": 'Неверный email!',
 "WRONG_FIRSTNAME": 'Неверное имя! Оно должно состоять из букв',
 "WRONG_LASTNAME": 'Неверная фамилия! Она должно состоять из букв',
 "WRONG_ADDRESS": 'К сожалению, ваш адрес сейчас не поддерживается нашим сервисом\n\nБот работает только в Москве(<b>Преображенское, Люблино, Орехово-Борисово Северное, Раменки</b>)\nПожалуйста, выберите адрес в пределах данных районов',
 "CHOOSE_SCHEDULE_PERIOD": 'Выберите по каким дням вывозить мусор:',
 "CHOOSE_DAY_OF_WEEK": 'Выберите дни недели',
 "CHOOSE_DAY_OF_MONTH": 'Выберите дни месяца',
 "SAVE_SCHEDULE": 'Ваше расписание сохранено',
 "ADD_NEW_ADDRESS": 'Отправьте адрес текстом или по кнопке с геопозицией\n\nДля точного поиска адреса указывайте максимально точный адрес(Москва, улица Потешная дом 8)',
 "CHOOSE_DATE_ORDER": 'Выберите дату вывоза:',
 "WRONG_ORDER_DATE": 'Неверный формат даты',
 "CHOOSE_ADDRESS_ORDER": 'Выберите адрес:',
 "CHOOSE_CONTAINER": 'Выберите тип контейнера для вывоза:',
 "CHOOSE_COUNT_CONTAINER": 'Введите количество контейнеров:',
 "ORDER_WAS_CREATED": 'Заявка создана! В ближайшее время она будет взята в работу',
 "ADDRESS_INFO_DEDAULT": '<b>Адрес № {}</b> (по умолчанию)\n{}',
 "ADDRESS_INFO_NOT_DEDAULT": '<b>Адрес № {}</b> \n{}',
 "YOU_HAVE_ACTIVE_ORDERS": 'У вас есть активные заявки ({})',
 "PAYMENT_ORDER": 'Заявка на оплату отправлена! Сейчас вам придет сообщение с ссылкой  для оплаты оплаты',
 "ORDER_HISTORY": 'История изменения статуса заказа: <b>{}</b>\n\n {}',
 "QUESTION_YES_NO": 'Уверены?',
 "YOUR_ORDERS": 'Список ваших заявок: ',
 "YOUR_ORDERS_BY_MONTH": 'Список ваших заявок по месяцам: ',
 "WRITE_TO_MANAGER": 'Добрый день!\n У меня есть вопрос по заявке {}',
 "CANCEL_ORDER_MESSAGE": 'Добрый день!\n Хочу отменить заявку {}',
 "CHOOSE_CHANGE_CONTAINER": 'Выберите что изменить: ',
 "ERROR_IN_HANDLER": 'Произошла ошибка! Пожалуйста, перезапустите бота по кнопке или перейдите персональной ссылке',
 "API_ERROR": 'Произошла ошибка на сервере!\nПожалуйста, попробуйте снова',
 "COURIER": 'Вы являетесь курьером сервиса\nДля просмотра маршрута нажмите кнопку ниже:',
 "NO_ROUTES": 'Hа текущий момент маршрута нет',
 "CURRENT_ROUTE": 'Текущий маршрут:',
 "ROUTE_INFO": 'Заявка #: <b>{}</b>({})\nАдрес: <b>{}</b>\nКомментарий к адресу: <b>{}</b>\nЗаказчик: <b>{}</b>\nТелефон: <b>{}</b>\nТип контейнера: <b>{}</b>\nКоличество: <b>{}</b>\nКомментарий к заявке: <b>{}</b>\nВаш комментарий: <b>{}</b>',
 "COMMENT_TO_POINT": 'Напишите причину отмены заказа:',
 "NO_ORDER": 'Список заявок пока пуст...',
 "NO_WORK_DAYS_FOR_ADDRESS": 'Мы добавили ваш адрес\nКак только наш сервис будет работать в вашем районе, то мы вам сообщим)\n\nСейчас работают районы: <b>Преображенское, Люблино, Орехово-Борисово Северное, Раменки</b>',
 "UNAVAILABLE_DAY": 'В данный день мы не можем вывозить(((',
 "YOUR_CHANGE_WAS_ADDED": 'Ваши изменения успешно применены',
 "ORDER_WAS_APPROVED": 'Заявка # <b>{}</b> успешно подтверждена',
 "ANY_TEXT": 'Главное меню',
 "NO_SCHEDULE_ADDRESS": '<b>Адресов пока нет</b>.\nДобавьте адреса, после этого сможете настроить расписание',
 "YOUR_ADD_ADDRESS": 'Адрес: <b>{}</b>',
 "ADDRESS_FOUND_BY_YANDEX": 'Найденный адрес: <b>{}</b>\n\nВерно?',
 "TRY_AGAIN_ADD_ADDRESS": 'Пожалуйста, попробуйте еще раз)',
 "NO_WORK_DAYS": 'На данный момент у адреса: <b>{}</b> отсутствуют дни вывоза\nВсе равно добавить адрес?',
 "NO_WORK_AREA": 'На данный момент в этом районе не принимаются заявки\nВсе равно добавить адрес?',
 "EMPTY_PAYMENTS": 'Пока у вас нет привязанных карт',
 "BACK_TO_ROUTES": 'Вернуться в курьерское меню',
 "BACK_TO_ORDER_LIST": 'Список заявок:',
 "CHOOSE_BOX_TYPE": 'Выберите тип контейнера',
 "CHOOSE_BOX_COUNT": 'Выберите количество контейнеров',
 "WRONG_CONTAINER_TYPE": 'Неверный тип контейнера',
 "WRONG_CONTAINER_COUNT": 'Неверное количество контейнеров',
 "PLEASE_ADD_NUMBER_OR_EMAIL": 'Для оплаты у вас должны быть указана телефон и email\nПожалуйста, укажите их в <b>настройки -> Анкета</b>',
 "YOUR_LINK_PAYMENT": 'Ссылка для оплаты:\n {}',
 "CARD_INFO": 'Номер карты: <b>{}</b>\nEmail: <b>{}</b>\nТелефон: <b>{}</b>',
 "CARD_WAS_DELETED": 'Карта успешно удалена',
 "PRESS_BUTTONS_MENU": 'Нажмите кнопку на клавиатуре',
 "ADD_MANUALLY_ADDRESS": 'Введите ваш адрес',
 "BACK": 'Для возврата назад нажмите кнопку внизу',
 "ORDER_WAS_DENY": 'Заявка # <b>{}</b> успешно отменена',
 "MESSAGE_PAYMENT_REQUIRED_ASK": 'От вас требуется оплата заявки (%ORDER_NUM%) по адресу (%ADDRESS_TEXT%) на сумму %AMOUNT%\n\nДля совершения оплаты вам нужно согласиться с <a href="https://vtorbox.ru/politics">политикой конфиденциальности</a>, <a href="https://vtorbox.ru/public">публичной офертой</a> и <a href="https://vtorbox.ru/agreement_reccurent">соглашением о подписке</a>\nВнимательно изучите данные документы и установите ниже галочку (нужно кликнуть по кнопке) и далее нажать кнопку Оплатить, после чего произвести оплату',
}



backend_host = '94.41.188.133'
api_url = f'http://{backend_host}:8000/api'

s = requests.Session()

def authorize(username='user3@example.com', password='string'):

    url = f"{api_url}/token"
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    }

    payload = f'username={username}&password={password}'
    
    response = requests.request("POST", url, headers=headers, data=payload)

    json_data = response.json()

    s.headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {json_data["access_token"]}'
    }

    print(response.json())

def get_settings():
    url = f'{api_url}/bot/settings?setting_type=бот'
    response = s.request("GET", url)

    return response.json()


def update_settings():
    settings_host = get_settings()



    for setting in MESSAGES:

        if setting['key'] in MESSAGES:
            print(f"Updating {setting['key']}")
            if setting['value'] == MESSAGES[setting['key']]:
                continue

            print("Setting value is different on host, updating")

            data =  json.dumps({
                "value": f"{MESSAGES[setting['key']]}"
            })

            headers = {
                'Content-Type': 'application/json'
            }

            request = s.put(f"{api_url}/bot/setting/{setting['id']}", data=data, headers=headers)
            print(request.status_code)
            #TODO: Если настройка не найдена то создать
        else:
            print(f"{setting['key']} not in messages")


def save_settings(settings):
    print('[')
    for setting in settings:
        print(f""" "{setting['key']}": {repr(setting['value'])},""")
    print(']')

    for setting in settings:
        if setting['key'] in MESSAGES:
            print(f"Updating {setting['key']}")
            if setting['value'] != MESSAGES[setting['key']]:
                print("Setting value is different on host, updating")

            continue
            data =  json.dumps({
                "value": f"{MESSAGES[setting['key']]}"
            })

            headers = {
                'Content-Type': 'application/json'
            }

            request = s.put(f"{api_url}/bot/setting/{setting['id']}", data=data, headers=headers)
            print(request.status_code)
            #TODO: Если настройка не найдена то создать
        else:
            print(f"{setting['key']} not in messages")


if __name__ == "__main__":
    authorize()
    # stgs = get_settings()
    # save_settings(stgs)
    update_settings()