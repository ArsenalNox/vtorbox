async function request_token() {
    user_email = document.getElementById('user-email').value
    user_password = document.getElementById('user-password').value

    const formData = new FormData()

    formData.append('username', user_email)
    formData.append('password', user_password)
    console.log(formData)


    var myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/x-www-form-urlencoded");
    myHeaders.append("ngrok-skip-browser-warning", "application");

    var urlencoded = new URLSearchParams();
    urlencoded.append("username", user_email);
    urlencoded.append("password", user_password);

    var requestOptions = {
        method: 'POST',
        headers: myHeaders,
        body: urlencoded,
        redirect: 'follow'
    };

    fetch(`${api_url}/token`, requestOptions)
        .then(
            response => response.json()
        )
        .then((result) => {
            localStorage.setItem("token", result['access_token'])
            console.log(result)
            location.reload()
        })
        .catch(error => console.log('error', error));
}


function restore_auth() {
    token = localStorage.getItem("token")
    if (token != null) {
        var myHeaders = new Headers();
        myHeaders.append("Authorization", `Bearer ${token}`);
        myHeaders.append("ngrok-skip-browser-warning", "application");

        var requestOptions = {
            method: 'GET',
            headers: myHeaders,
            redirect: 'follow'
        };

        fetch(`${api_url}/users/me`, requestOptions)
            .then((response) => {
                console.log(response.status)
                if (response.status == 200) {
                    return response.json()
                } else {
                    if (localStorage.getItem("token") != null){
                        localStorage.setItem("token", null)
                    }
                    throw 'error'
                }
            })
            .then((result) => {
                draw_main_window(result)
            })
            .catch(error => console.log('error', error));
    }
}


function logout() {
    localStorage.setItem("token", null)
    location.reload()
}

restore_auth()