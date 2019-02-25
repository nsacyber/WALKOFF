import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { LoginComponent } from './login.component';

@NgModule({
	imports: [BrowserModule],
	declarations: [LoginComponent],
	bootstrap: [LoginComponent],
})
export class LoginModule { }
