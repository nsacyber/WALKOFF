import {Component, Input, ViewChild} from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { EnvironmentVariable } from '../models/playbook/environmentVariable';
import { JsonEditorComponent } from 'ang-jsoneditor';

@Component({
  selector: 'playbook-environment-variable-modal-component',
  templateUrl: './playbook.environment.variable.modal.html',
})
export class PlaybookEnvironmentVariableModalComponent {
  @Input() variable: EnvironmentVariable = new EnvironmentVariable();
  @ViewChild('jsonEditor', { static: true }) jsonEditor: JsonEditorComponent;

  editorOptionsData: any = {
		mode: 'code',
		modes: ['code', 'tree'],
		history: false,
		search: false,
		// mainMenuBar: false,
		navigationBar: false,
		statusBar: false,
		enableSort: false,
		enableTransform: false,
	}

  constructor(public activeModal: NgbActiveModal) {}
}