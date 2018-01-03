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
var forms_1 = require("@angular/forms");
var ng2_toasty_1 = require("ng2-toasty");
var ng_bootstrap_1 = require("@ng-bootstrap/ng-bootstrap");
var moment = require("moment");
var messages_service_1 = require("./messages.service");
var utilities_service_1 = require("../utilities.service");
var messages_modal_component_1 = require("./messages.modal.component");
var MessagesComponent = (function () {
    function MessagesComponent(messagesService, modalService, toastyService, toastyConfig) {
        var _this = this;
        this.messagesService = messagesService;
        this.modalService = modalService;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.utils = new utilities_service_1.UtilitiesService();
        this.messages = [];
        this.displayMessages = [];
        this.filterQuery = new forms_1.FormControl();
        this.selectMapping = {};
        this.messageRelativeTimes = {};
        this.toastyConfig.theme = 'bootstrap';
        this.listMessages();
        this.filterQuery
            .valueChanges
            .debounceTime(500)
            .subscribe(function (event) { return _this.filterMessages(); });
    }
    MessagesComponent.prototype.filterMessages = function () {
        var _this = this;
        var searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';
        this.displayMessages = this.messages.filter(function (message) {
            _this.messageRelativeTimes[message.id] = _this.utils.getRelativeLocalTime(message.created_at);
            return (message.subject.toLocaleLowerCase().includes(searchFilter));
        });
    };
    MessagesComponent.prototype.listMessages = function () {
        var _this = this;
        this.messagesService.listMessages()
            .then(function (messages) {
            _this.messages = messages;
            _this.filterMessages();
        })
            .catch(function (e) { return _this.toastyService.error("Error retrieving messages: " + e.message); });
    };
    MessagesComponent.prototype.openMessage = function (event, messageListing) {
        var _this = this;
        event.preventDefault();
        this.messagesService.getMessage(messageListing.id)
            .then(function (message) {
            messageListing.is_read = true;
            messageListing.last_read_at = new Date();
            var modalRef = _this.modalService.open(messages_modal_component_1.MessagesModalComponent);
            modalRef.componentInstance.message = _.cloneDeep(message);
            _this._handleModalClose(modalRef);
        })
            .catch(function (e) { return _this.toastyService.error("Error opening message: " + e.message); });
    };
    MessagesComponent.prototype.deleteSelected = function () {
        var _this = this;
        var idsToDelete = this._getSelectedIds();
        if (!confirm("Are you sure you want to delete " + idsToDelete.length + " messages?")) {
            return;
        }
        this.messagesService.deleteMessages(idsToDelete)
            .then(function () {
            _this.messages = _this.messages.filter(function (message) { return idsToDelete.indexOf(message.id) === -1; });
            idsToDelete.forEach(function (id) {
                _this.selectMapping[id] = false;
            });
            _this.filterMessages();
        })
            .catch(function (e) { return _this.toastyService.error("Error deleting messages: " + e.message); });
    };
    MessagesComponent.prototype.markSelectedAsRead = function () {
        var _this = this;
        var idsToRead = this._getSelectedIds();
        this.messagesService.readMessages(idsToRead)
            .then(function () {
            _this.messages.forEach(function (message) {
                if (idsToRead.indexOf(message.id) !== -1) {
                    message.is_read = true;
                    message.last_read_at = new Date();
                }
            });
        })
            .catch(function (e) { return _this.toastyService.error("Error marking messages as read: " + e.message); });
    };
    MessagesComponent.prototype.markSelectedAsUnread = function () {
        var _this = this;
        var idsToUnread = this._getSelectedIds();
        this.messagesService.unreadMessages(idsToUnread)
            .then(function () {
            _this.messages.forEach(function (message) {
                if (idsToUnread.indexOf(message.id) !== -1) {
                    message.is_read = false;
                    message.last_read_at = null;
                }
            });
        })
            .catch(function (e) { return _this.toastyService.error("Error marking messages as unread: " + e.message); });
    };
    MessagesComponent.prototype.getFriendlyTime = function (createdAt) {
        return moment(createdAt).fromNow();
    };
    MessagesComponent.prototype._getSelectedIds = function () {
        var _this = this;
        var ids = [];
        Object.keys(this.selectMapping).forEach(function (id) {
            if (_this.selectMapping[id]) {
                ids.push(+id);
            }
        });
        return ids;
    };
    MessagesComponent.prototype._handleModalClose = function (modalRef) {
        var _this = this;
        modalRef.result
            .then(function (result) { return null; }, function (error) { if (error) {
            _this.toastyService.error(error.message);
        } });
    };
    return MessagesComponent;
}());
MessagesComponent = __decorate([
    core_1.Component({
        selector: 'messages-component',
        templateUrl: 'client/messages/messages.html',
        styleUrls: [
            'client/messages/messages.css',
        ],
        providers: [messages_service_1.MessagesService],
    }),
    __metadata("design:paramtypes", [messages_service_1.MessagesService, ng_bootstrap_1.NgbModal,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig])
], MessagesComponent);
exports.MessagesComponent = MessagesComponent;
