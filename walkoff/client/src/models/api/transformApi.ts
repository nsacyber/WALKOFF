import { ParameterApi } from './parameterApi';
import { ReturnApi } from './returnApi';

export class TransformApi {
	name: string;
	description: string;
	parameters: ParameterApi[] = [];
	returns: ReturnApi[] = [];
	run: string;
	data_in: string;
	deprecated: boolean;
	// tags: Tag[] = [];
	summary: string;
	// external_docs: ExternalDoc[] = [];
}
