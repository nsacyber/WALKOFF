import { Component, ViewEncapsulation, Input, OnInit } from '@angular/core';

import { AppApi } from '../models/api/appApi';
import { ConditionalExpression } from '../models/playbook/conditionalExpression';
import { Workflow } from '../models/playbook/workflow';

@Component({
	selector: 'playbook-conditional-expression-component',
	templateUrl: './playbook.conditional.expression.html',
	styleUrls: [],
	encapsulation: ViewEncapsulation.None,
	providers: [],
})
export class PlaybookConditionalExpressionComponent implements OnInit {
	@Input() id?: number;
	@Input() selectedAppName: string;
	@Input() conditionalExpression: ConditionalExpression;
	@Input() appApis: AppApi[];
	@Input() loadedWorkflow: Workflow;

	availableOperators: string[];
	selectedOperator: string;

	// tslint:disable-next-line:no-empty
	constructor() { }

	ngOnInit() {
		this.availableOperators = [ 'AND', 'OR', 'XOR' ];

		if (this.conditionalExpression && !this.conditionalExpression.operator) {
			this.conditionalExpression.operator = 'AND';
		}
	}

	addChildExpression(): void {
		if (!this.selectedOperator) { return; }

		const newConditionalExpression = new ConditionalExpression();

		this.conditionalExpression.child_expressions.push(newConditionalExpression);
	}

	moveUp(index: number): void {
		const idAbove = index - 1;
		const toBeSwapped = this.conditionalExpression.child_expressions[idAbove];

		this.conditionalExpression.child_expressions[idAbove] = this.conditionalExpression.child_expressions[index];
		this.conditionalExpression.child_expressions[index] = toBeSwapped;
	}

	moveDown(index: number): void {
		const idBelow = index + 1;
		const toBeSwapped = this.conditionalExpression.child_expressions[idBelow];

		this.conditionalExpression.child_expressions[idBelow] = this.conditionalExpression.child_expressions[index];
		this.conditionalExpression.child_expressions[index] = toBeSwapped;
	}

	removeChildExpression(index: number): void {
		this.conditionalExpression.child_expressions.splice(index, 1);
	}

	isOnlyOneChild(): boolean {
		return this.conditionalExpression.conditions.length + this.conditionalExpression.child_expressions.length <= 1;
	}
}
