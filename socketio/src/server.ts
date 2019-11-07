import * as express from "express";
import * as socketio from "socket.io";
import * as path from "path";

import "reflect-metadata";
import { plainToClassFromExist } from 'class-transformer';
import { EventQueue } from "./models/eventQueue";
import { ConsoleEvent } from "./models/consoleEvent";
import { NodeStatusEvent } from "./models/nodeStatusEvent";
import { BuildStatusEvent } from "./models/buildStatusEvent";
import { WorkflowStatusEvent } from "./models/workflowStatusEvent";
import { WalkoffEvent } from "./models/walkoffEvent";


const app = express();
app.set("port", process.env.PORT || 3000);
app.get("/", (req: any, res: any) => res.sendFile(path.resolve("./client/index.html")));

const http = require("http").Server(app);
const io = socketio(http, { path: '/walkoff/sockets/socket.io' });
const server = http.listen(3000, () => console.log("listening on *:3000"));

// whenever a user connects on port 3000 via a websocket, log that a user has connected
io.on("connection", (socket: any) => console.log("a user connected"));

createSpace('/console', () => new ConsoleEvent);
createSpace('/workflowStatus', () => new WorkflowStatusEvent)
createSpace('/nodeStatus', () => new NodeStatusEvent)
createSpace('/buildStatus', () => new BuildStatusEvent)

function createSpace(url: string, getEventClass: () => WalkoffEvent) {
    const queue = new EventQueue();
    const space = io.of(url);

    space.on('connect', function(client: socketio.Socket) {
        const channel = (client.handshake.query.channel) ? client.handshake.query.channel : 'all';
        console.log(client.id + ' joining ' + channel)
        client.join(channel);

        client.emit('connected', queue.filter(channel))
        client.on('log', (data: any) => {
            const item = plainToClassFromExist(getEventClass(), data);
            item.channels.forEach((c: string) => client.broadcast.to(c).emit('log', item))
            queue.add(item);
            console.log(item)
        });
    })
}
