import { Injectable } from '@angular/core';
import { plainToClass, classToPlain } from 'class-transformer';
import { HttpClient } from '@angular/common/http';

import { Workflow } from '../models/playbook/workflow';
import { Playbook } from '../models/playbook/playbook';
import { AppApi } from '../models/api/appApi';
import { Device } from '../models/device';
import { User } from '../models/user';
import { Role } from '../models/role';
import { WorkflowStatus } from '../models/execution/workflowStatus';

import { DevicesService } from '../devices/devices.service';
import { ExecutionService } from '../execution/execution.service';
import { SettingsService } from '../settings/settings.service';
import { UtilitiesService } from '../utilities.service';

import { Observable } from 'rxjs/Observable';
import 'rxjs/add/operator/catch';
import 'rxjs/add/operator/map';

@Injectable({
	providedIn: 'root'
})
export class PlaybookService {
	constructor(private http: HttpClient, private utils: UtilitiesService, private executionService: ExecutionService,
				private devicesService: DevicesService, private settingsService: SettingsService) {}

	/**
	 * Returns all playbooks and their child workflows in minimal form (id, name).
	 */
	getPlaybooks(): Promise<Playbook[]> {
		return this.http.get('/api/playbooks')
			.toPromise()
			.then((data) => plainToClass(Playbook, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Saves a new playbook.
	 * @param playbook New playbook to be saved
	 */
	newPlaybook(playbook: Playbook): Promise<Playbook> {
		return this.http.post('/api/playbooks', classToPlain(playbook))
			.toPromise()
			.then((data) => plainToClass(Playbook, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Renames an existing playbook.
	 * @param playbookId Current playbook ID to change
	 * @param newName New name for the updated playbook
	 */
	renamePlaybook(playbookId: string, newName: string): Promise<Playbook> {
		return this.http.patch('/api/playbooks', { id: playbookId, name: newName })
			.toPromise()
			.then((data: object) => plainToClass(Playbook, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Duplicates and saves an existing playbook, it's workflows, actions, branches, etc. under a new name.
	 * @param playbookId ID of the playbook to duplicate
	 * @param newName Name of the new copy to be saved
	 */
	duplicatePlaybook(playbookId: string, newName: string): Promise<Playbook> {
		return this.http.post(`/api/playbooks?source=${playbookId}`, { name: newName })
			.toPromise()
			.then((data) => plainToClass(Playbook, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Deletes a playbook by name.
	 * @param playbookIdToDelete ID of playbook to be deleted.
	 */
	deletePlaybook(playbookIdToDelete: string): Promise<void> {
		return this.http.delete(`/api/playbooks/${playbookIdToDelete}`)
			.toPromise()
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Exports a playbook as an Observable (component handles the actual 'save').
	 * @param playbookId: ID of playbook to export
	 */
	exportPlaybook(playbookId: string): Observable<Blob> {
		return this.http.get(`/api/playbooks/${playbookId}?mode=export`, { responseType: 'blob' })
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Imports a playbook from a supplied file.
	 * @param fileToImport File to be imported
	 */
	importPlaybook(fileToImport: File): Observable<Playbook> {
		const formData: FormData = new FormData();
		formData.append('file', fileToImport, fileToImport.name);

		const headers = { 'Accept': 'application/json' }

		return this.http.post('/api/playbooks', formData, { headers })
			.map(res => plainToClass(Playbook, res))
			.catch(error => Observable.throw(error));
	}

	/**
	 * Duplicates a workflow under a given playbook, it's actions, branches, etc. under a new name.
	 * @param sourceWorkflowId Current workflow ID to be duplicated
	 * @param destinationPlaybookId ID of playbook the workflow will be duplicated to
	 * @param newName Name for the new copy to be saved
	 */
	duplicateWorkflow(
		sourceWorkflowId: string, destinationPlaybookId: string, newName: string,
	): Promise<Workflow> {
		return this.http.post(`/api/workflows?source=${sourceWorkflowId}`,
			{ playbook_id: destinationPlaybookId, name: newName })
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Deletes a given workflow under a given playbook.
	 * @param workflowIdToDelete ID of the workflow to be deleted
	 */
	deleteWorkflow(workflowIdToDelete: string): Promise<void> {
		return this.http.delete(`/api/workflows/${workflowIdToDelete}`)
			.toPromise()
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Creates a new workflow under a given playbook.
	 * @param playbookId ID of the playbook the new workflow should be added under
	 * @param workflow Workflow to be saved
	 */
	newWorkflow(playbookId: string, workflow: Workflow): Promise<Workflow> {
		workflow.playbook_id = playbookId;

		return this.http.post('/api/workflows', classToPlain(workflow))
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Saves the data of a given workflow specified under a given playbook.
	 * @param workflow Data to be saved under the workflow (actions, etc.)
	 */
	saveWorkflow(workflow: Workflow): Promise<Workflow> {
		return this.http.put('/api/workflows', classToPlain(workflow))
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Loads the data of a given workflow under a given playbook.
	 * @param workflowId ID of the workflow to load
	 */
	loadWorkflow(workflowId: string): Promise<Workflow> {
		return this.http.get(`/api/workflows/${workflowId}`)
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Notifies the server to execute a given workflow.
	 * Note that execution results are not returned here, but on a separate stream-actions EventSource.
	 * @param workflowId ID of the workflow to execute
	 */
	addWorkflowToQueue(workflowId: string): Promise<WorkflowStatus> {
		return this.executionService.addWorkflowToQueue(workflowId);
	}

	/**
	 * Returns an array of all devices within the DB.
	 */
	getDevices(): Promise<Device[]> {
		return this.devicesService.getAllDevices();
	}

	/**
	 * Gets all app apis from the server.
	 */
	getApis(): Promise<AppApi[]> {
		return this.http.get('/api/apps/apis')
			.toPromise()
			.then((data) => plainToClass(AppApi, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Returns an array of all users within the DB.
	 */
	getUsers(): Promise<User[]> {
		return this.settingsService.getAllUsers();
	}

	/**
	 * Returns an array of all roles within the application.
	 */
	getRoles(): Promise<Role[]> {
		return this.settingsService.getRoles();
	}
}
