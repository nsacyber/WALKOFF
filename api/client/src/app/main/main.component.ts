import { Component, OnInit, OnDestroy } from '@angular/core';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';

import { MainService } from './main.service';
import { AuthService } from '../auth/auth.service';
import { UtilitiesService } from '../utilities.service';

import { ReportService } from '../reports/report.service';
import { Report } from '../models/report/report';

import { MainProfileModalComponent } from './main.profile.modal.component';
import { ClipboardService } from 'ngx-clipboard';

@Component({
	selector: 'main-component',
	templateUrl: './main.html',
	styleUrls: [
		'./main.scss',
	],
	providers: [MainService, AuthService, UtilitiesService],
})
export class MainComponent implements OnInit, OnDestroy {
	currentUser: string;
	reports: Report[] = [];

	constructor(
		private authService: AuthService, private modalService: NgbModal, 
		private toastrService: ToastrService, public utils: UtilitiesService, 
		private reportService: ReportService, private clipboardService: ClipboardService
	) {

		const hideBackdrop = () => {
			const backdropNodes = document.querySelectorAll('.modal-backdrop');
			backdropNodes.item(backdropNodes.length - 1).classList.remove('show');

			const modalNodes = document.querySelectorAll('.modal.show')
			modalNodes.item(modalNodes.length - 1).classList.remove('show');
		}

		/* Hack along with styles.scss for modal animations in ng-bootstrap */
		NgbModalRef.prototype['c'] = NgbModalRef.prototype.close;
        NgbModalRef.prototype.close = function (reason: string) {
			hideBackdrop();
            setTimeout(() => this['c'](reason), 250);
        };
        NgbModalRef.prototype['d'] = NgbModalRef.prototype.dismiss;
        NgbModalRef.prototype.dismiss = function (reason: string) {
			hideBackdrop();
            setTimeout(() => this['d'](reason), 250);
		};
		
		this.clipboardService.copyResponse$.subscribe(res => {
			if (res.isSuccess) this.toastrService.success('Copied to Clipboard');
		})
	}

	/**
	 * On init, set the current user from our JWT.
	 * Get a list of interface names that are installed. Get initial notifications for display.
	 * Set up an SSE for handling new notifications.
	 */
	ngOnInit(): void {
		this.currentUser = this.authService.getAndDecodeAccessToken().user_claims.username;
		this.reportService.reportsChange.subscribe(reports => this.reports = reports);
	}

	/**
	 * Closes our SSEs on component destroy.
	 */
	ngOnDestroy(): void {}

	/**
	 * Edit User Profile Modal 
	 */
	editUser() {
		const modalRef = this.modalService.open(MainProfileModalComponent);
		modalRef.componentInstance.username = this.currentUser;
		modalRef.result.then(username => {
			this.currentUser = username;
			this.toastrService.success('Updated Profile')
		}, () => null)
		return false;
	}
}
