import { Workflow } from './workflow';

export class Playbook {
	uid: string;
	name: string;
	workflows: Workflow[] = [];
}
