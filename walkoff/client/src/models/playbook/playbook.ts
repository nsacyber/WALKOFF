import { Workflow } from './workflow';
import { ExecutionElement } from './executionElement';

export class Playbook extends ExecutionElement {
	name: string;
	workflows: Workflow[] = [];
}
