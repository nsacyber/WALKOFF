import {Component, Input} from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { Variable } from '../models/variable';

@Component({
  selector: 'variable-modal-component',
  templateUrl: './variable.modal.html',
})
export class VariableModalComponent {
  @Input() variable: Variable = new Variable();
  @Input() isGlobal: boolean = false;
  existing: boolean = false;

  constructor(public activeModal: NgbActiveModal) {}
}