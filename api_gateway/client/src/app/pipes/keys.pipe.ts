import { PipeTransform, Pipe } from '@angular/core';

@Pipe({ name: 'keys', pure: false })
export class KeysPipe implements PipeTransform {
	transform(value: object, args: string[]): any {
		const keys: string[] = [];
		for (const key in value) {
			if (value.hasOwnProperty(key)) { keys.push(key); }
		}
		return keys;
	}
}
