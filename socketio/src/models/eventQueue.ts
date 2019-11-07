import { WalkoffEvent } from "./walkoffEvent";

export class EventQueue {
    items: WalkoffEvent[] = [];

    constructor(private maxSize = 500) {}

    add(item: WalkoffEvent) {
        this.items.push(item);
        if (this.items.length > this.maxSize)
            this.items = this.items.slice(this.maxSize * -1)
    }

    filter(channel: string) {
        return this.items.filter(item => item.channels.some(c => c == channel));
    }

    get all(): WalkoffEvent[] {
        return this.items;
    }

    get length(): number {
        return this.items.length
    }
}