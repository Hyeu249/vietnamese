$(document).ready(function() {
    // check if window.location.host is equal to 'qlt.vsico.com.vn'
    if (window.location.host == 'qlt.vsico.com.vn') {
        // if true, then print the message
        console.log('This is qlt.vsico.com.vn');
    } else {
        // if false, then print the message
        console.log('This is not qlt.vsico.com.vn');
        // flash the navbar
        setInterval(function() {
            $('.o_main_navbar').css('background-color', '#a23e2c');
            setTimeout(function() {
                $('.o_main_navbar').css('background-color', '#71639e');
            }, 1000);
        }, 2000);
    }
});