
const checkp = () => {
    const password = document.querySelector('#password')
    const cpassword = document.querySelector('#cpassword')
    
    const msg = document.getElementById('msg')
    const submit = document.getElementById('subm')

    if (password.value == cpassword.value) {
        msg.style.setProperty('color', 'green', 'important');
        msg.innerHTML = 'Passwords Match'
        submit.disabled = false
    }
    else {
        msg.style.setProperty('color', 'red', 'important');
        msg.innerHTML = 'Passwords Do Not Match'
        submit.disabled = true
    }
}

$(document).ready(function () {

    setTimeout(function(){
        $("div.alert").remove();
    }, 3000);

});