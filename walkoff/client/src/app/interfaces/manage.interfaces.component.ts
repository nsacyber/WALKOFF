import { Component, OnInit } from '@angular/core';
import { GridsterConfig, GridsterItem, GridType, CompactType } from 'angular-gridster2';
import { InterfaceWidget, PieChartWidget, LineChartWidget, TextWidget, KibanaWidget } from '../models/interface/interfaceWidget';
import { Interface } from '../models/interface/interface';
import { InterfaceService } from './interface.service';
import { ToastrService } from 'ngx-toastr';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { WidgetModalComponent } from './widget.modal.component';

@Component({
    selector: 'manage-interfaces-component',
    templateUrl: './manage.interfaces.component.html',
    styleUrls: ['./manage.interfaces.component.scss']
})
export class ManageInterfacesComponent implements OnInit {

    options: GridsterConfig;

    interface: Interface = new Interface();
    existingInterface = false;

    gridRows = 16;
    gridColumns = 8;
    gridColSize = 75;
    gridGutterSize = 10;
    gridDefaultCols = 3;

    public barChartOptions: any = {
        scaleShowVerticalLines: false,
        responsive: true
    };
    public barChartLabels: string[] = ['192.168.1.105', '192.168.1.103', '192.168.1.102', '192.168.1.104', '192.168.1.1', 'fe80::219:e3ff:fee7:5d23', 'fe80::2c23:b96c:78d:e116', '169.254.225.22', '0.0.0.0', '255.255.255.255'];
    public barChartType: string = 'bar';
    public barChartLegend: boolean = true;

    public barChartData: any[] = [
        { data: [951, 914, 896, 81, 427, 35, 34, 28, 4, 1, 1], label: 'Yesterday' },
        { data: [560, 800, 1200, 43, 500, 80, 25, 50, 10, 0, 0], label: 'Today' },
    ];

    public lineChartOptions: any = {
        scaleShowVerticalLines: false,
        responsive: true
    };
    public lineChartLabels: string[] = ['80', '53', '138', '137', '67', '5353', '443', '547', '995', '37']
    public lineChartType: string = 'line';
    public lineChartLegend: boolean = true;

    public lineChartData: any[] = [
        { data: [1316, 1271, 270, 159, 71, 68, 44, 17, 17, 16], label: 'Count' },
    ];

    // Pie
    public pieChartLabels: string[] = ['UDP', 'TCP', 'ICMP'];
    public pieChartData: number[] = [1881, 1408, 2];
    public pieChartType: string = 'pie';

    constructor(
        private interfaceService: InterfaceService, 
        private toastrService: ToastrService,
        private activeRoute: ActivatedRoute,
        private router: Router,
        private modalService: NgbModal
    ) {}

    ngOnInit() {
        this.activeRoute.params.subscribe(params => {
            if (params.interfaceName) {
                this.existingInterface = true;
                this.interface = this.interfaceService.getInterface(params.interfaceName);
            }
        })

        this.options = {
            itemChangeCallback: ManageInterfacesComponent.itemChange,
            itemResizeCallback: ManageInterfacesComponent.itemResize,
            gridType: GridType.Fixed,
            compactType: CompactType.None,
            pushItems: true,
            draggable: {
                enabled: true
            },
            resizable: {
                enabled: true
            },
            fixedColWidth: this.gridColSize * 4/3,
            fixedRowHeight: this.gridColSize * 3/4,
            minCols: this.gridColumns,
            maxCols: this.gridColumns,
            minRows: 1,
            maxRows: this.gridRows,
            maxItemCols: this.gridColumns,
            minItemCols: 1,
            maxItemRows: this.gridRows,
            minItemRows: 1,
            defaultItemCols: this.gridDefaultCols,
            defaultItemRows: 1
        };
    }

    getGridWidth() {
        return this.gridColumns * Math.ceil(this.gridColSize * 4/3 + this.gridGutterSize) + this.gridGutterSize + 'px';
    }

    getGridHeight() {
        return this.gridRows * Math.ceil(this.gridColSize * 3/4 + this.gridGutterSize) + this.gridGutterSize + 'px';
    }

    changedOptions() {
        this.options.api.optionsChanged();
    }

    removeItem($event: Event, item) {
        console.log(arguments);
        $event.preventDefault();
        this.interface.widgets.splice(this.interface.widgets.indexOf(item), 1);
    }

    addItem() {
        this.interface.widgets.push(new InterfaceWidget());
    }

    addWidget(type: string): void {
        let widget: InterfaceWidget;

        switch (type) {
            case "bar":
                widget = new InterfaceWidget('Top 10 Talkers');
            break;
            case "line":
                widget = new LineChartWidget('Top 10 Remote Ports');
            break;
            case "pie":
                widget = new PieChartWidget('Top Protocols');
            break;
            case "text":
                widget = new TextWidget('');
            break;
            case "kibana":
                widget = new KibanaWidget('Kibana');
            break;
        }

        const modalRef = this.modalService.open(WidgetModalComponent);
		modalRef.componentInstance.widget = widget;
		modalRef.result.then(addedWidget => {
			this.interface.widgets.push(addedWidget);
		}).catch(() => null)
    }
    
    save() {
        if (!this.interface.name) return this.toastrService.error('Enter a name for the interface');
        console.log(this.interfaceService.getInterfaces());
        this.interfaceService.saveInterface(this.interface);
        console.log(this.interfaceService.getInterfaces());
        this.toastrService.success(`"${ this.interface.name }" Saved`);

        this.router.navigate(['/interface', this.interface.name]);
    }

    delete() {
        if(confirm(`Are you sure you want to delete this Interface?`)) {
            const interfaceName = this.interface.name;
            this.interfaceService.deleteInterface(this.interface);
            this.toastrService.success(`"${ interfaceName }" Deleted`);
            this.router.navigate(['/new-interface']);
        }
    }

    static itemChange(item, itemComponent) {
        console.info('itemChanged', item, itemComponent);
    }

    static itemResize(item, itemComponent) {
        console.info('itemResized', item, itemComponent);
    }
}
