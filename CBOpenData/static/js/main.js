$(".nav-item").find("a").click(function(e) {
    e.preventDefault();
    var section = $(this).attr("href");
    $("html, body").animate({
        scrollTop: $(section).offset().top + (-56)}, 400);
    return false;
});

$("a[href='#top']").click(function() {
    $("html, body").animate({ scrollTop: 0 }, 400);
    return false;
});