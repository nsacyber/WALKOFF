import { Type } from 'class-transformer';

import { InterfaceWidget, 
         BarChartWidget, 
         PieChartWidget, 
         LineChartWidget,  
         TextWidget,
         TableWidget,
         KibanaWidget
} from "./interfaceWidget";

import { UUID } from 'angular2-uuid';

export class Interface {

    id: string;

    name: string;

    @Type(() => InterfaceWidget, {
        discriminator: {
            property: "type",
            subTypes: [
                { value: BarChartWidget, name: "bar" },
                { value: PieChartWidget, name: "pie" },
                { value: LineChartWidget, name: "line" },
                { value: TextWidget, name: "text" },
                { value: TableWidget, name: "table" },
                { value: KibanaWidget, name: "kibana" },
            ]
        }
    })
    widgets: InterfaceWidget[] = []; 

    constructor() { 
        this.id = UUID.UUID();
    }
}
