(function(app) {

app.AppModule = AppModule;
function AppModule() { }

AppModule.annotations = [
  new ng.core.NgModule({
    imports: [ ng.platformBrowser.BrowserModule ],
    declarations: [
      app.LoginComponent
    ],
    bootstrap: [ app.LoginComponent ],
  })
]

})(window.app = window.app || {});
