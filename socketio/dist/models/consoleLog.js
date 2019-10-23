"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
class ConsoleLog {
    // action_name: string;
    //
    // app_name: string;
    //
    // workflow: string;
    //
    // level: string;
    toNewConsoleLog() {
        const out = new ConsoleLog();
        out.message = this.message;
        // out.action_name = this.action_name;
        // out.app_name = this.app_name;
        // out.workflow = this.workflow;
        // out.level = this.level;
        return out;
    }
}
exports.ConsoleLog = ConsoleLog;
//# sourceMappingURL=consoleLog.js.map