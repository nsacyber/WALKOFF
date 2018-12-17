export class InterfaceWidget {
    type = 'bar';

    constructor(
        public label: string = 'Interface Widget', 
        public x = 0, 
        public y = 0, 
        public cols = 4, 
        public rows = 4
    ) { }
}

export class PieChartWidget  extends InterfaceWidget {
    type = 'pie';
}

export class LineChartWidget  extends InterfaceWidget {
    type = 'line';
}

export class TextWidget  extends InterfaceWidget {
    type = 'text';
    text: String;
}

export class KibanaWidget  extends InterfaceWidget {
    type = 'kibana';
}
