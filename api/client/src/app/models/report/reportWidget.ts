import { Exclude, Expose } from 'class-transformer';

export abstract class ReportWidget {

    @Expose({ name: "id_" })
    id: string;

    type_ = 'text';

    name: string = "";

    options: any = {};

    @Exclude()
    metadata: any = {};

    @Exclude()
    dashboard: string;

    constructor(
        public x = 0, 
        public y = 0, 
        public cols = 4, 
        public rows = 4,
    ) { }

    get type(): string {
        return this.type_;
    }

    setMetadata(results: any) {
        this.metadata = results;
    }
}

export abstract class ChartWidget extends ReportWidget {
    @Exclude()
    chartLabels: string[];

    @Exclude()
    chartData: any[];

    @Exclude()
    chartOptions: any = {
        scaleShowVerticalLines: false,
        responsive: true
    };

    @Exclude()
    showLegend: boolean = false;

    setMetadata(results: any) {
        this.metadata = {
            chartLabels: results.headers,
            chartData: [{
                data: results.rows[0],
                label: (this.options.units) ? this.options.units : 'Count'
            }]
        }
    }
}

export class BarChartWidget extends ChartWidget {
    type_ = 'bar';

    @Exclude()
    chartLabels: string[] = ['192.168.1.105', '192.168.1.103', '192.168.1.102', '192.168.1.104', '192.168.1.1', 'fe80::219:e3ff:fee7:5d23', 'fe80::2c23:b96c:78d:e116', '169.254.225.22', '0.0.0.0', '255.255.255.255'];

    @Exclude()
    chartData: any[] = [
        { data: [951, 914, 896, 81, 427, 35, 34, 28, 4, 1, 1], label: 'Yesterday' },
        { data: [560, 800, 1200, 43, 500, 80, 25, 50, 10, 0, 0], label: 'Today' },
    ];
}

export class PieChartWidget  extends ChartWidget {
    type_ = 'pie';

    @Exclude()
    chartLabels: string[] = ['UDP', 'TCP', 'ICMP'];

    @Exclude()
    chartData: number[] = [1881, 1408, 2];

    setMetadata(results: any) {
        this.metadata = {
            chartLabels: results.headers,
            chartData: results.rows[0]
        }
    }
}

export class LineChartWidget  extends ChartWidget {
    type_ = 'line';

    @Exclude()
    chartLabels: string[] = ['80', '53', '138', '137', '67', '5353', '443', '547', '995', '37'];

    @Exclude()
    chartData: any[] = [
        { data: [1316, 1271, 270, 159, 71, 68, 44, 17, 17, 16], label: 'Count' },
    ];
}

export class TableWidget extends ReportWidget {
    type_ = 'table';
    
    setMetadata(results: any) {
        const columns = results.headers.map(h => ({prop: h}))

        this.metadata = {
            columns,
            rows: results.data
        }
    }
}

export class TextWidget  extends ReportWidget {
    type_ = 'text';
}

export class KibanaWidget  extends ReportWidget {
    type_ = 'kibana';
}
