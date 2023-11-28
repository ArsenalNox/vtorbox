## Данные

### Пользователи
- Тгайди
- Фио 
- Номер 
- Почта

### Заявки 
- Адрес заявки
- Тгайди(Пользователь)
- Статус заяки (на рассмотрении, ждёт ответа пользователя, выполняется, ожидает оплаты)
- Курьер айди(Курьер)
- Комментарий

```Если пул заявок единственный и на 1 день каждый день, можно реализовать её флагом выборки
Статус в таблице заявок у менеждера можно обновлять через вебсокет? или обычный поллинг

Так же с комментариями от курьеров

Выставление счёта по апдейту статуса на завершённый
```

### Курьеры
- Координаты
- Данные курьера

### Отчёт
Отчёты можно генерить через xlsxwriter каждый день по джобе на таймере
Если надо хранить + просматривать историю можно сохранять генерируемые отчёты и выводить их в браузере
Так же можно опционально сохранять только те, что генерируются автоматически а те что вручную можно просто выводить и удалять

### Менеджер/Админ
- Логин/пароль

## Что сейчас требуется
1. Образец заявки
2. Образец их гугл таблиц

## Как реализуется
- RESTfull api, запросы под манипуляцию заявок, аунтефикацию можно проводить через api токен который отдельно будем выдавать под ботов и под сайт
- При скейлинге через docker нужно будет хранить таблицы или на гугл диске или на другом сревисе, иначе у каждого инстанса будет своя история
- Джобы так же через отдельный сервис, пока что можно в одном
- Фронт

## Запросы

### Зявки
- Создание заявки
- Получение заявки/заявок
- Обновление статуса заявки
- Получение заявки
- Подтверждение заявки

### Курьеры
- Регистрация курьера
- Получение списка курьеров
- Получение истории курьера
- Получение подходящих/указанных заявок курьеру

### Менеджер
- Статсы курьеров?
- Получение отчётов по дням
- Получение данных о заявках в реальном(?) времени


## Алгоритм работы
- Пользователь оставляет заявку 
- Менеждер её смотрит и подтверждает 
- Пользователю отправляется сообщение о том что приедет курьер 
- Он соглашается
- Курьеру даётся заявка на вывоз
- Курьер выполняет заявку, отмечает её 
- Высылается счёт оплаты