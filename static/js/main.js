
const checkp = (e) => {
    const password = document.querySelector('#password')
    const cpassword = document.querySelector('#cpassword')
    var meter = document.getElementById('password-strength-meter');
    var text = document.getElementById('password-strength-text');
    
    const msg = document.getElementById('msg')
    const submit = document.getElementById('subm')

    var strength = {
        0: "Worst",
        1: "Bad",
        2: "Weak",
        3: "Good",
        4: "Strong"
    }
    var result = zxcvbn(password.value);
    meter.value = result.score;

    if (password.value !== "") {
        text.innerHTML = "Strength: " + strength[result.score];
    } else {
        text.innerHTML = "";
    }

    if (strength[result.score] == "Worst") {
        msg.style.setProperty('color', 'red', 'important');
        msg.innerHTML = 'Set a stronger Password';
        submit.disabled = true
        return false
    }

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
    }, 6000);

    $('#tableusers').DataTable({
        responsive: true,
    });

    $('#tab1').DataTable({
        responsive: true,
    });

    var table = $('#tab9').DataTable({
        columns: [
            { width: '5%' },
            { width: '0%' },
            { width: '0%' },
            { width: '0%%' },
            { width: '10%' },
            { width: '15%' },
            { width: '10%' },
            { width: '10%' },
            { width: '10%' },
            { width: '14%' },
        ],
        "ordering": true,
        responsive: true,
        className: 'dt-body-left',
        className: 'dt-head-left', 
        "scrollX": true
    });

    table.column(1).visible(false).draw()
    table.column(2).visible(false).draw()
    table.column(3).visible(false).draw()
    table.column(0).order('desc').draw()

    $('#categoryxdf').change(function () {
        table.column(1).search(this.value).draw()
    })

    $('#datexdf').change(function() {
        table.draw()
    })


    
    let nav = document.getElementsByTagName('nav')[0]
    
    $('body').css({
        'padding-top': nav.offsetHeight + "px"
    })

    $(window).on('load', function() {
        $('body').css({
            'padding-top': nav.offsetHeight + "px"
        })
    })

    $(window).on('resize', function () {
        $('body').css({
            'padding-top': nav.offsetHeight + "px"
        })
    })

    $.fn.dataTable.ext.search.push(
        function (settings, data, dataIndex) {
            var max = new Date()
            max.setDate(max.getDate())
            var sel = $('#datexdf').val()
            if (sel == null) return true;
            var min = new Date()
            min.setDate(min.getDate() - sel)

            var startDate = new Date(data[2]);

            if (min == null && max == null) return true;
            if (min == null && startDate <= max) return true;
            if (max == null && startDate >= min) return true;
            if (startDate <= max && startDate >= min) return true;
            return false;
        }
    );


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

    (function (original) {
        jQuery.fn.clone = function () {
            var result = original.apply(this, arguments),
                my_textareas = this.find('textarea').add(this.filter('textarea')),
                result_textareas = result.find('textarea').add(result.filter('textarea')),
                my_selects = this.find('select').add(this.filter('select')),
                result_selects = result.find('select').add(result.filter('select'));

            for (var i = 0, l = my_textareas.length; i < l; ++i) $(result_textareas[i]).val($(my_textareas[i]).val());
            for (var i = 0, l = my_selects.length; i < l; ++i) result_selects[i].selectedIndex = my_selects[i].selectedIndex;

            return result;
        };
    })(jQuery.fn.clone);

        

});

function clearfilters(e) {
    $('#datexdf').val('Date Range')
    $('#categoryxdf').val('Category')
    var table = $('#tab9').DataTable()
    table
        .search('')
        .columns().search('')
        .draw();

}


function handleChange(checkbox) {
    
    const check = checkbox.parentElement.parentElement.parentElement

    
    let checkboxes = check.getElementsByClassName('checkbox-inline')
    let cc = check.getElementsByClassName('cc')

    for (var i=0; i<checkboxes.length; i++) {
        checkboxes[i].childNodes[1].disabled = !checkbox.checked
        checkboxes[i].childNodes[1].checked = false
    }

    for (var i = 0; i < cc.length; i++) {
        cc[i].childNodes[1].checked = false
    }


}

function hchange(checkbox) {
    const check = checkbox.parentElement.parentElement

    let checkboxes = checkbox.parentElement.nextSibling.nextSibling
    let subcheckboxes = checkboxes.getElementsByClassName('cc')


    for (var i =0; i<subcheckboxes.length;i++) {
        subcheckboxes[i].childNodes[1].disabled = !checkbox.checked
        subcheckboxes[i].childNodes[1].checked = false
    }
}



