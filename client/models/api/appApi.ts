import { ActionApi } from './actionApi';
import { ConditionApi } from './conditionApi';
import { TransformApi } from './transformApi';
import { DeviceApi } from './deviceApi';

export class AppApi {
	name: string;
	actions: ActionApi[] = [];
	conditions: ConditionApi[] = [];
	transforms: TransformApi[] = [];
	devices: DeviceApi[] = [];
	// info: AppInfo;
	// tags: Tag[] = [];
	// externalDocs: ExternalDoc[] = [];
}