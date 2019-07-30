import { Injectable } from '@angular/core';
import { plainToClass, classToPlain, serialize, deserializeArray } from 'class-transformer';
import { UtilitiesService } from '../utilities.service';
import { HttpClient } from '@angular/common/http';
import { Dashboard } from '../models/dashboard/dashboard';
import { ExecutionService } from '../execution/execution.service';
import { DashboardWidget } from '../models/dashboard/dashboardWidget';
import { WorkflowStatus } from '../models/execution/workflowStatus';

import * as csv from 'csvtojson';
import { Observable, Subscriber } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class DashboardService {

    dashboardsChange: Observable<any>;
    observer: Subscriber<any>;

    constructor(private http: HttpClient, private utils: UtilitiesService, private executionService: ExecutionService) {
        this.dashboardsChange = new Observable((observer) => {
            this.observer = observer;
            this.getDashboards().then(dashboards => this.observer.next(dashboards));
        })
    }

    emitChange(data: any) {
        if (this.observer) this.getDashboards().then(dashboards => this.observer.next(dashboards));
        return data;
    }

    newDashboard(dashboard: Dashboard) {
        return this.http.post('api/dashboards', classToPlain(dashboard))
            .toPromise()
            .then((data) => this.emitChange(data))
			.then((data: object) => plainToClass(Dashboard, data))
            .catch(this.utils.handleResponseError)
    }

    updateDashboard(dashboard: Dashboard) {
        return this.http.put('api/dashboards', classToPlain(dashboard))
            .toPromise()
            .then((data) => this.emitChange(data))
			.then((data: object) => plainToClass(Dashboard, data))
			.catch(this.utils.handleResponseError);
    }

    deleteDashboard(dashboard: Dashboard) {
        return this.http.delete(`api/dashboards/${ dashboard.id }`)
            .toPromise()
            .then((data) => this.emitChange(data))
            .catch(this.utils.handleResponseError);
    }

    getDashboards() : Promise<Dashboard[]> {
        return this.http.get('api/dashboards')
			.toPromise()
			.then((data) => plainToClass(Dashboard, data))
            .catch(this.utils.handleResponseError);
    }

    getDashboard(id: string) : Promise<Dashboard> {
        return this.http.get(`api/dashboards/${ id }`)
			.toPromise()
			.then((data: object) => plainToClass(Dashboard, data))
			.catch(this.utils.handleResponseError);
    }

    async getDashboardWithMetadata(id: string) : Promise<Dashboard> {
        const theDashboard: Dashboard = await this.getDashboard(id);
        await Promise.all(theDashboard.widgets.map(widget => this.getWidgetMetadata(widget)));
        return theDashboard;
    }

    async getWidgetMetadata(widget: DashboardWidget) {
        const testData = "A,B,C\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6";
        return widget.setMetadata(await this.parseResult(testData))

        const options = widget.options;
        if (options.workflow && options.execution && options.action) {
            const workflowStatus: WorkflowStatus = (options.execution == "latest") ?
                await this.executionService.getLatestExecution(options.workflow) :
                await this.executionService.getWorkflowStatus(options.execution)

            const nodeStatus = workflowStatus.node_statuses.find(status => status.node_id == options.action);
            if (nodeStatus) widget.setMetadata(await this.parseResult(nodeStatus.result));
        }
    }

    async parseResult(result) {
        let headers = [];
        return csv()
            .fromString(result)
            .on('header', row => headers = row)
            .then(data => ({
                headers,
                rows: data.map(Object.values),
                data
            }), err => {
                console.log(err);
                return result
            })
    }
}
