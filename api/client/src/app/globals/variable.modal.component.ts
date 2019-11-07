import { Component, Input, OnInit, ViewChild } from "@angular/core";

import { NgbActiveModal } from "@ng-bootstrap/ng-bootstrap";
import { Variable, VariablePermission } from "../models/variable";
import { SettingsService } from "../settings/settings.service";
import { Role } from "../models/role";
import { ToastrService } from "ngx-toastr";
import { JsonEditorComponent } from "ang-jsoneditor";

@Component({
  selector: "variable-modal-component",
  templateUrl: "./variable.modal.html",
  styleUrls: ["./variable.modal.scss"]
})
export class VariableModalComponent implements OnInit {
  @Input() variable: Variable = new Variable();
  @Input() isGlobal: boolean = false;
  @ViewChild("jsonEditor", { static: true }) jsonEditor: JsonEditorComponent;
  initialValue: string;
  existing: boolean = false;
  hasPermissions: boolean = true;
  permissionOptions = VariablePermission.PERMISSIONS;
  systemRoles: Role[];
  permissions: any[] = [];
  newPermission: any = { role: "", permissions: "" };

  constructor(
    public activeModal: NgbActiveModal,
    public settingsService: SettingsService,
    public toastrService: ToastrService
  ) {}

  editorOptionsData: any = {
    mode: "code",
    modes: ["code", "tree"],
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
  };

  ngOnInit(): void {
    this.settingsService.getRoles().then(roles => (this.systemRoles = roles));
    this.initialValue = this.variable.value;
  }

  addPermission() {
    if (
      !this.getRoleName(this.newPermission) ||
      !this.getPermissionDescription(this.newPermission)
    ) {
      return this.toastrService.error("Select a role and permission");
    }

    const existingPermission = this.variable.permissions.permissions.find(
      p => p.role == this.newPermission.role
    );
    existingPermission
      ? (existingPermission.permissions = this.newPermission.permissions)
      : this.variable.permissions.permissions.push(this.newPermission);

    this.variable.permissions.permissions.sort((a, b) =>
      this.getRoleName(a).localeCompare(this.getRoleName(b))
    );
    this.newPermission = { role: "", permissions: "" };
  }

  deletePermission(p: any) {
    this.variable.permissions.permissions = this.variable.permissions.permissions.filter(
      permission => permission.role != p.role
    );
  }

  getRoleName(p: any): string {
    const role = this.systemRoles.find(role => role.id == p.role);
    return role ? role.name : null;
  }

  getPermissionDescription(r: any): string {
    const permission = this.permissionOptions.find(
      o => JSON.stringify(o.crud) == JSON.stringify(r.permissions)
    );
    return permission ? permission.description : null;
  }

    submit() {
        if (this.variable.permissions.access_level != 2) this.variable.permissions.permissions = [];
        this.activeModal.close(this.variable)
    }
}
