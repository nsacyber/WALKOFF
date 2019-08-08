import { Component, ViewEncapsulation, OnInit, OnDestroy} from '@angular/core';
import 'rxjs/Rx';
import * as Fuse from 'fuse.js';
import { saveAs } from 'file-saver';
import { UUID } from 'angular2-uuid';
import { Router, ActivatedRoute } from '@angular/router';
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
import { WorkflowStatuses } from '../models/execution/workflowStatus';
import { MetadataModalComponent } from '../playbook/metadata.modal.component';
import { ImportModalComponent } from '../playbook/import.modal.component';
import { WorkflowStatusEvent } from '../models/execution/workflowStatusEvent';
import { AppService } from './app.service';
import { AppApi } from '../models/api/appApi';
import * as CodeMirror from 'codemirror'

//import $ from "jquery";  // CSS or LESS
import { createTree } from 'jquery.fancytree';
import 'jquery.fancytree/dist/modules/jquery.fancytree.edit';
import 'jquery.fancytree/dist/modules/jquery.fancytree.filter';

@Component({
	selector: 'manage-app-component',
	templateUrl: './manage.app.html',
	styleUrls: [
		'./manage.app.scss',
	],
	encapsulation: ViewEncapsulation.None,
	providers: [AuthService, GlobalsService, SettingsService],
})
export class ManageAppComponent implements OnInit, OnDestroy {
	workflowsLoaded: boolean = false;
	workflows: Workflow[] = [];
	eventSource: any;
	filterQuery: FormControl = new FormControl();
	filteredWorkflows: Workflow[] = [];

    apps: AppApi[];
    currentApp: AppApi;
    currentFile: string;
    content: string;
    filesLoaded = false;
    fileTree: any;

    options: any = {
        lineNumbers: true,
        //theme: 'ttcn'
    }

	constructor(
		private playbookService: PlaybookService, private authService: AuthService,
		private appService: AppService, private activeRoute: ActivatedRoute,
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
            
        this.activeRoute.params.subscribe(params => {
            if (params.appId) {
                this.appService.getApi(params.appId).then(app => {
                    this.currentApp = app;
                    this.appService.listFiles(app).then(files => {
                        this.filesLoaded = true;
                        this.fileTree = createTree('#tree', {
                            extensions: ['edit', 'filter'],
                            source: files,
                            activate: (event, data) => (data.node.folder) ? '' : this.loadFile(data.node.data.path),
                            renderNode: (event, data)  => {
                                var node = data.node;
                                var $nodeSpan = $(node.span);
                            
                                // check if span of node already rendered
                                if (node.folder && !$nodeSpan.data('rendered')) {
                            
                                    var newFileLink = $('<a href="#" class="fancytree-title small">+New File</a>');
                                    newFileLink.click(() => {
                                        this.createFile(node.data.path);
                                        return false;
                                    })
                            
                                    $nodeSpan.append(newFileLink);
                                    $nodeSpan.data('rendered', true);
                                }
                            }
                        });
                    });
                });
            }
        })
    }

    async createFile(root: string) {
        const path = root + await this.utils.prompt('Enter name for new file');
        await this.appService.putFile(this.currentApp, path, '')
        await this.fileTree.reload(await this.appService.listFiles(this.currentApp))
        this.toastrService.success(`Created <b>${ path }</b>`);
    }
    
    loadFile(path: string) {
        const filetype = (CodeMirror as any).findModeByFileName(path);
        this.appService.getFile(this.currentApp, path).then(content => {
            this.content = content;
            this.currentFile = path;
            this.options.mode =  filetype ? filetype.mode : 'null';
        });
    }

    saveFile() {
        this.appService.putFile(this.currentApp, this.currentFile, this.content).then(() => {
            this.toastrService.success(`Saved <b>${ this.currentFile }</b>`);
        });
    }

    buildImage() {
        this.appService.buildImage(this.currentApp).then(() => {
            this.toastrService.success(`Building App <b>${this.currentApp.name}</b>`);
        })
    }

	/**
	 * Closes our SSEs on component destroy.
	 */
	ngOnDestroy(): void {}

	manageApp(app: AppApi): void {
		this.router.navigateByUrl(`/apps/${ app.id }`);
    }

}
