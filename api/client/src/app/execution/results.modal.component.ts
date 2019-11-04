import { Component, Input, ViewChild, ViewEncapsulation, OnInit, OnDestroy, ElementRef } from '@angular/core';

import { NgbActiveModal, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../auth/auth.service';
import { UtilitiesService } from '../utilities.service';
import { DatatableComponent } from '@swimlane/ngx-datatable';
import { WorkflowStatus } from '../models/execution/workflowStatus';
import { NodeStatuses } from '../models/execution/nodeStatus';
import { JsonModalComponent } from './json.modal.component';

@Component({
    selector: 'results-modal-component',
    templateUrl: './results.modal.html',
    styleUrls: [
        './results.modal.scss',
    ],
    encapsulation: ViewEncapsulation.None,
})
export class ResultsModalComponent implements OnInit, OnDestroy {
    @Input() loadedWorkflowStatus: WorkflowStatus;
    @ViewChild('nodeStatusContainer', { static: false }) nodeStatusContainer: ElementRef;
    @ViewChild('nodeStatusTable', { static: false }) nodeStatusTable: DatatableComponent;
    NodeStatuses = NodeStatuses;

    editorOptionsData: any = {
		mode: 'code',
		modes: ['code', 'view'],
		history: false,
		search: false,
		// mainMenuBar: false,
		navigationBar: false,
		statusBar: false,
		enableSort: false,
        enableTransform: false,
        onEditable: () => false
	}

    constructor(public activeModal: NgbActiveModal, public utils: UtilitiesService,
        public toastrService: ToastrService, public authService: AuthService,
        public modalService: NgbModal) { }

    ngOnInit(): void {}

    ngOnDestroy(): void {}

    resultsModal(results) {
		const modalRef = this.modalService.open(JsonModalComponent, { size: 'lg', centered: true });
		modalRef.componentInstance.results = results;
		return false;
	}
}