import { UUID } from 'angular2-uuid';

export class EnvironmentVariable {

    id: string;
    
    name: string;
    
    value: string;

    description?: string;
    
    constructor() {
        this.id = UUID.UUID();
    }
}
