$(document).ready(function(){
    var myApp = angular.module('settingsPageApp', [], function($interpolateProvider) {
        $interpolateProvider.startSymbol('{a');
        $interpolateProvider.endSymbol('a}');
    });
});
