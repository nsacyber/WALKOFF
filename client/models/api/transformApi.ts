import { ParameterApi } from './parameterApi';

export class TransformApi {
	name: string;
	description: string;
	parameters: ParameterApi[] = [];
	run: string;
	dataIn: string;
	deprecated: boolean;
	// tags: Tag[] = [];
	summary: string;
	// externalDocs: ExternalDoc[] = [];
}
