import { Injectable } from '@angular/core';
import { plainToClass, classToPlain, serialize, deserializeArray } from 'class-transformer';
import { UtilitiesService } from '../utilities.service';
import { Interface } from '../models/interface/interface';


@Injectable({
    providedIn: 'root'
})
export class InterfaceService {

    constructor(private utils: UtilitiesService) { }

    saveInterface(newInterface: Interface): void {
        const interfaces: Interface[] = this.getInterfaces();
        const index = interfaces.findIndex(item => item.id == newInterface.id);

        if (index == -1) interfaces.push(newInterface);
        else interfaces[index] = newInterface;

        localStorage.setItem('interfaces', serialize(interfaces));
    }

    deleteInterface(deletedInterface: Interface): void {
        const interfaces: Interface[] = this.getInterfaces().filter(item => item.id != deletedInterface.id);
        localStorage.setItem('interfaces', serialize(interfaces));
    }

    getInterfaces() : Interface[] {
        return deserializeArray(Interface, localStorage.getItem('interfaces')) || [];
    }

    getInterface(name: string) : Interface {
        return this.getInterfaces().find(item => item.name == name);
    }
}
