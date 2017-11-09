import { ParameterApi } from './parameterApi';

export class TransformApi {
	name: string;
	description: string;
	parameters: ParameterApi[] = [];
	run: string;
	data_in: string;
	deprecated: boolean;
	// tags: Tag[] = [];
	summary: string;
	// external_docs: ExternalDoc[] = [];
}
