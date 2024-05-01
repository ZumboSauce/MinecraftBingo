function api_request(query, args, ctx){
    if(typeof ctx !== "undefined") {
        return $.ajax({
            type: 'post',
            url: '/php/bingo_api.php',
            context: ctx,
            data: { QUERY: query, ARGS: JSON.stringify(args)},
            dataType: 'json'
        });
    } else {
        return $.ajax({
            type: 'post',
            url: '/php/bingo_api.php',
            data: { QUERY: query, ARGS: JSON.stringify(args)},
            dataType: 'json'
        });
    }

}

$("#id01 .tab_container :not(.close)").on("click", function(){
    $("#id01 .popup-mc > *").css("display", "none");
    switch($(this).attr('class')){
        case 'login':
            $("#login").css("display", "grid");
            break;
        case 'signup':
            $("#signup").css("display", "grid");
            break;
        default:
            break;
    }
});

function span_input_fetch(target_form){
    let data = {};
    console.log(target_form.children());
    target_form.find(".sign-mc-input span").each(function() {
        data[$(this).attr('name')] = $(this).text();
    });
    return data;
}

$('#login-form').on('submit', function (e) {
    e.preventDefault();
    $.ajax({
        type: 'post',
        url: '/assets/php/bingo_login.php',
        data: span_input_fetch($(this)),
        success: function () {
            alert('thang');
        }
    });
});

$('#signup-form').on('submit', function (e) {
    e.preventDefault();
    $.ajax({
        type: 'post',
        url: '/assets/php/bingo_signup.php',
        data: span_input_fetch($(this)),
        success: function () {
            alert('thang');
        }
    });
});

for(let i = 0; i < 6; i++){
    $('#id02 .bingo-card_container').append('<div class=bingo-card_wrapper><div class="bingo-card"></div></div>');
}

for(let i = 0; i < 7; i++) {
    $("#bingo-machine .bingo-machine").append(`<div class="bingo-roll" style="flex-grow: 1"><div></div></div>`);
}

$("#id02 #bingo-cards .button-mc_container button").on('click', function(){
    api_request('bingo', {}).done(function(r){
        if(r.resp == 1){
            console.log('bingo');
        } else {
            console.log("cum bingo");
        }
    })
});


$("#id01 tab_container button[name='bingo-login']").trigger("click");

async function textures_load(){
    const resp = await fetch('/assets/texture.json');
    const textures = await resp.json();
    return textures;
}

textures_load().then(textures => {
    api_request("request_cards", {}).done(function(r){
        for (const [idx, card] of r.resp.entries()){
            console.log(card);
            for (const spot of card){
                $(`#id02 .bingo-card_container .bingo-card_wrapper:nth-child(${idx+1}) .bingo-spot:nth-child(${spot['idx']+1})`).append(`<img src="${textures[textures["idx"][spot.number]].texture}" alt="${spot.number}" ${spot.called==1 ? 'class="called"' : ''}>`);
            }
        }
    }).fail(function(r){
        console.log("b");
    });
    var bingo_sse_reconnect_time = 1;
    function bingo_sse_connect(){
        bingosrv = new EventSource("http://localhost:8080/");
        bingosrv.addEventListener("call", function(event) {
            item = JSON.parse(event.data).call;
            $("#bingo-machine .bingo-machine").trigger("bingo-machine:call", textures[textures["idx"][item]].texture);
        });
        bingosrv.addEventListener("bingo_alert", function(event) {
            console.log(JSON.parse(event.data).tgt)
            console.log(`wait for winners to be announced in ${(JSON.parse(event.data).tgt - Date.now()) / 1000000}`);
        });
        bingosrv.addEventListener("bingo", function(event) {
            console.log("wholesome");
        });
        bingosrv.onopen = (e) => {
            bingo_sse_reconnect_time = 1;
        };
        bingosrv.onerror = (err) => {
            bingosrv.close();
            bingo_sse_reconnect_time *= 2;
            setTimeout(() => {bingo_sse_connect();}, bingo_sse_reconnect_time * 1000);
            console.log(bingo_sse_reconnect_time);
        };
    }
    bingo_sse_connect();
});