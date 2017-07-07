import { Component } from '@angular/core';
import _ from 'lodash/lodash.js';

import { SettingsService } from './settings.service';

import { Configuration } from '../models/configuration';

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

	//User Data Table params
	userNames: string[];
	filterQuery: string = "";
	rowsOnPage: number = 10;
	sortBy: string = "username";
	sortOrder: string = "asc";

	constructor(private settingsService: SettingsService) {
		this.getConfiguration();
	}

	getConfiguration(): void {
		this.settingsService
			.getConfiguration()
			.then(configuration => this.configuration = configuration)
			.catch(e => this.configuration = Configuration.getDefaultConfiguration());
	}

	updateConfiguration(): void {
		this.settingsService
			.updateConfiguration(this.configuration)
			.then(configuration => this.configuration = configuration);
	}

	getUsers(): void {
		this.settingsService
			.getUserNames()
			.then(userNames => this.userNames = userNames);
	}

	addUser(): void {

	}
	
	//TODO: add a better confirm dialog
	resetConfiguration(): void {
		if (!confirm("Are you sure you want to reset the configuration? Note that you'll have to save the configuration after reset to update it on the server.")) return; 

		let defaultConfig = new Configuration();

		_.assign(this.configuration, defaultConfig);

		console.log(this.configuration);
	}
}


// @Component({
//   	selector: 'user-modal',
// 	templateUrl: 'client/settings/settings.user.modal.html',
// 	// styleUrls: [
// 	// 	'client/settings/settings.user.modal.css',
// 	// ],
// 	// providers: [SettingsService]
// })
// export class UserModalComponent {
// 	public visible = false;
// 	public visibleAnimate = false;

// 	public show(): void {
// 		this.visible = true;
// 		setTimeout(() => this.visibleAnimate = true, 100);
// 	}

// 	public hide(): void {
// 		this.visibleAnimate = false;
// 		setTimeout(() => this.visible = false, 300);
// 	}

// 	public validate(): void {
		
// 	}

// 	public onContainerClicked(event: MouseEvent): void {
// 		if ((<HTMLElement>event.target).classList.contains('modal')) {
// 		this.hide();
// 		}
// 	}
// }