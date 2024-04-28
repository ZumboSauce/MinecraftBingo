$(".bingo-machine").on('bingo-machine:call', function (e, texture) {
    $(this).prepend(`<div class="bingo-roll" style="--idx: 1"><div style="background-image: url(${texture})"></div>`);
    $(this).children(":not(.flush)").last().addClass("flush").animate({'flex-grow': 0}, {duration: 3000, easing: "swing", queue: false, start: function() {
        $(this).siblings().first().animate({'flex-grow': 1}, {duration: 3000, easing: "swing", queue: false});
    }, 
    complete: function() {
        $(this).remove();
    }});
});