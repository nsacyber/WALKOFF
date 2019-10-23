"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express = require("express");
const socketio = require("socket.io");
const path = require("path");
require("reflect-metadata");
const class_transformer_1 = require("class-transformer");
const eventQueue_1 = require("./models/eventQueue");
const consoleEvent_1 = require("./models/consoleEvent");
const nodeStatusEvent_1 = require("./models/nodeStatusEvent");
const workflowStatusEvent_1 = require("./models/workflowStatusEvent");
const app = express();
app.set("port", process.env.PORT || 3000);
app.get("/", (req, res) => res.sendFile(path.resolve("./client/index.html")));
const http = require("http").Server(app);
const io = socketio(http);
const server = http.listen(3000, () => console.log("listening on *:3000"));
// whenever a user connects on port 3000 via a websocket, log that a user has connected
io.on("connection", (socket) => console.log("a user connected"));
createSpace('/console', new consoleEvent_1.ConsoleEvent);
createSpace('/workflowStatus', new workflowStatusEvent_1.WorkflowStatusEvent);
createSpace('/nodeStatus', new nodeStatusEvent_1.NodeStatusEvent);
function createSpace(url, eventClass) {
    const queue = new eventQueue_1.EventQueue();
    const space = io.of(url);
    space.on('connection', function (client) {
        const channel = (client.handshake.query.channel) ? client.handshake.query.channel : 'all';
        console.log(client.id + ' joining ' + channel);
        client.join(channel);
        client.emit('connected', queue.filter(channel));
        client.on('log', (data) => {
            const item = class_transformer_1.plainToClassFromExist(eventClass, data);
            queue.add(item);
            item.channels.forEach((c) => client.broadcast.to(c).emit('log', item));
            space.emit('log', item);
        });
    });
}
// let count = 0;
// function newConsoleEvent() : ConsoleEvent {
//     return plainToClass(ConsoleEvent, {
//         execution_id: Math.floor(count / 5),
// 	    //workflow_id: Math.floor(count / 10),
// 	    //node_id: count,
// 	    message: `Message Count: ${++count}`
//     });
// }
//# sourceMappingURL=server.js.map