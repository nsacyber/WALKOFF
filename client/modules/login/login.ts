import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { LoginComponent } from '../../components/login/login';

@NgModule({
  imports: [BrowserModule],
  declarations: [LoginComponent],
  bootstrap: [LoginComponent]
})
export class LoginModule { }