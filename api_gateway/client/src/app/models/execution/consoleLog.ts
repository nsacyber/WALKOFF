export class ConsoleLog {
	message: string;

	// action_name: string;
  //
	// app_name: string;
  //
	// workflow: string;
  //
	// level: string;

	toNewConsoleLog(): ConsoleLog {
		const out = new ConsoleLog();

		out.message = this.message;
		// out.action_name = this.action_name;
		// out.app_name = this.app_name;
		// out.workflow = this.workflow;
		// out.level = this.level;

		return out;
	}
}
