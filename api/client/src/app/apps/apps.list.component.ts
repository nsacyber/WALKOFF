import { Component, ViewEncapsulation, OnInit, OnDestroy} from '@angular/core';
import 'rxjs/Rx';
import * as Fuse from 'fuse.js';
import { saveAs } from 'file-saver';
import { UUID } from 'angular2-uuid';
import { Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { FormControl } from '@angular/forms';
import { plainToClass } from 'class-transformer';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { AuthService } from '../auth/auth.service';
import { PlaybookService } from '../playbook/playbook.service';
import { UtilitiesService } from '../utilities.service';
import { GlobalsService } from '../globals/globals.service';
import { SettingsService } from '../settings/settings.service';
import { Workflow } from '../models/playbook/workflow';
import { AppService } from './app.service';
import { AppApi } from '../models/api/appApi';
import { StatusModalComponent } from './status.modal.component';

@Component({
	selector: 'apps-list-component',
	templateUrl: './apps.list.html',
	styleUrls: [
		'./apps.list.scss',
	],
	encapsulation: ViewEncapsulation.None,
	providers: [AuthService, GlobalsService, SettingsService],
})
export class AppsListComponent implements OnInit, OnDestroy {
	workflowsLoaded: boolean = false;
	workflows: Workflow[] = [];
	eventSource: any;
	filterQuery: FormControl = new FormControl();
	filteredWorkflows: Workflow[] = [];

	apps: AppApi[];

	constructor(
		private playbookService: PlaybookService, private authService: AuthService,
		private appService: AppService,
		private toastrService: ToastrService, private utils: UtilitiesService, 
		private modalService: NgbModal, private router: Router
	) {}

	/**
	 * On component initialization, we grab arrays of globals, app apis, and playbooks/workflows (id, name pairs).
	 * We also initialize an EventSoruce for Action Statuses for the execution results table.
	 * Also initialize cytoscape event bindings.
	 */
	ngOnInit(): void {
		this.appService.getApis().then(apps => this.apps = apps);
	}

	/**
	 * Closes our SSEs on component destroy.
	 */
	ngOnDestroy(): void { }

	manageApp(app: AppApi): void {
		this.router.navigateByUrl(`/apps/${ app.id }`);
	}

	async buildImage(appApi: AppApi) {
		const buildId = await this.appService.buildImage(appApi);
        const modalRef = this.modalService.open(StatusModalComponent, { size: 'xl', centered: true });
        modalRef.componentInstance.buildId = buildId;
        modalRef.componentInstance.appApi = appApi;
    }
}
