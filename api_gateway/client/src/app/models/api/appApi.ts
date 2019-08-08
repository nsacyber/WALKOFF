import { Type, Expose } from 'class-transformer';

import { ActionApi } from './actionApi';
import { ConditionApi } from './conditionApi';
import { TransformApi } from './transformApi';
import { DeviceApi } from './deviceApi';

export class AppApi {

	@Expose({ name: 'id_'})
	id: string;

	name: string;

	walkoff_version?: string;

	app_version?: string;

	description?: string;

	contact_info?: {
		name: string,
		url: string,
		email: string
	};

	license_info?: {
		name: string,
		url: string
	};

	tags?: any[];

	external_docs?: any[];


	@Expose({ name: 'actions'})
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
