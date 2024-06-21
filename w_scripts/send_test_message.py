from app.utils import send_message_through_bot

'b3bdc515-cfd6-4a80-9e5d-caee44e36cd0'

send_message_through_bot(
    368262500,
    message=f"От вас требуется подверждение заявки ({123}) по адресу (Ул. Тверская) по временному итервалу 17:00-20:00",
    btn={
        "inline_keyboard" : [
        [{
            "text" : "Подтвердить",
            "callback_data": f"confirm_order_12342536",
        }],
        [{
            "text" : "Отказаться",
            "callback_data": f"deny_order_124353647",
        }],
    ]}
)