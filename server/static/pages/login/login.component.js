(function(app) {

app.LoginComponent = LoginComponent;
function LoginComponent() {
  this.title = 'WALKOFF';
}

LoginComponent.annotations = [
  new ng.core.Component({
    selector: 'login-page',
    templateUrl: 'static/pages/login/index.html',
    styleUrls: ['/static/pages/login/style.css']
  })
];

})(window.app = window.app || {});
