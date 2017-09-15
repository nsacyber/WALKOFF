(function(app) {

var platformBrowserDynamic = ng.platformBrowserDynamic.platformBrowserDynamic;

document.addEventListener('DOMContentLoaded', function() {
  platformBrowserDynamic().bootstrapModule(app.AppModule);
});

})(window.app = window.app || {});


$('.message a').click(function(){
   $('form').animate({height: "toggle", opacity: "toggle"}, "slow");
});