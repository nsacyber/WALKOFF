import { Injectable } from '@angular/core';
import { plainToClass, classToPlain } from 'class-transformer';
import { HttpClient } from '@angular/common/http';

import { Workflow } from '../models/playbook/workflow';
import { Playbook } from '../models/playbook/playbook';
import { AppApi } from '../models/api/appApi';
import { Global } from '../models/global';
import { Variable } from '../models/variable';
import { User } from '../models/user';
import { Role } from '../models/role';
import { WorkflowStatus } from '../models/execution/workflowStatus';

import { GlobalsService } from '../globals/globals.service';
import { ExecutionService } from '../execution/execution.service';
import { SettingsService } from '../settings/settings.service';
import { UtilitiesService } from '../utilities.service';

import { UUID } from 'angular2-uuid';

import { Observable } from 'rxjs/Observable';
import 'rxjs/add/operator/catch';
import 'rxjs/add/operator/map';
import { Subscriber } from 'rxjs';
import { ActionType } from '../models/api/actionApi';

@Injectable({
	providedIn: 'root'
})
export class PlaybookService {

	workflowsChange: Observable<any>;
	observer: Subscriber<any>;

	tempStoredWorkflow: Workflow;

	constructor(private http: HttpClient, private utils: UtilitiesService, private executionService: ExecutionService,
		private globalsService: GlobalsService, private settingsService: SettingsService) {
		this.workflowsChange = new Observable((observer) => {
			this.observer = observer;
			this.getWorkflows().then(workflows => this.observer.next(workflows));
		})
	}

	emitChange(data: any) {
		if (this.observer) this.getWorkflows().then(workflows => this.observer.next(workflows));
		return data;
	}

