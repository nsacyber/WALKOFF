import { Injectable } from '@angular/core';
import { plainToClass, classToPlain, serialize, deserializeArray } from 'class-transformer';
import { UtilitiesService } from '../utilities.service';
import { HttpClient } from '@angular/common/http';
import { Report } from '../models/report/report';
import { ExecutionService } from '../execution/execution.service';
import { ReportWidget } from '../models/report/reportWidget';
import { WorkflowStatus } from '../models/execution/workflowStatus';

import * as csv from 'csvtojson';
import { Observable, Subscriber } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class ReportService {

    reportsChange: Observable<any>;
    observer: Subscriber<any>;

    constructor(private http: HttpClient, private utils: UtilitiesService, private executionService: ExecutionService) {
        this.reportsChange = new Observable((observer) => {
            this.observer = observer;
            this.getReports().then(reports => this.observer.next(reports));
        })
    }

    emitChange(data: any) {
        if (this.observer) this.getReports().then(reports => this.observer.next(reports));
        return data;
    }

    newReport(report: Report) {
        return this.http.post('api/dashboards/', classToPlain(report))
            .toPromise()
            .then((data) => this.emitChange(data))
			.then((data: object) => plainToClass(Report, data))
            .catch(this.utils.handleResponseError)
    }

    updateReport(report: Report) {
        return this.http.put(`api/dashboards/${ report.id }`, classToPlain(report))
            .toPromise()
            .then((data) => this.emitChange(data))
			.then((data: object) => plainToClass(Report, data))
			.catch(this.utils.handleResponseError);
    }

    deleteReport(report: Report) {
        return this.http.delete(`api/dashboards/${ report.id }`)
            .toPromise()
            .then((data) => this.emitChange(data))
            .catch(this.utils.handleResponseError);
    }

    getReports() : Promise<Report[]> {
        return this.http.get('api/dashboards/')
			.toPromise()
			.then((data) => plainToClass(Report, data))
            .catch(this.utils.handleResponseError);
    }

    getReport(id: string) : Promise<Report> {
        return this.http.get(`api/dashboards/${ id }`)
			.toPromise()
			.then((data: object) => plainToClass(Report, data))
			.catch(this.utils.handleResponseError);
    }

    async getReportWithMetadata(id: string) : Promise<Report> {
        const theReport: Report = await this.getReport(id);
        await Promise.all(theReport.widgets.map(widget => this.getWidgetMetadata(widget)));
        return theReport;
    }

    async getWidgetMetadata(widget: ReportWidget) {
        // const testData = "A,B,C\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6";
        // return widget.setMetadata(await this.parseResult(testData))

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
