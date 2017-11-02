import { ActionApi } from './actionApi';
import { ConditionApi } from './conditionApi';
import { TransformApi } from './transformApi';

export class AppApi {
	name: string;
	actionApis: ActionApi[];
	conditionApis: ConditionApi[];
	transformApis: TransformApi[];
}