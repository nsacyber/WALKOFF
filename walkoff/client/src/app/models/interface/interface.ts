import { InterfaceWidget } from "./interfaceWidget";
import { UUID } from 'angular2-uuid';

export class Interface {

    id: string;

    name: string;

    widgets: InterfaceWidget[] = []; 

    constructor() { 
        this.id = UUID.UUID();
    }
}
