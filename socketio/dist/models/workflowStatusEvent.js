"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
const class_transformer_1 = require("class-transformer");
class WorkflowStatusEvent {
    get channels() {
        return ['all', this.execution_id, this.workflow_id];
    }
}
__decorate([
    class_transformer_1.Type(() => NodeStatusSummary)
], WorkflowStatusEvent.prototype, "node_status", void 0);
exports.WorkflowStatusEvent = WorkflowStatusEvent;
var WorkflowStatuses;
(function (WorkflowStatuses) {
    WorkflowStatuses["PAUSED"] = "PAUSED";
    WorkflowStatuses["AWAITING_DATA"] = "AWAITING_DATA";
    WorkflowStatuses["PENDING"] = "PENDING";
    WorkflowStatuses["COMPLETED"] = "COMPLETED";
    WorkflowStatuses["ABORTED"] = "ABORTED";
    WorkflowStatuses["EXECUTING"] = "EXECUTING";
})(WorkflowStatuses = exports.WorkflowStatuses || (exports.WorkflowStatuses = {}));
class NodeStatusSummary {
}
exports.NodeStatusSummary = NodeStatusSummary;
//# sourceMappingURL=workflowStatusEvent.js.map