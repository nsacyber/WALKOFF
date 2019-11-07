import { Type, Expose, classToClass } from 'class-transformer';

import { ReportWidget, 
         BarChartWidget, 
         PieChartWidget, 
         LineChartWidget,  
         TextWidget,
         TableWidget,
         KibanaWidget
} from "./reportWidget";

import { UUID } from 'angular2-uuid';

export class Report {

    @Expose({ name: "id_" })
    id: string;

    name: string;

    @Type(() => ReportWidget, {
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
    widgets: ReportWidget[] = []; 

    constructor() { 
        this.id = UUID.UUID();
    }

    clone() {
		return classToClass(this, { ignoreDecorators: true });
	}
}
