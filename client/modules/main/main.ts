import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule }   from '@angular/forms';
import { HttpModule } from '@angular/http';

// Custom routing module
import { RoutingModule } from '../routing';

import { MainComponent } from '../../components/main/main';
import { ControllerComponent } from '../../components/controller/controller';

@NgModule({
	imports: [
		BrowserModule,
		FormsModule,
		HttpModule,
		RoutingModule,
	],
	declarations: [
		MainComponent,
		ControllerComponent,
	],
	bootstrap: [MainComponent]
})
export class MainModule { }

platformBrowserDynamic().bootstrapModule(MainModule);