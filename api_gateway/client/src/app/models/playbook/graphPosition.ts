import { Expose } from 'class-transformer';

export class GraphPosition {
	@Expose({name: 'id_'})
	id: string;

	x: number;

	y: number;
}
