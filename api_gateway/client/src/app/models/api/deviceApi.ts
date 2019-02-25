import { Type } from 'class-transformer';

import { DeviceFieldApi } from './deviceFieldApi';

export class DeviceApi {
	name: string;

	description: string;

	@Type(() => DeviceFieldApi)
	fields: DeviceFieldApi[] = [];
}
