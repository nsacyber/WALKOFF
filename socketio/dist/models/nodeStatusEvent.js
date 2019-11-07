"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var NodeStatuses;
(function (NodeStatuses) {
    NodeStatuses["AWAITING_DATA"] = "AWAITING_DATA";
    NodeStatuses["EXECUTING"] = "EXECUTING";
    NodeStatuses["SUCCESS"] = "SUCCESS";
    NodeStatuses["FAILURE"] = "FAILURE";
})(NodeStatuses = exports.NodeStatuses || (exports.NodeStatuses = {}));
class NodeStatusEvent {
    get channels() {
        return ['all', this.execution_id, this.node_id];
    }
}
exports.NodeStatusEvent = NodeStatusEvent;
//# sourceMappingURL=nodeStatusEvent.js.map