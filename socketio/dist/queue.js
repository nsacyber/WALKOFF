"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const consoleEvent_1 = require("./models/consoleEvent");
const nodeStatusEvent_1 = require("./models/nodeStatusEvent");
const workflowStatusEvent_1 = require("./models/workflowStatusEvent");
class EventQueue {
    constructor(size = 100) {
        this.size = size;
    }
    add(item) {
        this.items.push(item);
        if (this.items.length > this.size)
            this.items = this.items.slice(this.size * -1);
    }
    filter(id) {
        if (id == 'all')
            return this.items;
        return this.items.filter((item) => {
            if (item instanceof consoleEvent_1.ConsoleEvent)
                return item.execution_id == id;
            if (item instanceof nodeStatusEvent_1.NodeStatusEvent)
                return item.node_id == id || item.execution_id == id;
            if (item instanceof workflowStatusEvent_1.WorkflowStatusEvent)
                return item.workflow_id == id || item.execution_id == id;
        });
    }
}
exports.EventQueue = EventQueue;
//# sourceMappingURL=queue.js.map