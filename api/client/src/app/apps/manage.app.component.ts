import { Component, ViewEncapsulation, OnInit, OnDestroy, ViewChild} from '@angular/core';
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
import { AppService } from './app.service';
import { AppApi } from '../models/api/appApi';
import * as CodeMirror from 'codemirror'

//import $ from "jquery";  // CSS or LESS
import { createTree } from 'jquery.fancytree';
import 'jquery.fancytree/dist/modules/jquery.fancytree.edit';
import 'jquery.fancytree/dist/modules/jquery.fancytree.filter';
import { CodemirrorComponent } from '@ctrl/ngx-codemirror';
import { StatusModalComponent } from './status.modal.component';
import { FileModalComponent } from './file.modal.component';

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
    @ViewChild('editorArea', { static: false }) editorArea: CodemirrorComponent;

	workflowsLoaded: boolean = false;
	workflows: Workflow[] = [];
	eventSource: any;
	filterQuery: FormControl = new FormControl();
    filteredWorkflows: Workflow[] = [];

    apps: AppApi[];
    currentApp: AppApi;
    currentFile: string;
    orginalContent: string;
    content: string;
    filesLoaded = false;
    fileTree: any;

    options: any = {
        lineNumbers: true,
        //theme: 'ttcn'
    }

    warningCallback: any;

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
                            
                                    var newFileLink = $('<a href="#" title="New File" class="fancytree-title small mr-1"><i class="fa fa-plus-square" aria-hidden="true"></i></a>');
                                    newFileLink.click(() => {
                                        this.createFile(node.data.path);
                                        return false;
                                    })

                                    var uploadFileLink = $('<a href="#" title="Upload File" class="fancytree-title small"><i class="fa fa-upload" aria-hidden="true"></i></a>');
                                    uploadFileLink.click(() => {
                                        this.uploadFile(node.data.path);
                                        return false;
                                    })
                            
                                    $nodeSpan.append(newFileLink, uploadFileLink);
                                    $nodeSpan.data('rendered', true);
                                }
                            }
                        });
                    });
                });
            }
        })
    }

	ngOnDestroy(): void {}

    get fileChanged(): boolean {
        return this.currentFile && this.orginalContent.localeCompare(this.content) != 0;
    }

    canDeactivate(): Promise<boolean> | boolean {
        return this.checkUnsavedChanges(); 
    }

    async checkUnsavedChanges() : Promise<boolean> {
        if (!this.fileChanged) return true;
        return this.utils.confirm('Any unsaved changes will be lost. Are you sure?', { alwaysResolve: true });
    }

    async createFile(root: string) {
        if (!await this.checkUnsavedChanges()) return;

        const path = root + await this.utils.prompt('Add New File', { 
            required: true,
            message: '<h6>Enter name for new file:</h6>',
            buttons: {
                confirm: { label: 'Add'}
            },
        });
        await this.appService.putFile(this.currentApp, path, '')
        await this.fileTree.reload(await this.appService.listFiles(this.currentApp))

        this.selectTreeNode(path);
        this.loadFile(path, false)
        this.toastrService.success(`Created <b>${ path }</b>`);
    }

    async uploadFile(root: string) {
        if (!await this.checkUnsavedChanges()) return;

        const modalRef = this.modalService.open(FileModalComponent);
        const fileInfo = await modalRef.result;
        const path = root + fileInfo.path;
        await this.appService.putFile(this.currentApp, path, fileInfo.body)
        await this.fileTree.reload(await this.appService.listFiles(this.currentApp))

        this.selectTreeNode(path);
        this.loadFile(path, false)
        this.toastrService.success(`Created <b>${ path }</b>`);
    }

    selectTreeNode(path: string) {
        const newNode = this.fileTree.findFirst(((n) => path.localeCompare(n.data.path) == 0))
        this.fileTree.activateKey(newNode.key, { noEvents: true });
    }
    
    async loadFile(path: string, checkUnsaved: boolean = true) {
        if(checkUnsaved && !await this.checkUnsavedChanges()) 
            return this.selectTreeNode(this.currentFile);

        const filetype = (CodeMirror as any).findModeByFileName(path);
        this.appService.getFile(this.currentApp, path).then(content => {
            this.orginalContent = this.content = content;
            this.currentFile = path;
            this.options.mode =  filetype ? filetype.mode : 'null';
            setTimeout(() => {
                this.editorArea.codeMirror.getDoc().clearHistory();
                this.editorArea.codeMirrorGlobal.commands.save = (instance) => {
                    if (instance == this.editorArea.codeMirror)
                        this.saveFile();
                }
            });
        });
    }

    saveFile() {
        if (!this.fileChanged) return;
        this.orginalContent = this.content;
        this.appService.putFile(this.currentApp, this.currentFile, this.content).then(() => {
            this.toastrService.success(`Saved <b>${ this.currentFile }</b>`);
        });
    }

    async buildImage() {
        if (!await this.checkUnsavedChanges()) return;

        const buildId = await this.appService.buildImage(this.currentApp);
        const modalRef = this.modalService.open(StatusModalComponent, { size: 'xl', centered: true });
        modalRef.componentInstance.buildId = buildId;
        modalRef.componentInstance.appApi = this.currentApp;
    }

    undo() {
        this.editorArea.codeMirror.execCommand('undo')
    }

    redo() {
        this.editorArea.codeMirror.execCommand('redo')
    }

	manageApp(app: AppApi): void {
		this.router.navigateByUrl(`/apps/${ app.id }`);
    }

}
