import { Injectable } from '@angular/core';
import { Http, Response, Headers } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import { Workflow } from '../models/playbook/workflow';
import { Playbook } from '../models/playbook/playbook';
import { App } from '../models/api/app';
import { ActionApi } from '../models/api/actionApi';
import { ConditionApi } from '../models/api/conditionApi';
import { TransformApi } from '../models/api/transformApi';
import { Device } from '../models/device';

@Injectable()
export class PlaybookService {
	constructor(private authHttp: JwtHttp) { }

	// TODO: should maybe just return all playbooks and not just names?
	getPlaybooks(): Promise<Playbook[]> {
		return this.authHttp.get(`/api/playbooks`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Playbook[])
			.catch(this.handleError);
	}

	/**
	 * Renames an existing playbook.
	 * @param oldName Current playbook name to change
	 * @param newName New name for the updated playbook
	 */
	renamePlaybook(oldName: string, newName: string): Promise<void> {
		return this.authHttp.post(`/api/playbooks/${oldName}`, { new_name: newName })
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	/**
	 * Duplicates and saves an existing playbook, it's workflows, steps, next steps, etc. under a new name.
	 * @param oldName Name of the playbook to duplicate
	 * @param newName Name of the new copy to be saved
	 */
	duplicatePlaybook(oldName: string, newName: string): Promise<void> {
		return this.authHttp.post(`/api/playbooks/${oldName}/copy`, { playbook: newName })
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	/**
	 * Deletes a playbook by name.
	 * @param playbookToDelete Name of playbook to be deleted.
	 */
	deletePlaybook(playbookToDelete: string): Promise<void> {
		return this.authHttp.delete(`/api/playbooks/${playbookToDelete}`)
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	/**
	 * Renames a workflow under a given playbook.
	 * @param playbook Name of playbook the workflow exists under
	 * @param oldName Current workflow name to be changed
	 * @param newName New name for the updated workflow
	 */
	renameWorkflow(playbook: string, oldName: string, newName: string): Promise<void> {
		return this.authHttp.post(`/api/playbooks/${playbook}/workflows/${oldName}`, { new_name: newName })
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	/**
	 * Duplicates a workflow under a given playbook, its steps, next steps, etc. under a new name.
	 * @param playbook Name of playbook the workflow exists under
	 * @param oldName Current workflow name to be duplicated
	 * @param newName Name for the new copy to be saved
	 */
	// TODO: probably don't need playbook in body, verify on server
	duplicateWorkflow(playbook: string, oldName: string, newName: string): Promise<Workflow> {
		return this.authHttp.post(`/api/playbooks/${playbook}/workflows/${oldName}/copy`, { playbook: playbook, workflow: newName })
			.toPromise()
			.then(this.extractData)
			.then(data => data as Workflow)
			.catch(this.handleError);
	}

	/**
	 * Deletes a given workflow under a given playbook.
	 * @param playbook Name of the playbook the workflow exists under
	 * @param workflowToDelete Name of the workflow to be deleted
	 */
	deleteWorkflow(playbook: string, workflowToDelete: string): Promise<void> {
		return this.authHttp.delete(`/api/playbooks/${playbook}/workflows/${workflowToDelete}`)
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	/**
	 * Creates a new blank workflow under a given playbook.
	 * @param playbook Name of the playbook the new workflow should be added under
	 * @param workflow Name of the new workflow to be saved
	 */
	newWorkflow(playbook: string, workflow: string): Promise<Workflow> {
		return this.authHttp.put(`/api/playbooks/${playbook}/workflows`, { name: workflow })
			.toPromise()
			.then(this.extractData)
			.then(data => data as Workflow)
			.catch(this.handleError);
	}

	/**
	 * Saves the data of a given workflow specified under a given playbook.
	 * @param playbookName Name of the playbook the workflow exists under
	 * @param workflowName Name of the workflow to be saved
	 * @param workflow Data to be saved under the workflow (steps, etc.)
	 */
	saveWorkflow(playbookName: string, workflowName: string, workflow: Workflow): Promise<void> {
		return this.authHttp.post(`/api/playbooks/${playbookName}/workflows/${workflowName}/save`, workflow)
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	/**
	 * Loads the data of a given workflow under a given playbook.
	 * @param playbook Name of playbook the workflow exists under
	 * @param workflow Name of the workflow to load
	 */
	loadWorkflow(playbook: string, workflow: string): Promise<Workflow> {
		return this.authHttp.get(`/api/playbooks/${playbook}/workflows/${workflow}`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Workflow)
			.catch(this.handleError);
	}

	/**
	 * Notifies the server to execute a given workflow under a given playbook. Note that execution results are not returned here, but on a separate stream-steps EventSource.
	 * @param playbook Name of the playbook the workflow exists under
	 * @param workflow Name of the workflow to execute
	 */
	executeWorkflow(playbook: string, workflow: string): Promise<void> {
		return this.authHttp.post(`/api/playbooks/${playbook}/workflows/${workflow}/execute`, {})
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}
	
	/**
	 * Returns an array of all devices within the DB.
	 */
	getDevices(): Promise<Device[]> {
		return this.authHttp.get(`/api/devices`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device[])
			.catch(this.handleError);
	}

	// TODO: not actually used and doesn't currently exist in the backend; should replace the actions/conditions/triggers calls with this...
	getApis(): Promise<App[]> {
		return this.authHttp.get(`/api/apps/apis`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as App[])
			.catch(this.handleError);
	}

	/**
	 * Returns an object with actions listed by app. Of form { app_name -> { action_name: {} } }.
	 */
	getAppsAndActions(): Promise<App[]> {
		return this.authHttp.get(`/api/apps/actions`)
			.toPromise()
			.then(this.extractData)
			// TODO: should remove this step once the backend gives the data in this form
			.then(a => {
				let apps: App[] = _.map(a, function (app: { [key: string] : ActionApi }, appName: string) {
					return <App>{ name: appName, actionApis: _.map(app, function (action: ActionApi, actionName: string) {
						action.name = actionName;

						return action;
					})};
				})

				apps.filter(a => a.actionApis.length);

				return apps;
			})
			.catch(this.handleError);
	}

	/**
	 * Returns an array of all next step conditions specified within the application and its apps.
	 */
	getConditions(): Promise<App[]> {
		return this.authHttp.get(`/api/conditions`)
			.toPromise()
			.then(this.extractData)
			// TODO: should remove this step once the backend gives the data in this form
			.then(a => {
				let apps: App[] = _.map(a, function (app: { [key: string] : ActionApi }, appName: string) {
					return <App>{ name: appName, conditionApis: _.map(app, function (condition: ConditionApi, conditionName: string) {
						condition.name = conditionName;

						return condition;
					})};
				})

				apps.filter(a => a.conditionApis.length);

				return apps;
			})
			.catch(this.handleError);
	}

	/**
	 * Returns an array of all data transforms specified within the application and its apps.
	 */
	getTransforms(): Promise<App[]> {
		return this.authHttp.get(`/api/transforms`)
			.toPromise()
			.then(this.extractData)
			// TODO: should remove this step once the backend gives the data in this form
			.then(a => {
				let apps: App[] = _.map(a, function (app: { [key: string] : ActionApi }, appName: string) {
					return <App>{ name: appName, transformApis: _.map(app, function (transform: TransformApi, transformName: string) {
						transform.name = transformName;

						return transform;
					})};
				})

				apps.filter(a => a.transformApis.length);

				return apps;
			})
			.catch(this.handleError);
	}

	private extractData(res: Response) {
		let body = res.json();
		return body || {};
	}

	private handleError(error: Response | any): Promise<any> {
		let errMsg: string;
		let err: string;
		if (error instanceof Response) {
			const body = error.json() || '';
			err = body.error || body.detail || JSON.stringify(body);
			errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
		} else {
			err = errMsg = error.message ? error.message : error.toString();
		}
		console.error(errMsg);
		throw new Error(err);
	}
}