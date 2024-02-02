var current_page_user = 0
const MAX_PER_PAGE_USER = 20


function draw_main_window(data) {

    console.log('drawing user info')
    console.log(data)
    document.getElementById('login-form-wrapper').classList.add('hidden')

    document.getElementById('user-info').classList.remove('hidden')
    document.getElementById('root').classList.remove('hidden')

    document.getElementById('user-email-holder').innerText = data['user_data']['email']
    document.getElementById('user-roles-holder').innerText = data['token_data']['scopes']

    get_roles()
}


function init_users() {
    create_orders_option_handler()
    load_users()
}


function init_orders() {

}



function load_users() {
    console.log('Loading users')

    content_wrapper = document.getElementById('data-wrapper')
    content_wrapper.innerHTML = ''

    let page_wrapper = document.getElementById('page_num_wrap')
    page_wrapper.innerHTML = ''

    var myHeaders = new Headers();
    myHeaders.append("Authorization", `Bearer ${token}`);
    myHeaders.append("ngrok-skip-browser-warning", "application");

    var requestOptions = {
        method: 'GET',
        headers: myHeaders,
        redirect: 'follow'
    };

    page = current_page_user
    let with_orders = (document.getElementById('with_orders_select').value === "true")

    var user_search_optinos = new URLSearchParams({
        with_orders: document.getElementById('with_orders_select').value,
        limit: MAX_PER_PAGE_USER,
        role_name: document.getElementById('roles_select').value,
        show_deleted: document.getElementById('show_deleted').value,
        only_bot_users: document.getElementById('only_bot_users').value,
        page: page
    })

    fetch(`${api_url}/users?` + user_search_optinos, requestOptions)
        .then(response => response.json())
        .then((result) => {
            let order_th = ''
            if (with_orders) {
                order_th = '<th> orders </th>'
            }

            table = document.createElement('table')
            table.innerHTML += `<tr> 
            <th> email </th> 
            <th> telegram_id </th> 
            <th> telegram_username </th> 
            <th> phone_number </th> 
            <th> name </th> 
            <th> link_code </th>
            <th> roles </th> 
            ${order_th}
            </tr> `


            result['data'].forEach(element => {
                console.log(element)
                let tr = document.createElement('tr')

                view_button = document.createElement('input')
                view_button.type = 'button'
                view_button.addEventListener('click', () => {
                    view_user_orders(element.id)
                })
                view_button.value = 'просмотр заявок'

                let order_th = ''
                if (with_orders) {
                    order_th = `<th>${element.orders.length}</th>`
                }

                tr.innerHTML = `
                <th>${element.email ? element.email : '-' }</th>
                <th>${element.telegram_id ? element.telegram_id : '-'}</th>
                <th>${element.telegram_username ? `<a target="_blank" href='https://t.me/${element.telegram_username}'>${element.telegram_username}</a>` : '-'}</th>
                <th>${element.phone_number ? element.phone_number : "-"}</th>
                <th>${element.firstname ? element.firstname : "-"} ${element.secondname ? element.secondname : ""}</th>
                <th>${element.link_code ? element.link_code : "-"} </th>
                <th>${element.roles}</th>
                ${order_th}
                `

                edit_button = document.createElement('input')
                edit_button.type = 'button'
                edit_button.addEventListener('click', () => {
                    edit_user_data(element.id)
                })
                edit_button.value = 'редактировать'

                let th = document.createElement('th')
                th.append(edit_button)
                tr.append(th)

                if (with_orders) {
                    if (element.orders.length > 0) {
                        let th = document.createElement('th')
                        th.append(view_button)
                        tr.append(th)
                    } else {
                        tr.append(document.createElement('th'))
                    }
                }
                if (show_deleted) {
                    if (element.deleted_at) {
                        let th = document.createElement('th')
                        th.innerText = `удалён ${element.deleted_at}`
                        tr.append(th)
                    } else {
                        tr.append(document.createElement('th'))
                    }
                }

                table.append(tr)
            });

            content_wrapper.append(table)

            let page_count = Math.ceil(result['global_count'] / MAX_PER_PAGE_USER)
            console.log(`Page count ${page_count}`)

            for (let i = 0; i < page_count; i++) {
                let page_num = document.createElement('input')
                page_num.type = 'button'
                page_num.value = i

                page_num.addEventListener('click', () => {
                    current_page_user = i
                    load_users()
                })

                page_wrapper.append(page_num)
            }

        })
        .catch(error => console.log('error', error));
}


