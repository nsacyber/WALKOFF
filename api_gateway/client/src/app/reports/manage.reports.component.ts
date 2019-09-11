import { Component, OnInit } from '@angular/core';
import { GridsterConfig, GridType, CompactType } from 'angular-gridster2';
import { ReportWidget, BarChartWidget, PieChartWidget, LineChartWidget, TextWidget, KibanaWidget, TableWidget } from '../models/report/reportWidget';
import { Report } from '../models/report/report';
import { ReportService } from './report.service';
import { ToastrService } from 'ngx-toastr';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { WidgetModalComponent } from './widget.modal.component';
import { UtilitiesService } from '../utilities.service';

@Component({
    selector: 'manage-reports-component',
    templateUrl: './manage.reports.component.html',
    styleUrls: ['./manage.reports.component.scss']
})
export class ManageReportsComponent implements OnInit {

    options: GridsterConfig;

    report: Report = new Report();
    originalReport: Report = new Report();

    existingReport = false;
    submitted = false;

    gridRows = 16;
    gridColumns = 8;
    gridColSize = 75;
    gridGutterSize = 10;
    gridDefaultCols = 3;

    widgets = [
        {name: 'text', label: 'Text Widget'},
        {name: 'table', label: 'Table Widget'},
        {name: 'bar', label: 'Bar Graph'},
        {name: 'line', label: 'Line Graph'},
        {name: 'pie', label: 'Pie Graph'},
        {name: 'kibana', label: 'Kibana Embed'},
    ];

    constructor(
        private reportService: ReportService, 
        private toastrService: ToastrService,
        private activeRoute: ActivatedRoute,
        private router: Router,
        private modalService: NgbModal,
        private utils: UtilitiesService
    ) {}

    ngOnInit() {
        this.activeRoute.params.subscribe(params => {
            if (params.reportId) {
                this.existingReport = true;
                this.reportService.getReportWithMetadata(params.reportId).then(report => {
                    this.report = report;
                    this.originalReport = this.report.clone();
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
        this.report.widgets.splice(this.report.widgets.indexOf(widget), 1);
    }

    addWidget(type: string): void {
        let widget: ReportWidget;

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
        modalRef.componentInstance.typeLabel = this.widgets.find(w => w.name == type).label;
		modalRef.result.then(addedWidget => {
			this.report.widgets.push(addedWidget);
		}).catch(() => null)
    }
    
    save() {
        if (!this.report.name) return this.submitted = true;

        (this.existingReport) ? this.reportService.updateReport(this.report) : this.reportService.newReport(this.report);

        this.originalReport = this.report.clone();
        this.toastrService.success(`"${ this.report.name }" Saved`);

        this.router.navigate(['/report', this.report.id]);
    }

    async delete() {
        await this.utils.confirm(`Are you sure you want to delete this report?`);

        const reportName = this.report.name;
        this.reportService.deleteReport(this.report);
        this.toastrService.success(`"${ reportName }" Deleted`);
        this.router.navigate(['/report/new']);
    }

    canDeactivate(): Promise<boolean> | boolean {
        return this.checkUnsavedChanges(); 
    }

    async checkUnsavedChanges() : Promise<boolean> {
        if (!this.reportChanged) return true;
        return this.utils.confirm('Any unsaved changes will be lost. Are you sure?', { alwaysResolve: true });
    }

    get reportChanged(): boolean {
		return this.report && JSON.stringify(this.originalReport).localeCompare(JSON.stringify(this.report)) != 0;
	}
}
