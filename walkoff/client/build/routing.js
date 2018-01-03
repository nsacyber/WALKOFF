"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
var core_1 = require("@angular/core");
var router_1 = require("@angular/router");
var dashboard_component_1 = require("./dashboard/dashboard.component");
var playbook_component_1 = require("./playbook/playbook.component");
var scheduler_component_1 = require("./scheduler/scheduler.component");
var devices_component_1 = require("./devices/devices.component");
var messages_component_1 = require("./messages/messages.component");
var cases_component_1 = require("./cases/cases.component");
var settings_component_1 = require("./settings/settings.component");
var interfaces_component_1 = require("./interfaces/interfaces.component");
var routes = [
    { path: '', redirectTo: '/playbook', pathMatch: 'full' },
    { path: 'dashboard', component: dashboard_component_1.DashboardComponent },
    { path: 'playbook', component: playbook_component_1.PlaybookComponent },
    { path: 'scheduler', component: scheduler_component_1.SchedulerComponent },
    { path: 'devices', component: devices_component_1.DevicesComponent },
    { path: 'messages', component: messages_component_1.MessagesComponent },
    { path: 'cases', component: cases_component_1.CasesComponent },
    { path: 'settings', component: settings_component_1.SettingsComponent },
    { path: 'interfaces/:interfaceName', component: interfaces_component_1.InterfacesComponent },
];
var RoutingModule = (function () {
    function RoutingModule() {
    }
    return RoutingModule;
}());
RoutingModule = __decorate([
    core_1.NgModule({
        imports: [router_1.RouterModule.forRoot(routes)],
        exports: [router_1.RouterModule],
    })
], RoutingModule);
exports.RoutingModule = RoutingModule;
