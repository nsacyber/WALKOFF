import { Component, ViewEncapsulation, OnInit, ViewChild, ChangeDetectorRef } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { Select2OptionData } from 'ng2-select2';
import 'rxjs/add/operator/debounceTime';
import { DatatableComponent } from '@swimlane/ngx-datatable';

import { MetricsService } from './metrics.service';
import { UtilitiesService } from '../utilities.service';

import { AppMetric } from '../models/metric/appMetric';
import { WorkflowMetric } from '../models/metric/workflowMetric';

@Component({
	selector: 'metrics-component',
	templateUrl: './metrics.html',
	encapsulation: ViewEncapsulation.None,
	styleUrls: [
		'./metrics.scss',
	],
	providers: [MetricsService],
})

export class MetricsComponent implements OnInit {
    appMetrics: AppMetric[] = [];
    appFilter: string = '';
    workflowMetrics: WorkflowMetric[] = [];
	availableApps: Select2OptionData[] = [];
	appSelectConfig: any;
	recalculateTableCallback: any;

	@ViewChild('appMetricsTable', { static: true }) appMetricsTable: DatatableComponent; 
	@ViewChild('workflowMetricsTable', { static: true }) workflowMetricsTable: DatatableComponent; 

	constructor(
        private metricsService: MetricsService, private toastrService: ToastrService, 
		private utils: UtilitiesService, private cdr: ChangeDetectorRef
	) {}

	ngOnInit(): void {

		this.appSelectConfig = {
			width: '100%',
			placeholder: 'Select an App to view its Metrics',
		};

		this.recalculateTableCallback = (e: any) => {
			this.recalculateTable(e);
		}
		$(document).on('shown.bs.tab', 'a[data-toggle="tab"]', this.recalculateTableCallback)

		this.getAppMetrics();
		this.getWorkflowMetrics();
	}

	/**
	 * Closes our SSEs on component destroy.
	 */
	ngOnDestroy(): void {
		if (this.recalculateTableCallback) { $(document).off('shown.bs.tab', 'a[data-toggle="tab"]', this.recalculateTableCallback); }
	}

	/**
	 * This angular function is used primarily to recalculate column widths for execution results table.
	 */
	recalculateTable(event: any) : void {
		let table: DatatableComponent;
		switch(event.target.getAttribute('href')) {
			case '#apps':
				table = this.appMetricsTable;
				break;
			case '#workflows':
				table = this.workflowMetricsTable;
		}
		if (table && table.recalculate) {
			this.cdr.detectChanges();
			if (Array.isArray(table.rows)) table.rows = [...table.rows];
			table.recalculate();
		}
	}
	/**
	 * Grabs case events from the server for the selected case (from the JS event supplied).
	 * Will update the case events data table with the new case events.
	 * @param event JS event from the select2 case select box
	 */
	appSelectChange(event: any): void {
		if (!event.value || event.value === '') { 
            this.appFilter = '';
        }
        else {
            this.appFilter = event.value;
        }
    }
    
    getFilteredAppMetrics(): AppMetric[] {
        if (!this.appFilter || this.appFilter == 'all') return this.appMetrics;
        return this.appMetrics.filter(appMetric => appMetric.name == this.appFilter);
    }

    displayAppMetrics(): object[] {
        let metrics: object[] = [];
        this.getFilteredAppMetrics().forEach(appMetric => {
            appMetric.actions.forEach(actionMetric => {
                metrics.push({
                    app: appMetric.name,
                    action: actionMetric.name,
                    success: actionMetric.success_metrics.display_text,
                    error: actionMetric.error_metrics.display_text,
                    total_count: actionMetric.success_metrics.count + actionMetric.error_metrics.count
                })
            })
        })
        return metrics;
    }
    
    /**
	 * Grabs all the existing cases in the DB for use in populating the cases datatable.
	 * Will also populate the case select2 data for use on the case events tab.
	 */
	getAppMetrics(): void {
		this.metricsService
			.getAppMetrics()
			.then((appMetrics) => {
				this.appMetrics = appMetrics;
                this.availableApps = [{ id: '', text: '' },{ id: 'all', text: 'All' }].concat(appMetrics.map(m => ({ id: m.name, text: m.name })));
                this.displayAppMetrics();
			})
			.catch(e => this.toastrService.error(`Error retrieving app metrics: ${e.message}`));
    }
    
    /**
	 * Grabs all the existing cases in the DB for use in populating the cases datatable.
	 * Will also populate the case select2 data for use on the case events tab.
	 */
	getWorkflowMetrics(): void {
		this.metricsService
			.getWorkflowMetrics()
			.then((workflowMetrics) => {
				this.workflowMetrics = workflowMetrics;
			})
			.catch(e => this.toastrService.error(`Error retrieving workflow metrics: ${e.message}`));
	}

	/**
	 * Returns a string of concatenated array values.
	 * E.g. ['some', 'text', 'here'] => 'some, text, here'
	 * @param input Array of strings to concat into a friendly string
	 */
	getFriendlyArray(input: string[]): string {
		return input.join(', ');
	}

	/**
	 * Converts an input object to a JSON string, removing the quotes for better reading.
	 * @param input Input object to convert
	 */
	getFriendlyObject(input: object): string {
		let out = JSON.stringify(input, null, 1);
		out = out.substr(1, out.length - 2).replace(/"/g, '');
		return out;
	}

}
