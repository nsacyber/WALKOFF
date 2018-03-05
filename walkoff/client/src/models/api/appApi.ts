import { ActionApi } from './actionApi';
import { ConditionApi } from './conditionApi';
import { TransformApi } from './transformApi';
import { DeviceApi } from './deviceApi';

export class AppApi {
	name: string;
	action_apis?: ActionApi[] = [];
	condition_apis?: ConditionApi[] = [];
	transform_apis?: TransformApi[] = [];
	device_apis?: DeviceApi[] = [];
	// info: AppInfo;
	// tags: Tag[] = [];
	// external_docs: ExternalDoc[] = [];
}
