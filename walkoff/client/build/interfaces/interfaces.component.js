"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
Object.defineProperty(exports, "__esModule", { value: true });
var core_1 = require("@angular/core");
var router_1 = require("@angular/router");
var ng2_toasty_1 = require("ng2-toasty");
var auth_service_1 = require("../auth/auth.service");
var InterfacesComponent = (function () {
    function InterfacesComponent(route, authService, toastyService, toastyConfig) {
        this.route = route;
        this.authService = authService;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.toastyConfig.theme = 'bootstrap';
    }
    InterfacesComponent.prototype.ngOnInit = function () {
        var _this = this;
        this.paramsSub = this.route.params.subscribe(function (params) {
            _this.interfaceName = params.interfaceName;
            _this.getInterface();
        });
    };
    InterfacesComponent.prototype.getInterface = function () {
        var _this = this;
        var self = this;
        this.authService.getAccessTokenRefreshed()
            .then(function (authToken) {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', "custominterfaces/" + _this.interfaceName + "/", true);
            xhr.onreadystatechange = function () {
                if (this.readyState !== 4) {
                    return;
                }
                if (this.status !== 200) {
                    return;
                }
                self.main.nativeElement.removeChild(self.main.nativeElement.lastChild);
                self.activeIFrame = document.createElement('iframe');
                self.activeIFrame.srcdoc = this.responseText;
                self.activeIFrame.src = 'data:text/html;charset=utf-8,' + this.responseText;
                self.main.nativeElement.appendChild(self.activeIFrame);
            };
            xhr.setRequestHeader('Authorization', 'Bearer ' + authToken);
            xhr.send();
        })
            .catch(function (e) { return _this.toastyService.error("Error retrieving interface: " + e.message); });
    };
    return InterfacesComponent;
}());
__decorate([
    core_1.ViewChild('interfacesMain'),
    __metadata("design:type", core_1.ElementRef)
], InterfacesComponent.prototype, "main", void 0);
InterfacesComponent = __decorate([
    core_1.Component({
        selector: 'interfaces-component',
        templateUrl: 'client/interfaces/interfaces.html',
        styleUrls: ['client/interfaces/interfaces.css'],
        encapsulation: core_1.ViewEncapsulation.None,
        providers: [auth_service_1.AuthService],
    }),
    __metadata("design:paramtypes", [router_1.ActivatedRoute, auth_service_1.AuthService,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig])
], InterfacesComponent);
exports.InterfacesComponent = InterfacesComponent;
