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
var angular2_jwt_1 = require("angular2-jwt");
var ng_bootstrap_1 = require("@ng-bootstrap/ng-bootstrap");
var ng2_toasty_1 = require("ng2-toasty");
var messages_modal_component_1 = require("../messages/messages.modal.component");
var main_service_1 = require("./main.service");
var auth_service_1 = require("../auth/auth.service");
var utilities_service_1 = require("../utilities.service");
var MAX_READ_MESSAGES = 5;
var MAX_TOTAL_MESSAGES = 20;
var MainComponent = (function () {
    function MainComponent(mainService, authService, modalService, toastyService, toastyConfig) {
        var _this = this;
        this.mainService = mainService;
        this.authService = authService;
        this.modalService = modalService;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.utils = new utilities_service_1.UtilitiesService();
        this.interfaceNames = [];
        this.jwtHelper = new angular2_jwt_1.JwtHelper();
        this.messageListings = [];
        this.newMessagesCount = 0;
        this.notificationRelativeTimes = {};
        this.toastyConfig.theme = 'bootstrap';
        this.mainService.getInterfaceNamess()
            .then(function (interfaceNames) { return _this.interfaceNames = interfaceNames; });
        this.currentUser = this.authService.getAndDecodeAccessToken().user_claims.username;
        this.getInitialNotifications();
        this.getNotificationsSSE();
    }
    MainComponent.prototype.getInitialNotifications = function () {
        var _this = this;
        this.mainService.getInitialNotifications()
            .then(function (messageListings) {
            _this.messageListings = messageListings.concat(_this.messageListings);
            _this._recalculateNewMessagesCount();
        })
            .catch(function (e) { return _this.toastyService.error("Error retrieving notifications: " + e.message); });
    };
    MainComponent.prototype.getNotificationsSSE = function () {
        var _this = this;
        this.authService.getAccessTokenRefreshed()
            .then(function (authToken) {
            var eventSource = new window.EventSource('/api/notifications/stream?access_token=' + authToken);
            eventSource.addEventListener('created', function (message) {
                var newMessage = JSON.parse(message.data);
                var existingMessage = _this.messageListings.find(function (m) { return m.id === newMessage.id; });
                var index = _this.messageListings.indexOf(existingMessage);
                if (index > -1) {
                    _this.messageListings[index] = newMessage;
                }
                else {
                    _this.messageListings.unshift(newMessage);
                }
                if (_this.messageListings.filter(function (m) { return m.is_read; }).length > MAX_READ_MESSAGES ||
                    _this.messageListings.length > MAX_TOTAL_MESSAGES) {
                    _this.messageListings.pop();
                }
                _this._recalculateNewMessagesCount();
                _this.recalculateRelativeTimes();
            });
            eventSource.addEventListener('respond', function (message) {
                var update = JSON.parse(message.data);
                var existingMessage = _this.messageListings.find(function (m) { return m.id === update.id; });
                if (existingMessage) {
                    existingMessage.awaiting_response = false;
                }
            });
            eventSource.addEventListener('error', function (err) {
                console.error(err);
            });
        });
    };
    MainComponent.prototype.logout = function () {
        this.authService.logout()
            .then(function () { return location.href = '/login'; })
            .catch(function (e) { return console.error(e); });
    };
    MainComponent.prototype.openMessage = function (event, messageListing) {
        var _this = this;
        event.preventDefault();
        this.mainService.getMessage(messageListing.id)
            .then(function (message) {
            messageListing.is_read = true;
            messageListing.last_read_at = new Date();
            _this._recalculateNewMessagesCount();
            _this.messageModalRef = _this.modalService.open(messages_modal_component_1.MessagesModalComponent);
            _this.messageModalRef.componentInstance.message = _.cloneDeep(message);
            _this._handleModalClose(_this.messageModalRef);
        })
            .catch(function (e) { return _this.toastyService.error("Error opening message: " + e.message); });
    };
    MainComponent.prototype.recalculateRelativeTimes = function () {
        var _this = this;
        this.messageListings.forEach(function (ml) {
            _this.notificationRelativeTimes[ml.id] = _this.utils.getRelativeLocalTime(ml.created_at);
        });
    };
    MainComponent.prototype._recalculateNewMessagesCount = function () {
        this.newMessagesCount = this.messageListings.filter(function (m) { return !m.is_read; }).length;
    };
    MainComponent.prototype._handleModalClose = function (modalRef) {
        var _this = this;
        modalRef.result
            .then(function (result) { return null; }, function (error) { if (error) {
            _this.toastyService.error(error.message);
        } });
    };
    return MainComponent;
}());
MainComponent = __decorate([
    core_1.Component({
        selector: 'main-component',
        templateUrl: 'client/main/main.html',
        styleUrls: [
            'client/main/main.css',
        ],
        providers: [main_service_1.MainService, auth_service_1.AuthService, utilities_service_1.UtilitiesService],
    }),
    __metadata("design:paramtypes", [main_service_1.MainService, auth_service_1.AuthService,
        ng_bootstrap_1.NgbModal, ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig])
], MainComponent);
exports.MainComponent = MainComponent;
