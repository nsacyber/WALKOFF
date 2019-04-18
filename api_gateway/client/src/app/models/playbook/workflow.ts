import { Type, Expose } from 'class-transformer';
import { Select2OptionData } from 'ng2-select2/ng2-select2';

import { Action } from './action';
import { Branch } from './branch';
import { ExecutionElement } from './executionElement';
import { EnvironmentVariable } from './environmentVariable';
import { ConditionalExpression } from './conditionalExpression';
import { Argument } from './argument';

export class Workflow extends ExecutionElement {
	// _playbook_id: number;
	/**
	 * Playbook ID this workflow resides under. Only used on create/duplicate.
	 */
	playbook_id?: string;

	/**
	 * Name of the workflow. Updated by passing in new_name in POST.
	 */
	name: string;

	/**
	 * Name of the workflow. Updated by passing in new_name in POST.
	 */
	description: string;

	/**
	 * Name of the workflow. Updated by passing in new_name in POST.
	 */
	tags: string[] = [];

	/**
	 * Array of actions specified in the workflow.
	 */
	@Type(() => Action)
	actions?: Action[] = [];

	/**
	 * Array of branches between actions.
	 */
	@Type(() => Branch)
	branches?: Branch[] = [];

	/**
	 * Array of environment variables.
	 */
	@Type(() => EnvironmentVariable)
	@Expose({name: 'workflow_variables'})
	environment_variables?: EnvironmentVariable[] = [];

	/**
	 * ID of the action designated as the start action.
	 */
	start?: string;
	
	/**
	 * A factor of how often the workflow fails.
	 */
	accumulated_risk?: number;

	/**
	 * Returns true if this workflow doesn't contain any errors
	 */
	is_valid: boolean;

	/**
	 * Array of errors returned from the server for this Argument and any of its descendants 
	 */
	get all_errors(): string[] {
		return this.errors
				   .concat(...this.actions.map(action => action.all_errors))
				   .concat(...this.branches.map(branch => branch.all_errors))
	}

	get all_arguments(): Argument[] {
		let allArgs: Argument[] = [];
		const getExpressionArguments = (expression: ConditionalExpression) => {
			expression.conditions.forEach(condition => {
				allArgs = allArgs.concat(condition.arguments);
				condition.transforms.forEach(transform => allArgs = allArgs.concat(transform.arguments));
			})
			expression.child_expressions.forEach(getExpressionArguments);
		}

		this.actions.forEach(action => {
			allArgs = allArgs.concat(action.arguments);
			if (action.trigger) getExpressionArguments(action.trigger);
		})
		this.branches.forEach(branch => {
			if (branch.condition) getExpressionArguments(branch.condition);
		})

		return allArgs;
	}

	get referenced_variables() : EnvironmentVariable[] {
		if (!this.environment_variables) return [];
		return this.environment_variables.filter(variable => this.all_arguments.some(arg => arg.reference == variable.id));
	}

	listBranchCounters() : Select2OptionData[] {
		return this.branches.map(branch  => {
			const sourceAction = this.findActionById(branch.source_id);
			const destAction = this.findActionById(branch.destination_id);
			return { id: branch.id, text: `${ (sourceAction || { name: null}).name } > ${ (destAction || { name: null}).name }` }
		})
	}

	findActionById(id: string) : Action {
		return this.actions.find(action => action.id == id)
	}

	deleteVariable(deletedVariable: EnvironmentVariable) {
		this.environment_variables = this.environment_variables.filter(variable => variable.id !== deletedVariable.id);
		this.all_arguments
			.filter(arg => arg.value == deletedVariable.id)
			.forEach(arg => arg.value = '');
	}

	getNextActionName(actionName: string) : string {
		let numActions = this.actions.filter(a => a.action_name === actionName && a.name).length;
		return numActions ? `${actionName} ${ ++numActions }` : actionName;
	}

	getPreviousActions(action: Action) : Action[] {
		return this.branches
			.filter(b => b.destination_id == action.id)
			.map(b => this.actions.find(a => a.id == b.source_id))
			.reduce((previous, action) => $.unique(previous.concat([action], this.getPreviousActions(action))), []);
	}
}
