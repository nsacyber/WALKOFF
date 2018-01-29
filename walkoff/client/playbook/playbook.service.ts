import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import { Workflow } from '../models/playbook/workflow';
import { Playbook } from '../models/playbook/playbook';
import { AppApi } from '../models/api/appApi';
import { Device } from '../models/device';
import { User } from '../models/user';
import { Role } from '../models/role';

@Injectable()
export class PlaybookService {
	constructor(private authHttp: JwtHttp) { }

	// TODO: should maybe just return all playbooks and not just names?
	getPlaybooks(): Promise<Playbook[]> {
		return this.authHttp.get('/api/playbooks')
			.toPromise()
			.then(this.extractData)
			.then(data => data as Playbook[])
			.catch(this.handleError);
	}

	/**
	 * Saves a new playbook.
	 * @param playbook New playbook to be saved
	 */
	newPlaybook(playbook: Playbook): Promise<Playbook> {
		return this.authHttp.put('/api/playbooks', playbook)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Playbook)
			.catch(this.handleError);
	}

	/**
	 * Renames an existing playbook.
	 * @param playbookId Current playbook ID to change
	 * @param newName New name for the updated playbook
	 */
	renamePlaybook(playbookId: number, newName: string): Promise<Playbook> {
		return this.authHttp.post('/api/playbooks', { id: playbookId, name: newName })
			.toPromise()
			.then(this.extractData)
			.then(data => data as Playbook)
			.catch(this.handleError);
	}

	/**
	 * Duplicates and saves an existing playbook, it's workflows, actions, branches, etc. under a new name.
	 * @param playbookId ID of the playbook to duplicate
	 * @param newName Name of the new copy to be saved
	 */
	duplicatePlaybook(playbookId: number, newName: string): Promise<Playbook> {
		return this.authHttp.post(`/api/playbooks/${playbookId}/copy`, { playbook_name: newName })
			.toPromise()
			.then(this.extractData)
			.then(data => data as Playbook)
			.catch(this.handleError);
	}

	/**
	 * Deletes a playbook by name.
	 * @param playbookIdToDelete ID of playbook to be deleted.
	 */
	deletePlaybook(playbookIdToDelete: number): Promise<void> {
		return this.authHttp.delete(`/api/playbooks/${playbookIdToDelete}`)
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	// /**
	//  * Renames a workflow under a given playbook.
	//  * @param playbookId ID of playbook the workflow exists under
	//  * @param workflowId Current workflow ID to be changed
	//  * @param newName New name for the updated workflow
	//  */
	// renameWorkflow(playbookId: number, workflowId: number, newName: string): Promise<void> {
	// 	return this.authHttp.post(`/api/playbooks/${playbookId}/workflows`, { id: workflowId, name: newName })
	// 		.toPromise()
	// 		.then(this.extractData)
	// 		.catch(this.handleError);
	// }

	/**
	 * Duplicates a workflow under a given playbook, it's actions, branches, etc. under a new name.
	 * @param sourcePlaybookId ID of playbook the workflow exists under
	 * @param sourceWorkflowId Current workflow ID to be duplicated
	 * @param destinationPlaybookId ID of playbook the workflow will be duplicated to
	 * @param newName Name for the new copy to be saved
	 */
	duplicateWorkflow(
		sourcePlaybookId: number, sourceWorkflowId: number, destinationPlaybookId: number, newName: string,
	): Promise<Workflow> {
		return this.authHttp.post(`/api/playbooks/${sourcePlaybookId}/workflows/${sourceWorkflowId}/copy`,
				{ playbook_id: destinationPlaybookId, workflow_name: newName })
			.toPromise()
			.then(this.extractData)
			.then(data => data as Workflow)
			.catch(this.handleError);
	}

	/**
	 * Deletes a given workflow under a given playbook.
	 * @param playbookId ID of the playbook the workflow exists under
	 * @param workflowIdToDelete ID of the workflow to be deleted
	 */
	deleteWorkflow(playbookId: number, workflowIdToDelete: number): Promise<void> {
		return this.authHttp.delete(`/api/playbooks/${playbookId}/workflows/${workflowIdToDelete}`)
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	/**
	 * Creates a new workflow under a given playbook.
	 * @param playbookId ID of the playbook the new workflow should be added under
	 * @param workflow Workflow to be saved
	 */
	newWorkflow(playbookId: number, workflow: Workflow): Promise<Workflow> {
		// let addPlaybookPromise: Promise<any>;
		// if (newPlaybookName) {
		// 	addPlaybookPromise = this.authHttp.put('/api/playbooks', { name: newPlaybookName })
		// 		.toPromise()
		// 		.then(() => { return; });
		// } else {
		// 	addPlaybookPromise = Promise.resolve();
		// }

		return this.authHttp.put(`/api/playbooks/${playbookId}/workflows`, workflow)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Workflow)
			.catch(this.handleError);
	}

	/**
	 * Saves the data of a given workflow specified under a given playbook.
	 * @param playbookId ID of the playbook the workflow exists under
	 * @param workflow Data to be saved under the workflow (actions, etc.)
	 */
	saveWorkflow(playbookId: number, workflow: Workflow): Promise<Workflow> {
		return this.authHttp.post(`/api/playbooks/${playbookId}/workflows`, workflow)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Workflow)
			.catch(this.handleError);
	}

	/**
	 * Loads the data of a given workflow under a given playbook.
	 * @param playbookId ID of playbook the workflow exists under
	 * @param workflowId ID of the workflow to load
	 */
	loadWorkflow(playbookId: number, workflowId: number): Promise<Workflow> {
		return this.authHttp.get(`/api/playbooks/${playbookId}/workflows/${workflowId}`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Workflow)
			.catch(this.handleError);
	}

	/**
	 * Notifies the server to execute a given workflow under a given playbook.
	 * Note that execution results are not returned here, but on a separate stream-actions EventSource.
	 * @param playbookId ID of the playbook the workflow exists under
	 * @param workflowId ID of the workflow to execute
	 */
	executeWorkflow(playbookId: number, workflowId: number): Promise<void> {
		return this.authHttp.post(`/api/playbooks/${playbookId}/workflows/${workflowId}/execute`, {})
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}
	
	/**
	 * Returns an array of all devices within the DB.
	 */
	getDevices(): Promise<Device[]> {
		return this.authHttp.get('/api/devices')
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device[])
			.catch(this.handleError);
	}

	/**
	 * Gets all app apis from the server.
	 */
	getApis(): Promise<AppApi[]> {
		return this.authHttp.get('/api/apps/apis')
			.toPromise()
			.then(this.extractData)
			.then(data => data as AppApi[])
			.catch(this.handleError);
	}

	/**
	 * Returns an array of all users within the DB.
	 */
	getUsers(): Promise<User[]> {
		return this.authHttp.get('/api/users')
			.toPromise()
			.then(this.extractData)
			.then(data => data as User[])
			.catch(this.handleError);
	}

	/**
	 * Returns an array of all roles within the application.
	 */
	getRoles(): Promise<Role[]> {
		return this.authHttp.get('/api/roles')
			.toPromise()
			.then(this.extractData)
			.then(data => data as Role[])
			.catch(this.handleError);
	}

	private extractData(res: Response) {
		const body = res.json();
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
