"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
var core_1 = require("@angular/core");
var moment = require("moment");
var UtilitiesService = (function () {
    function UtilitiesService() {
    }
    UtilitiesService.prototype.getTruncatedString = function (input, length, def) {
        input = this.getDefaultString(input, def);
        if (input.length <= length) {
            return input;
        }
        return input.substr(0, length) + '...';
    };
    UtilitiesService.prototype.getDefaultString = function (input, def) {
        if (!input) {
            input = '';
        }
        var trimmed = input.trim();
        if (!trimmed) {
            if (def) {
                return def;
            }
            return '';
        }
        return trimmed;
    };
    UtilitiesService.prototype.getLocalTime = function (time) {
        return moment.utc(time).local().toLocaleString();
    };
    UtilitiesService.prototype.getRelativeLocalTime = function (time) {
        return moment.utc(time).local().fromNow();
    };
    return UtilitiesService;
}());
UtilitiesService = __decorate([
    core_1.Injectable()
], UtilitiesService);
exports.UtilitiesService = UtilitiesService;
