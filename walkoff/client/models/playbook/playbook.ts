import { Workflow } from './workflow';

export class Playbook {
	id: number;
	name: string;
	workflows: Workflow[] = [];
}
