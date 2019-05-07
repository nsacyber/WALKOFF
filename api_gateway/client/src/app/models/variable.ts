import { UUID } from 'angular2-uuid';
import { Expose, classToClass } from 'class-transformer';

export class Variable {

    @Expose({ name: "id_" })
    id: string;
    
    name: string;
    
    value: string;

    description?: string;
    
    constructor() {
        this.id = UUID.UUID();
    }

    clone() {
        return classToClass(this, { ignoreDecorators: true });
    }
}
