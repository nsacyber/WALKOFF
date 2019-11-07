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
  @Input() existing: boolean = false;
  @ViewChild('jsonEditor', { static: true }) jsonEditor: JsonEditorComponent;

  initialValue: string;
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
		onChange: () => {
			try {
			  	this.variable.value = this.jsonEditor.get() as any;
			}
			catch(e) {
				this.variable.value = this.jsonEditor.getText();
			}
		}
	}

	
	constructor(public activeModal: NgbActiveModal) {}

	ngOnInit(): void {
    	this.initialValue = this.variable.value;
	}
	
}