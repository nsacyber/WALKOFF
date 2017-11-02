import { ParameterApi } from './parameterApi';
import { ReturnApi } from './returnApi';

export class ConditionApi {
	name: string;
	description: string;
	parameters: ParameterApi[] = [];
	returns: ReturnApi[] = [];
	run: string;
	dataIn: string;
	deprecated: boolean;
	// tags: Tag[] = [];
	summary: string;
	// externalDocs: ExternalDoc[] = [];
}