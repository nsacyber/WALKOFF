import { Component, ViewEncapsulation, Input, Output, OnInit, EventEmitter } from '@angular/core';

import { AppApi } from '../models/api/appApi';
import { ConditionalExpression } from '../models/playbook/conditionalExpression';
import { Workflow } from '../models/playbook/workflow';
import { Argument } from '../models/playbook/argument';

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

	@Output() createVariable = new EventEmitter<Argument>();

	availableOperators: string[];

	// tslint:disable-next-line:no-empty
	constructor() { }

	ngOnInit() {
		this.availableOperators = [ 'and', 'or', 'xor' ];

		if (this.conditionalExpression && !this.conditionalExpression.operator) {
			this.conditionalExpression.operator = 'and';
		}
	}

	/**
	 * Adds a new blank conditional expression to our child expressions array.
	 */
	addChildExpression(): void {
		this.conditionalExpression.child_expressions.push(new ConditionalExpression());
	}

	/**
	 * Moves a selected index in our child expressions array "up" (by swapping it with the ID before).
	 * @param index Index to move
	 */
	moveUp(index: number): void {
		const idAbove = index - 1;
		const toBeSwapped = this.conditionalExpression.child_expressions[idAbove];

		this.conditionalExpression.child_expressions[idAbove] = this.conditionalExpression.child_expressions[index];
		this.conditionalExpression.child_expressions[index] = toBeSwapped;
	}

	/**
	 * Moves a selected index in our child expressions array "down" (by swapping it with the ID after).
	 * @param index Index to move
	 */
	moveDown(index: number): void {
		const idBelow = index + 1;
		const toBeSwapped = this.conditionalExpression.child_expressions[idBelow];

		this.conditionalExpression.child_expressions[idBelow] = this.conditionalExpression.child_expressions[index];
		this.conditionalExpression.child_expressions[index] = toBeSwapped;
	}

	/**
	 * Removes a child expression from our child expressions array by a given index.
	 * @param index Index to remove
	 */
	removeChildExpression(index: number): void {
		this.conditionalExpression.child_expressions.splice(index, 1);
	}

	onCreateVariable(argument: Argument) {
		this.createVariable.emit(argument);
	}

	// This method was used to disable the operator dropdown, but I feel it might confuse users if it's disabled.
	// isOnlyOneChild(): boolean {
	// 	return this.conditionalExpression.conditions.length + this.conditionalExpression.child_expressions.length <= 1;
	// }
}
