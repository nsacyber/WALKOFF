import { Type } from 'class-transformer';

import { Workflow } from './workflow';
import { ExecutionElement } from './executionElement';

export class Playbook extends ExecutionElement {
	name: string;

	@Type(() => Workflow)
	workflows: Workflow[] = [];
}
