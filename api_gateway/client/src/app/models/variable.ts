import { UUID } from 'angular2-uuid';
import { Expose } from 'class-transformer';

export class Variable {

    @Expose({ name: "id_" })
    id: string;
    
    name: string;
    
    value: string;

    description?: string;
    
    constructor() {
        this.id = UUID.UUID();
    }
    
}
