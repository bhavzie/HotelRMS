
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

function ssd(selectobj) {
    const val = selectobj.value
    const fff = document.getElementById('fff')
    const ggg = document.getElementById('ggg')

    if (val == 'tour') {
        ggg.style.display = 'block';
        fff.style.display = 'none';
    } else if(val == 'corporate') {
        fff.style.display = 'block';
        ggg.style.display = 'none';
    } else{
        ggg.style.display = 'none';
        fff.style.display = 'none';
    }
}

$(document).ready(function () {

    setTimeout(function(){
        $("div.alert").remove();
    }, 3000);

    $('#tableusers').DataTable();

});


function handleChange(checkbox) {
    
    const check = checkbox.parentElement.parentElement.parentElement
    
    let checkboxes = check.getElementsByClassName('checkbox-inline')
    
    for (var i=0; i<checkboxes.length; i++) {
        checkboxes[i].childNodes[1].disabled = !checkbox.checked
        checkboxes[i].childNodes[1].checked = false
    }

}



$(document).ready(function () {
    //the trigger on hover when cursor directed to this class
    $(".core-menu li").hover(
        function () {
            //i used the parent ul to show submenu
            $(this).children('ul').slideDown('fast');
        },
        //when the cursor away 
        function () {
            $('ul', this).slideUp('fast');
        });
    //this feature only show on 600px device width
    $(".hamburger-menu").click(function () {
        $(".burger-1, .burger-2, .burger-3").toggleClass("open");
        $(".core-menu").slideToggle("fast");
    });

    $('.dropdown-menu li').on('click', function () {
        var getValue = $(this).text();
        $('.dropdown-select').text(getValue);
    });
}); 

