$(".bingo-card").each(function() {
    for(let i = 0; i < 27; i++){
        $(this).append('<div class="bingo-spot"></div>');
    }
});

$(".bingo-card .bingo-spot").on("click", function() {
    api_request("check_spot", {space_number: Number($(this).children("img").attr('alt'))}, this).done(function(r){
        if(r.resp == 1){
            console.log($(this));
            $(this).children("img").addClass("called");
        }
    });
});