import { Component, Input, ViewChild, ViewEncapsulation, OnInit, OnDestroy } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../auth/auth.service';

import { UtilitiesService } from '../utilities.service';
import { JsonEditorComponent } from 'ang-jsoneditor';

@Component({
    selector: 'json-modal-component',
    templateUrl: './json.modal.html',
    styleUrls: [
        './json.modal.scss',
    ],
    encapsulation: ViewEncapsulation.None,
})
export class JsonModalComponent implements OnInit, OnDestroy {
    @Input() results: string;
    @ViewChild('jsonEditor', { static: false }) jsonEditor: JsonEditorComponent;

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
        public toastrService: ToastrService, public authService: AuthService) { }

    ngOnInit(): void {}

    ngOnDestroy(): void {}

    getClipboard() {
        return  ($.isPlainObject(this.results) || $.isArray(this.results)) ?
            JSON.stringify(this.results, null, 2) : this.results;
    }

    downloadResults() {
        var element = document.createElement('a');
        element.setAttribute('href', 'data:application/json;charset=utf-8,' + encodeURIComponent(this.getClipboard()));
        element.setAttribute('download', 'action-results.json');  
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    }
}