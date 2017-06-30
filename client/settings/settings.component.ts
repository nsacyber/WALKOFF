import { Component } from '@angular/core';
import * as _ from 'lodash';

import { SettingsService } from './settings.service';

import { Configuration } from './configuration';

@Component({
	selector: 'settings-component',
	templateUrl: 'client/settings/settings.html',
	styleUrls: [
		'client/settings/settings.css',
	],
	providers: [SettingsService]
})
export class SettingsComponent {
	configuration: Configuration;

	constructor(private settingsService: SettingsService) {
		this.configuration = new Configuration();
		console.log(this.configuration);
		console.log(_.VERSION);
		this.getConfiguration();
	}

	getConfiguration(): void {
		this.settingsService
			.getConfiguration()
			.then(configuration => this.configuration = configuration);
	}

	updateConfiguration(): void {
		this.settingsService
			.updateConfiguration(this.configuration)
			.then(configuration => this.configuration = configuration);
	}
	
	//TODO: add some sort of a confirm dialog
	resetConfiguration(): void {
		let defaultConfig = new Configuration();

		_.assign(this.configuration, defaultConfig);

		console.log(this.configuration);
	}
}