	/**
	 * Returns all playbooks and their child workflows in minimal form (id, name).
	 */
	getPlaybooks(): Promise<Playbook[]> {
		return this.http.get('api/playbooks')
			.toPromise()
			.then((data) => plainToClass(Playbook, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Saves a new playbook.
	 * @param playbook New playbook to be saved
	 */
	newPlaybook(playbook: Playbook): Promise<Playbook> {
		return this.http.post('api/playbooks', classToPlain(playbook))
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
		return this.http.patch('api/playbooks', { id: playbookId, name: newName })
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
		return this.http.post(`api/playbooks?source=${playbookId}`, { name: newName })
			.toPromise()
			.then((data) => plainToClass(Playbook, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Deletes a playbook by name.
	 * @param playbookIdToDelete ID of playbook to be deleted.
	 */
	deletePlaybook(playbookIdToDelete: string): Promise<void> {
		return this.http.delete(`api/playbooks/${playbookIdToDelete}`)
			.toPromise()
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Exports a playbook as an Observable (component handles the actual 'save').
	 * @param playbookId: ID of playbook to export
	 */
	exportPlaybook(playbookId: string): Observable<Blob> {
		return this.http.get(`api/playbooks/${playbookId}?mode=export`, { responseType: 'blob' })
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Exports a playbook as an Observable (component handles the actual 'save').
	 * @param workflowId: ID of playbook to export
	 */
	exportWorkflow(workflowId: string): Promise<Blob> {
		return this.http.get(`api/workflows/${workflowId}?mode=export`, { responseType: 'blob' })
			.toPromise()
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Imports a playbook from a supplied file.
	 * @param fileToImport File to be imported
	 */
	async importWorkflow(fileToImport: File): Promise<Workflow> {
		const body: FormData = new FormData();
		body.append('file', fileToImport, fileToImport.name);

		return this.http.post('api/workflows/upload', body)
			.toPromise()
			.then((data) => this.emitChange(data))
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	async nextWorkflowName(name: string) : Promise<string> {
		const workflows = await this.getWorkflows();
		const count = workflows.filter(w => w.name.match(new RegExp(`^${ name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') }( \(\d+\))?$`))).length;
		return (count > 0) ? `${ name } (${ count })`: name;
	}

	/**
	 * Returns all playbooks and their child workflows in minimal form (id, name).
	 */
	getWorkflows(): Promise<Workflow[]> {
		return this.http.get('api/workflows/')
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Duplicates a workflow under a given playbook, it's actions, branches, etc. under a new name.
	 * @param sourceWorkflowId Current workflow ID to be duplicated
	 * @param destinationPlaybookId ID of playbook the workflow will be duplicated to
	 * @param newName Name for the new copy to be saved
	 */
	duplicateWorkflow(
		sourceWorkflowId: string, newName: string,
	): Promise<Workflow> {
		return this.http.post(`api/workflows/copy?source=${sourceWorkflowId}`,
			{ name: newName })
			.toPromise()
			.then((data) => this.emitChange(data))
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Deletes a given workflow under a given playbook.
	 * @param workflowIdToDelete ID of the workflow to be deleted
	 */
	deleteWorkflow(workflowIdToDelete: string): Promise<void> {
		return this.http.delete(`api/workflows/${workflowIdToDelete}`)
			.toPromise()
			.then((data) => this.emitChange(data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Creates a new workflow under a given playbook.
	 * @param playbookId ID of the playbook the new workflow should be added under
	 * @param workflow Workflow to be saved
	 */
	newWorkflow(workflow: Workflow): Promise<Workflow> {
		workflow.id = UUID.UUID();
		return this.http.post('api/workflows/', classToPlain(workflow))
			.toPromise()
			.then((data) => this.emitChange(data))
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Saves the data of a given workflow specified under a given playbook.
	 * @param workflow Data to be saved under the workflow (actions, etc.)
	 */
	saveWorkflow(workflow: Workflow): Promise<Workflow> {
		return this.http.put(`api/workflows/${workflow.id}`, classToPlain(workflow))
			.toPromise()
			.then((data) => this.emitChange(data))
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Loads the data of a given workflow under a given playbook.
	 * @param workflowId ID of the workflow to load
	 */
	loadWorkflow(workflowId: string): Promise<Workflow> {
		return this.http.get(`api/workflows/${workflowId}`)
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Notifies the server to execute a given workflow.
	 * Note that execution results are not returned here, but on a separate stream-actions EventSource.
	 * @param workflowId ID of the workflow to execute
	 */
	addWorkflowToQueue(workflowId: string, executionId: string = null): Promise<WorkflowStatus> {
		return this.executionService.addWorkflowToQueue(workflowId, executionId);
	}

	/**
	 * For a given executing workflow, asyncronously perform some action to change its status.
	 * Only returns success
	 * @param executionId Execution ID to act upon
	 * @param action Action to take (e.g. abort, resume, pause)
	 */
	performWorkflowTrigger(executionId: string, trigger: string, data = {}): Promise<void> {
		return this.http.patch(`api/workflowqueue/${ executionId }`, { status: 'trigger',  trigger_id: trigger, trigger_data: data})
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Returns an array of all globals within the DB.
	 */
	getGlobals(): Promise<Variable[]> {
		return this.globalsService.getAllGlobals();
	}

	/**
	 * Gets all app apis from the server.
	 */
	getApis(): Promise<AppApi[]> {
		return this.http.get('api/apps/apis/')
			.toPromise()
			// .then((data: any[]) => {
			// 	return [{
			// 		id_: '30f06bd4-3703-f8a9-47e0-8853ea916913',
			// 		name: 'Builtin',
			// 		description: 'Walkoff built-in functions',
			// 		app_version: '1.0.1',
			// 		walkoff_version: '1.0.0',
			// 		contact_info: {email: "walkoff@nsa.gov", name: "Walkoff Team", url: "https://github.com/nsacyber/walkoff"},
			// 		license_info: {name: "Creative Commons", url: "https://github.com/nsacyber/WALKOFF/blob/master/LICENSE.md"},
			// 		external_docs: {},
			// 		actions: [
			// 			{
			// 				id_: '7a1c6838-1b14-4ddc-7d84-935fcbc260ca',
			// 				name: 'Condition',
			// 				node_type: ActionType.CONDITION,
			// 			},
			// 			{
			// 				id_: '21f7c721-448f-da7b-fea9-9b781824e7d3',
			// 				name: 'Trigger',
			// 				node_type: ActionType.TRIGGER,
			// 			},
			// 			{
			// 				id_: '40a9e8ee-9a4f-ffb7-0a01-0cd25a6bd3a2',
			// 				name: 'Transform',
			// 				node_type: ActionType.TRANSFORM,
			// 			}
			// 		]
			// 	}].concat(data);
			// })
			.then((data: any[]) => plainToClass(AppApi, data))
			.then((appApis: AppApi[]) => {
				appApis.forEach(app => app.action_apis.map(action => {
					action.app_name = app.name;
					action.app_version = app.app_version;
					return action;
				}))
				return appApis;
			})
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

	get workflowToCreate(): Workflow {
		const w = this.tempStoredWorkflow;
		//this.tempStoredWorkflow = null;
		return w;
	}

	set workflowToCreate(workflow: Workflow) {
		this.tempStoredWorkflow = workflow;
	}

}
