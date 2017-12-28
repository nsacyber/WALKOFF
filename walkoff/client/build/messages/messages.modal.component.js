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
var ng_bootstrap_1 = require("@ng-bootstrap/ng-bootstrap");
var ng2_toasty_1 = require("ng2-toasty");
var moment = require("moment");
var messages_service_1 = require("./messages.service");
var message_1 = require("../models/message/message");
var MessagesModalComponent = (function () {
    function MessagesModalComponent(messagesService, activeModal, toastyService, toastyConfig) {
        this.messagesService = messagesService;
        this.activeModal = activeModal;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.toastyConfig.theme = 'bootstrap';
    }
    MessagesModalComponent.prototype.performMessageAction = function (action) {
        var _this = this;
        this.messagesService.performMessageAction(this.message.workflow_execution_uid, action)
            .then(function () {
            _this.message.awaiting_response = false;
            _this.message.responded_at = new Date();
        })
            .catch(function (e) { return _this.toastyService.error("Error performing " + action + " on message: " + e.message); });
    };
    MessagesModalComponent.prototype.dismiss = function () {
        this.activeModal.dismiss();
    };
    MessagesModalComponent.prototype.getRelativeTime = function (time) {
        return moment(time).fromNow();
    };
    return MessagesModalComponent;
}());
__decorate([
    core_1.Input(),
    __metadata("design:type", message_1.Message)
], MessagesModalComponent.prototype, "message", void 0);
MessagesModalComponent = __decorate([
    core_1.Component({
        selector: 'messages-modal',
        templateUrl: 'client/messages/messages.modal.html',
        styleUrls: [
            'client/messages/messages.css',
        ],
        providers: [messages_service_1.MessagesService],
    }),
    __metadata("design:paramtypes", [messages_service_1.MessagesService, ng_bootstrap_1.NgbActiveModal,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig])
], MessagesModalComponent);
exports.MessagesModalComponent = MessagesModalComponent;
