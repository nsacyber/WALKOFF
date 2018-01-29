import { Workflow } from './workflow';
import { ExecutionElement } from './executionElement';

export class Playbook extends ExecutionElement {
	id: number;
	name: string;
	workflows: Workflow[] = [];
}
