import { Step } from './step';

export class Workflow {
	name: string;
	steps: Step[] = [];
	start: string;
	accumulated_risk: number;
}