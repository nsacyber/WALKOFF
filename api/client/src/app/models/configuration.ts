export class Configuration {

	static getDefaultConfiguration(): Configuration {
		return {
			access_token_duration: 15,
			refresh_token_duration: 30
		};
	}

	access_token_duration: number; //in minutes

	refresh_token_duration: number; //in days
}
