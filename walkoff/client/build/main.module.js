"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
var core_1 = require("@angular/core");
var http_1 = require("@angular/http");
var platform_browser_1 = require("@angular/platform-browser");
var forms_1 = require("@angular/forms");
var http_2 = require("@angular/http");
var ng_bootstrap_1 = require("@ng-bootstrap/ng-bootstrap");
var ngx_datatable_1 = require("@swimlane/ngx-datatable");
var ng2_toasty_1 = require("ng2-toasty");
var ng2_select2_1 = require("ng2-select2");
var angular2_jwt_1 = require("angular2-jwt");
var angular2_jwt_refresh_1 = require("angular2-jwt-refresh");
var ng_pick_datetime_1 = require("ng-pick-datetime");
var ng2_dnd_1 = require("ng2-dnd");
var routing_1 = require("./routing");
var main_component_1 = require("./main/main.component");
var scheduler_component_1 = require("./scheduler/scheduler.component");
var playbook_component_1 = require("./playbook/playbook.component");
var devices_component_1 = require("./devices/devices.component");
var messages_component_1 = require("./messages/messages.component");
var cases_component_1 = require("./cases/cases.component");
var settings_component_1 = require("./settings/settings.component");
var dashboard_component_1 = require("./dashboard/dashboard.component");
var interfaces_component_1 = require("./interfaces/interfaces.component");
var scheduler_modal_component_1 = require("./scheduler/scheduler.modal.component");
var devices_modal_component_1 = require("./devices/devices.modal.component");
var cases_modal_component_1 = require("./cases/cases.modal.component");
var settings_user_modal_component_1 = require("./settings/settings.user.modal.component");
var settings_roles_modal_component_1 = require("./settings/settings.roles.modal.component");
var playbook_argument_component_1 = require("./playbook/playbook.argument.component");
var playbook_conditions_component_1 = require("./playbook/playbook.conditions.component");
var playbook_transforms_component_1 = require("./playbook/playbook.transforms.component");
var settings_roles_component_1 = require("./settings/settings.roles.component");
var messages_modal_component_1 = require("./messages/messages.modal.component");
var keys_pipe_1 = require("./pipes/keys.pipe");
var MainModule = (function () {
    function MainModule() {
    }
    return MainModule;
}());
MainModule = __decorate([
    core_1.NgModule({
        imports: [
            platform_browser_1.BrowserModule,
            forms_1.FormsModule,
            forms_1.ReactiveFormsModule,
            http_2.HttpModule,
            routing_1.RoutingModule,
            ng_bootstrap_1.NgbModule.forRoot(),
            ngx_datatable_1.NgxDatatableModule,
            ng2_toasty_1.ToastyModule.forRoot(),
            ng2_select2_1.Select2Module,
            ng_pick_datetime_1.DateTimePickerModule,
            ng2_dnd_1.DndModule.forRoot(),
        ],
        declarations: [
            main_component_1.MainComponent,
            playbook_component_1.PlaybookComponent,
            dashboard_component_1.DashboardComponent,
            scheduler_component_1.SchedulerComponent,
            devices_component_1.DevicesComponent,
            messages_component_1.MessagesComponent,
            cases_component_1.CasesComponent,
            settings_component_1.SettingsComponent,
            interfaces_component_1.InterfacesComponent,
            scheduler_modal_component_1.SchedulerModalComponent,
            devices_modal_component_1.DevicesModalComponent,
            cases_modal_component_1.CasesModalComponent,
            settings_user_modal_component_1.SettingsUserModalComponent,
            settings_roles_modal_component_1.SettingsRoleModalComponent,
            messages_modal_component_1.MessagesModalComponent,
            playbook_argument_component_1.PlaybookArgumentComponent,
            playbook_conditions_component_1.PlaybookConditionsComponent,
            playbook_transforms_component_1.PlaybookTransformsComponent,
            settings_roles_component_1.SettingsRolesComponent,
            keys_pipe_1.KeysPipe,
        ],
        providers: [{
                provide: angular2_jwt_refresh_1.JwtHttp,
                useFactory: getJwtHttp,
                deps: [http_1.Http, http_1.RequestOptions],
            }],
        entryComponents: [
            scheduler_modal_component_1.SchedulerModalComponent,
            devices_modal_component_1.DevicesModalComponent,
            cases_modal_component_1.CasesModalComponent,
            settings_user_modal_component_1.SettingsUserModalComponent,
            settings_roles_modal_component_1.SettingsRoleModalComponent,
            messages_modal_component_1.MessagesModalComponent,
        ],
        bootstrap: [main_component_1.MainComponent],
    })
], MainModule);
exports.MainModule = MainModule;
function getJwtHttp(http, options) {
    var jwtOptions = {
        endPoint: '/api/auth/refresh',
        beforeSeconds: 300,
        tokenName: 'refresh_token',
        refreshTokenGetter: (function () {
            var token = sessionStorage.getItem('refresh_token');
            if (token && angular2_jwt_1.tokenNotExpired(null, token)) {
                return token;
            }
            location.href = '/login';
            return;
        }),
        tokenSetter: (function (res) {
            res = res.json();
            if (!res.access_token) {
                sessionStorage.removeItem('access_token');
                sessionStorage.removeItem('refresh_token');
                location.href = '/login';
                return false;
            }
            sessionStorage.setItem('access_token', res.access_token);
            return true;
        }),
    };
    var authConfig = new angular2_jwt_1.AuthConfig({
        noJwtError: true,
        tokenName: 'access_token',
        tokenGetter: (function () { return sessionStorage.getItem('access_token'); }),
    });
    return new angular2_jwt_refresh_1.JwtHttp(new angular2_jwt_refresh_1.JwtConfigService(jwtOptions, authConfig), http, options);
}
exports.getJwtHttp = getJwtHttp;