function view_user_orders(user_id) {
    console.log(user_id)
    var myHeaders = new Headers();
    myHeaders.append("Authorization", `Bearer ${token}`);
    myHeaders.append("ngrok-skip-browser-warning", "application");

    var requestOptions = {
        method: 'GET',
        headers: myHeaders,
        redirect: 'follow'
    };

    fetch(`${api_url}/users/orders?user_id=${user_id}`, requestOptions)
        .then(response => response.json())
        .then((result) => {

            let orders_data_wrapepr = document.createElement('div')
            orders_data_wrapepr.classList = 'orders_data'
            result.forEach(element => {
                let order_data_wrapepr = document.createElement('div')
                order_data_wrapepr.classList = 'order_data'
                order_data_wrapepr.innerHTML = `
                <p>Создана: ${element.date_created}</p>
                <p>Дата вывоза: ${element.day ? element.day : "Не определена"}</p>
                <p>Номер заявки пользователя: ${element.user_order_num}</p>
                <p>Айди заявки: ${element.id}</p>
                <br>
                <p>Данные адреса:</p>
                <p>Адрес: ${element.address_data.address}</p>
                ${element.address_data.main ? `<p>Основной: ${element.address_data.main}</p>` : ""}
                ${element.address_data.detail ? `<p>Уточнение: ${element.address_data.detail}</p>` : ""}
                ${element.address_data.district ? `<p>Район: ${element.address_data.district}</p>` : ""}
                ${element.address_data.interval ? `<p>Интервал: ${element.address_data.interval}</p>` : ""}
                ${element.address_data.interval_type ? `<p>Тип интервала: ${element.address_data.interval_type}</p>` : ""}
                ${element.address_data.distance_from_mkad ? `<p>Расстояние от МКАД: ${element.address_data.distance_from_mkad}км</p>` : ""}
                ${element.address_data.point_on_map ? `<p>Точка на карте: <a>${element.address_data.point_on_map}</a></p>` : ""}
                <br>
                <p>Данные контейнера:</p>
                ${element.box_data.box_name? `<p>Наименование: ${element.box_data.box_name}</p>` : ""}
                ${element.box_count? `<p>Кол-во: ${element.box_count}</p>` : ""}
                ${element.box_data.pricing_default? `<p>Цена по умолчанию: ${element.box_data.pricing_default}</p>` : ""}
                <br>
                <p>Статус заявки: ${element.status_data.status_name}</p>
                <p>${element.status_data.description}</p>
                <button onclick="view_order_status_history(order_id='${element.id}')"> просмотр истории статуса </button>
                <hr>
                `

                orders_data_wrapepr.append(order_data_wrapepr)
                console.log(element)
            });
            show_modal('show_user_orders', orders_data_wrapepr)
        })
        .catch(error => console.log('error', error));
}


function view_order_status_history(order_id) {

    console.log(user_id)
    var myHeaders = new Headers();
    myHeaders.append("Authorization", `Bearer ${token}`);
    myHeaders.append("ngrok-skip-browser-warning", "application");

    var requestOptions = {
        method: 'GET',
        headers: myHeaders,
        redirect: 'follow'
    };

    fetch(`${api_url}/users/orders?user_id=${user_id}`, requestOptions)
        .then(response => response.json())
        .then((result) => {

            forEach(element => {

            });
            show_modal('show_user_orders', orders_data_wrapepr)
        })
        .catch(error => console.log('error', error));

}


function create_orders_option_handler() {
    content_wrapper = document.getElementById('content-wrapper')
    content_wrapper.innerHTML = ''

    document.getElementById('content-wrapper').innerHTML = `
                <div>
                <label>
                    Роль: 
                    <input name="role_name" id="roles_select" list="roles_list_id">
                </label>

                <label>
                    Показывать с заявками:
                    <select name="with_orders_select" id="with_orders_select">
                        <option value="false">Нет</option>
                        <option value="true">Да</option>
                    </select>
                </label>

                <label>
                    Показывать удалённых
                    <select name="show_deleted" id="show_deleted">
                        <option value="false">Нет</option>
                        <option value="true">Да</option>
                    </select>
                </label>

                <label>
                    Только пользователи бота
                    <select name="only_bot_users" id="only_bot_users">
                        <option value="false">Нет</option>
                        <option value="true">Да</option>
                    </select>
                </label>

                <button onclick="load_users()">Поиск</button>
                </div>
            <div id="data-wrapper"></div>

            <div id='page_num_wrap'>
            
            </div>
            <div> 
                <button onclick=show_modal('create_user')> Создать пользователя <button>
            </div>

    `
}


