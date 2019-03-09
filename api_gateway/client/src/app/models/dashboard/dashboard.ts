import { Type, Expose } from 'class-transformer';

import { DashboardWidget, 
         BarChartWidget, 
         PieChartWidget, 
         LineChartWidget,  
         TextWidget,
         TableWidget,
         KibanaWidget
} from "./dashboardWidget";

import { UUID } from 'angular2-uuid';

export class Dashboard {

    @Expose({ name: "id_" })
    id: string;

    name: string;

    @Type(() => DashboardWidget, {
        keepDiscriminatorProperty: true,
        discriminator: {
            property: "type_",
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
    widgets: DashboardWidget[] = []; 

    constructor() { 
        this.id = UUID.UUID();
    }
}
