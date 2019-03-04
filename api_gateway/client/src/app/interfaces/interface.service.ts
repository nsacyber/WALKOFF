import { Injectable } from '@angular/core';
import { plainToClass, classToPlain, serialize, deserializeArray } from 'class-transformer';
import { UtilitiesService } from '../utilities.service';
import { Interface } from '../models/interface/interface';
import { ExecutionService } from '../execution/execution.service';
import { InterfaceWidget } from '../models/interface/interfaceWidget';
import { WorkflowStatus } from '../models/execution/workflowStatus';

import * as csv from 'csvtojson';

@Injectable({
    providedIn: 'root'
})
export class InterfaceService {

    constructor(private utils: UtilitiesService, private executionService: ExecutionService) { }

    saveInterface(newInterface: Interface): void {
        const interfaces: Interface[] = this.getInterfaces();
        const index = interfaces.findIndex(item => item.id == newInterface.id);

        if (index == -1) interfaces.push(newInterface);
        else interfaces[index] = newInterface;

        localStorage.setItem('interfaces', serialize(interfaces));
    }

    deleteInterface(deletedInterface: Interface): void {
        const interfaces: Interface[] = this.getInterfaces().filter(item => item.id != deletedInterface.id);
        localStorage.setItem('interfaces', serialize(interfaces));
    }

    getInterfaces() : Interface[] {
        return deserializeArray(Interface, localStorage.getItem('interfaces')) || [];
    }

    getInterface(name: string) : Interface {
        return this.getInterfaces().find(item => item.name == name);
    }

    async getInterfaceWithMetadata(name: string) : Promise<Interface> {
        const theInterface: Interface = this.getInterface(name);
        await Promise.all(theInterface.widgets.map(widget => this.getWidgetMetadata(widget)));
        return theInterface;
    }

    async getWidgetMetadata(widget: InterfaceWidget) {
        const options = widget.options;
        if (options.workflow && options.execution && options.action) {         
            const workflowStatus: WorkflowStatus = (options.execution == "latest") ?
                await this.executionService.getLatestExecution(options.workflow) :
                await this.executionService.getWorkflowStatus(options.execution)

            const actionStatus = workflowStatus.action_statuses.find(status => status.action_id == options.action);
            if (actionStatus) widget.setMetadata(await this.parseResult(actionStatus.result));
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
