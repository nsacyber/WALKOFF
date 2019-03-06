import { Exclude } from 'class-transformer';

export abstract class InterfaceWidget {
    type = 'bar';

    options: any = {};

    @Exclude()
    metadata: any = {};

    constructor(
        public title: string = '', 
        public x = 0, 
        public y = 0, 
        public cols = 4, 
        public rows = 4,
    ) { }

    setMetadata(results: any) {
        this.metadata = results;
    }
}

export abstract class ChartWidget extends InterfaceWidget {
    chartLabels: string[];
    chartData: any[];
    chartOptions: any = {
        scaleShowVerticalLines: false,
        responsive: true
    };

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
    type = 'bar';

    chartLabels: string[] = ['192.168.1.105', '192.168.1.103', '192.168.1.102', '192.168.1.104', '192.168.1.1', 'fe80::219:e3ff:fee7:5d23', 'fe80::2c23:b96c:78d:e116', '169.254.225.22', '0.0.0.0', '255.255.255.255'];

    chartData: any[] = [
        { data: [951, 914, 896, 81, 427, 35, 34, 28, 4, 1, 1], label: 'Yesterday' },
        { data: [560, 800, 1200, 43, 500, 80, 25, 50, 10, 0, 0], label: 'Today' },
    ];
}

export class PieChartWidget  extends ChartWidget {
    type = 'pie';

    chartLabels: string[] = ['UDP', 'TCP', 'ICMP'];

    chartData: number[] = [1881, 1408, 2];

    setMetadata(results: any) {
        this.metadata = {
            chartLabels: results.headers,
            chartData: results.rows[0]
        }
    }
}

export class LineChartWidget  extends ChartWidget {
    type = 'line';

    chartLabels: string[] = ['80', '53', '138', '137', '67', '5353', '443', '547', '995', '37'];

    chartData: any[] = [
        { data: [1316, 1271, 270, 159, 71, 68, 44, 17, 17, 16], label: 'Count' },
    ];
}

export class TableWidget extends InterfaceWidget {
    type = 'table';
    
    setMetadata(results: any) {
        const columns = results.headers.map(h => ({prop: h}))

        this.metadata = {
            columns,
            rows: results.data
        }
    }
}

export class TextWidget  extends InterfaceWidget {
    type = 'text';
}

export class KibanaWidget  extends InterfaceWidget {
    type = 'kibana';
}
