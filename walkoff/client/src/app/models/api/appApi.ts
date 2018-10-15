import { Type } from 'class-transformer';

import { ActionApi } from './actionApi';
import { ConditionApi } from './conditionApi';
import { TransformApi } from './transformApi';
import { DeviceApi } from './deviceApi';

export class AppApi {
	name: string;

	@Type(() => ActionApi)
	action_apis?: ActionApi[] = [];

	@Type(() => ConditionApi)
	condition_apis?: ConditionApi[] = [];

	@Type(() => TransformApi)
	transform_apis?: TransformApi[] = [];

	@Type(() => DeviceApi)
	device_apis?: DeviceApi[] = [];

	getFilteredActionApis(searchTerm: string) : ActionApi[] {
		searchTerm = searchTerm.trim().toLowerCase();
		return (searchTerm) ? 
			this.action_apis.filter(api => api.name.toLowerCase().includes(searchTerm) || this.name.toLowerCase().includes(searchTerm)) :
			this.action_apis;
	}

	// info: AppInfo;

	// tags: Tag[] = [];

	// external_docs: ExternalDoc[] = [];
}
