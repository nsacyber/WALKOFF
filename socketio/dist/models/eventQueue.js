"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
class EventQueue {
    constructor(maxSize = 1000) {
        this.maxSize = maxSize;
        this.items = [];
    }
    add(item) {
        this.items.push(item);
        if (this.items.length > this.maxSize)
            this.items = this.items.slice(this.maxSize * -1);
    }
    filter(channel) {
        return this.items.filter(item => item.channels.some(c => c == channel));
    }
    get all() {
        return this.items;
    }
    get length() {
        return this.items.length;
    }
}
exports.EventQueue = EventQueue;
//# sourceMappingURL=eventQueue.js.map