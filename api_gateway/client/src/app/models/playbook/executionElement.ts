export class ExecutionElement {
	id: string;
	errors: string[] = [];

	get all_errors(): string[] {
		return this.errors;
	}
	
	get has_errors(): boolean {
		return (this.all_errors.length > 0) ? true : false;
	}
}
