import { Type, Expose, Exclude, classToClass } from 'class-transformer';
import { UUID } from 'angular2-uuid';

export class ExecutionElement {

	@Expose({ name: "id_" })
	id: string;

	@Exclude({ toPlainOnly: true })
	errors: string[] = [];

	constructor() {
		//this.id = UUID.UUID()
	}

	get all_errors(): string[] {
		return this.errors;
	}
	
	get has_errors(): boolean {
		return (this.all_errors.length > 0) ? true : false;
	}

	clone() {
		return classToClass(this, { ignoreDecorators: true });
	}
}