function edit_user_data(user_id) {
    var myHeaders = new Headers();
    myHeaders.append("Authorization", `Bearer ${token}`);
    myHeaders.append("ngrok-skip-browser-warning", "application");

    var requestOptions = {
        method: 'GET',
        headers: myHeaders,
        redirect: 'follow'
    };

    fetch(`${api_url}/user/${user_id}`, requestOptions)
        .then(response => response.json())
        .then((result) => {
            console.log(result)
            input_field = create_edit_fields(result)
            show_modal('edit_user', input_field)
        })
        .catch(error => console.log('error', error));
}


function create_edit_fields(element) {
    let keys = Object.keys(element)
    let input_wrapper = document.createElement('div')
    input_wrapper.classList = 'edit-wrapper'

    for (key of keys) {
        let input_label = document.createElement('label')
        input_label.innerText = `${key}: `

        let input = document.createElement('input')
        input.type = 'text'
        input.value = element[key]
        input.id = `${element.id}-${key}`
        input.classList = 'data-sent'

        input_label.append(input)
        input_wrapper.append(input_label)

        console.log(`${key}: ${element[key]}`)
    }

    let delete_user_button = document.createElement('input')
    delete_user_button.type = 'button'
    delete_user_button.value = 'delete user (soft)'
    delete_user_button.addEventListener('click', () => {
        delete_user(element.id)
    })


    let confirm_button = document.createElement('input')
    confirm_button.type = 'button'
    confirm_button.value = 'confirm'
    confirm_button.addEventListener('click', ()=>{
        update_user_data(element.id)
    })

    input_wrapper.append(confirm_button, delete_user_button)
    return input_wrapper
}


function update_user_data(){

}


function delete_user(user_id) {
    console.log(`Deleteing user ${user_id}`)
    var myHeaders = new Headers();
    myHeaders.append(`Authorization", "Bearer ${token}`);
    myHeaders.append("ngrok-skip-browser-warning", "application");

    var requestOptions = {
        method: 'DELETE',
        headers: myHeaders,
        redirect: 'follow'
    };
    if (!confirm("Удалить пользователя?")) {
        return
    }

    fetch(`${api_url}/users/?user_id=${user_id}`, requestOptions)
        .then((response) => {
            return response.json()
        })
        .then((result) => {
            if (result == null) {
                alert('Пользователь удалён')
            } else if (result.message) {
                alert(result.message)
            }
        })
        .catch((error) => {
            alert(error.message)
        });
}


function create_modal_wrapper() {
    let modal_wrapper = document.createElement('div')
    modal_wrapper.classList = 'modal active_modal'

    modal_list = document.getElementsByClassName('modal')
    modal_wrapper.id = `modal_${modal_list.length}`

    close_button = document.createElement('input')
    close_button.type = 'button'
    close_button.value = 'X'
    close_button.classList = 'close_modal_wrapper'
    close_button.id = `close_${modal_list.length}`

    close_button.addEventListener('click', () => {
        console.log('CIC')
        document.getElementById(modal_wrapper.id).remove()
    })

    modal_wrapper.append(close_button)

    return modal_wrapper
}


function show_modal(type, data) {
    console.log(type)

    let modal_wrapper = create_modal_wrapper()

    switch (type) {
        case 'create_user':
            console.log("Creating usercreate modal")
            let new_text = document.createElement('p')
            new_text.innerText = 'usermodel'
            modal_wrapper.append(new_text)
            document.body.append(modal_wrapper)
            break

        case 'show_user_orders':
            console.log("Showing Creating show_user_orders modal")
            modal_wrapper.append(data)
            document.body.append(modal_wrapper)

        case 'edit_user':
            console.log("Showing edit_user modal")
            modal_wrapper.append(data)
            document.body.append(modal_wrapper)
        default:
            return
    }
}


function get_roles() {
    console.log("Getting roles")

    var myHeaders = new Headers();
    myHeaders.append("Authorization", `Bearer ${token}`);
    myHeaders.append("ngrok-skip-browser-warning", "application");


    var requestOptions = {
        method: 'GET',
        headers: myHeaders,
        redirect: 'follow'
    };

    fetch("http://127.0.0.1:8000/api/roles", requestOptions)
        .then(response => response.json())
        .then((result) => {
            roles = result
            let container = document.getElementById('roles_list_id')
            roles.forEach(element => {
                container.innerHTML += `<option value='${element["role_name"]}'>`
            });
            container.innerHTML += `<option value=''>`
            console.log(result)
        })
        .catch(error => console.log('error', error));
}


document.getElementById('main-menu').addEventListener('click', e => {
    console.log(e.target.tagName)
    if (e.target.tagName == 'LI') {
        let menu_elem = document.getElementById('main-menu').childNodes[1].children
        for (element of menu_elem) {
            element.classList.remove('active-page')
        }

        e.target.classList.add('active-page')
    }
})