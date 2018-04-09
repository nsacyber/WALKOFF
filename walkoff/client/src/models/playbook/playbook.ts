import { Type } from 'class-transformer';

import { Workflow } from './workflow';
import { ExecutionElement } from './executionElement';

export class Playbook extends ExecutionElement {
	name: string;

	@Type(() => Workflow)
	workflows: Workflow[] = [];

	get all_errors(): string[] {
		return this.errors.concat(...this.workflows.map(workflow => workflow.all_errors))
	}
}
