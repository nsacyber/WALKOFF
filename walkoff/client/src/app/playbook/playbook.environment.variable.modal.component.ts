import {Component, Input} from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { EnvironmentVariable } from '../models/playbook/environmentVariable';

@Component({
  selector: 'playbook-environment-variable-modal-component',
  templateUrl: './playbook.environment.variable.modal.html',
})
export class PlaybookEnvironmentVariableModalComponent {
  @Input() variable: EnvironmentVariable = new EnvironmentVariable();
  existing: boolean = false;

  constructor(public activeModal: NgbActiveModal) {}
}