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
	@Input() selectedAppName: string;
	@Input() conditionalExpression: ConditionalExpression;
	@Input() appApis: AppApi[];
	@Input() loadedWorkflow: Workflow;

	availableOperators: string[];

	// tslint:disable-next-line:no-empty
	constructor() { }

	ngOnInit() {
		this.availableOperators = [ 'and', 'or', 'xor' ];

		if (this.conditionalExpression && !this.conditionalExpression.operator) {
			this.conditionalExpression.operator = 'and';
		}
	}

	addChildExpression(): void {
		this.conditionalExpression.child_expressions.push(new ConditionalExpression());
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
