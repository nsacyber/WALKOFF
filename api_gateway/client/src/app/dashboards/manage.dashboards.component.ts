import { Component, OnInit } from '@angular/core';
import { GridsterConfig, GridType, CompactType } from 'angular-gridster2';
import { DashboardWidget, BarChartWidget, PieChartWidget, LineChartWidget, TextWidget, KibanaWidget, TableWidget } from '../models/dashboard/dashboardWidget';
import { Dashboard } from '../models/dashboard/dashboard';
import { DashboardService } from './dashboard.service';
import { ToastrService } from 'ngx-toastr';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { WidgetModalComponent } from './widget.modal.component';
import { UtilitiesService } from '../utilities.service';

@Component({
    selector: 'manage-dashboards-component',
    templateUrl: './manage.dashboards.component.html',
    styleUrls: ['./manage.dashboards.component.scss']
})
export class ManageDashboardsComponent implements OnInit {

    options: GridsterConfig;

    dashboard: Dashboard = new Dashboard();
    existingDashboard = false;

    gridRows = 16;
    gridColumns = 8;
    gridColSize = 75;
    gridGutterSize = 10;
    gridDefaultCols = 3;

    constructor(
        private dashboardService: DashboardService, 
        private toastrService: ToastrService,
        private activeRoute: ActivatedRoute,
        private router: Router,
        private modalService: NgbModal,
        private utils: UtilitiesService
    ) {}

    ngOnInit() {
        this.activeRoute.params.subscribe(params => {
            if (params.dashboardId) {
                this.existingDashboard = true;
                this.dashboardService.getDashboardWithMetadata(params.dashboardId).then(dashboard => {
                    this.dashboard = dashboard;
                });
            }

            this.initGrid();
        })
    }

    initGrid() {
        this.options = {
            gridType: GridType.Fixed,
            compactType: CompactType.None,
            pushItems: true,
            draggable: {
                enabled: true
            },
            resizable: {
                enabled: true
            },
            fixedColWidth: this.gridColSize * 4/3,
            fixedRowHeight: this.gridColSize * 3/4,
            minCols: this.gridColumns,
            maxCols: this.gridColumns,
            minRows: 1,
            maxRows: this.gridRows,
            maxItemCols: this.gridColumns,
            minItemCols: 1,
            maxItemRows: this.gridRows,
            minItemRows: 1,
            defaultItemCols: this.gridDefaultCols,
            defaultItemRows: 1
        };
    }

    getGridWidth() {
        return this.gridColumns * Math.ceil(this.gridColSize * 4/3 + this.gridGutterSize) + this.gridGutterSize + 'px';
    }

    getGridHeight() {
        return this.gridRows * Math.ceil(this.gridColSize * 3/4 + this.gridGutterSize) + this.gridGutterSize + 'px';
    }

    changedOptions() {
        this.options.api.optionsChanged();
    }

    editWidget($event: Event, widget) {
        $event.preventDefault();
        const modalRef = this.modalService.open(WidgetModalComponent);
		modalRef.componentInstance.widget = widget;
    }

    removeWidget($event: Event, widget) {
        $event.preventDefault();
        this.dashboard.widgets.splice(this.dashboard.widgets.indexOf(widget), 1);
    }

    addWidget(type: string): void {
        let widget: DashboardWidget;

        switch (type) {
            case "bar":
                widget = new BarChartWidget();
            break;
            case "line":
                widget = new LineChartWidget();
            break;
            case "pie":
                widget = new PieChartWidget();
            break;
            case "text":
                widget = new TextWidget();
            break;
            case "table":
                widget = new TableWidget();
            break;
            case "kibana":
                widget = new KibanaWidget();
            break;
        }

        const modalRef = this.modalService.open(WidgetModalComponent);
		modalRef.componentInstance.widget = widget;
		modalRef.result.then(addedWidget => {
			this.dashboard.widgets.push(addedWidget);
		}).catch(() => null)
    }
    
    save() {
        if (!this.dashboard.name) return this.toastrService.error('Enter a name for the dashboard');

        (this.existingDashboard) ? this.dashboardService.updateDashboard(this.dashboard) : this.dashboardService.newDashboard(this.dashboard);
        this.toastrService.success(`"${ this.dashboard.name }" Saved`);

        this.router.navigate(['/dashboard', this.dashboard.id]);
    }

    async delete() {
        await this.utils.confirm(`Are you sure you want to delete this dashboard?`);

        const dashboardName = this.dashboard.name;
        this.dashboardService.deleteDashboard(this.dashboard);
        this.toastrService.success(`"${ dashboardName }" Deleted`);
        this.router.navigate(['/dashboard/new']);
    }
}
