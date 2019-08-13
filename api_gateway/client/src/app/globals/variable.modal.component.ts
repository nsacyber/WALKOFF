import {Component, Input, ViewChild, OnInit} from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { Variable } from '../models/variable';
import { JsonEditorComponent } from 'ang-jsoneditor';

@Component({
  selector: 'variable-modal-component',
  templateUrl: './variable.modal.html',
})
export class VariableModalComponent implements OnInit{
  @Input() variable: Variable = new Variable();
  @Input() isGlobal: boolean = false;
  @ViewChild('jsonEditor', { static: true }) jsonEditor: JsonEditorComponent;
  existing: boolean = false;

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

  initialValue;

  constructor(public activeModal: NgbActiveModal) {}

  ngOnInit(): void {
    this.initialValue = this.variable.value;
  }
  
  updateValue($event: any): void {
		this.variable.value = $event;
	}
}