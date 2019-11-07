import { Component, Input, ViewChild, ViewEncapsulation, OnInit, OnDestroy } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';
import { AppService } from './app.service';
import { AuthService } from '../auth/auth.service';
import { CodemirrorComponent } from '@ctrl/ngx-codemirror';
import { Observable, Observer, zip, interval, Subscription } from 'rxjs';
import { takeWhile, finalize } from 'rxjs/operators';

import { AppApi } from '../models/api/appApi';
import { UtilitiesService } from '../utilities.service';

@Component({
    selector: 'status-modal-component',
    templateUrl: './status.modal.html',
    styleUrls: [
        './status.modal.scss',
    ],
    encapsulation: ViewEncapsulation.None,
})
export class StatusModalComponent implements OnInit, OnDestroy {
    @ViewChild('consoleArea', { static: false }) consoleArea: CodemirrorComponent;
    @Input() buildId: string;
    @Input() appApi: AppApi;
    statusEventSource: any;
    consoleLog: any[] = [];
    statusObserver: Observer<any>;
    statusSubscription: Subscription;
    completedStatus: { success: boolean, message: string};
    buildStatusSocket: SocketIOClient.Socket;

    constructor(public activeModal: NgbActiveModal, public appService: AppService, public utils: UtilitiesService,
        public toastrService: ToastrService, public authService: AuthService) { }

    ngOnInit(): void {
        this.createBuildStatusSocket();

        const observable = new Observable<string>((observer) => this.statusObserver = observer);
        this.statusSubscription = zip(observable, interval(100), (a, b) => a)
            .pipe(
                takeWhile((i) => !this.completedStatus || this.consoleContent.localeCompare(i) != 0, true),
                finalize(() => {
                    (this.completedStatus.success) ?
                        this.toastrService.success(this.completedStatus.message) :
                        this.toastrService.error(this.completedStatus.message)
                    this.cleanUp();
                })
            )
            .subscribe(i => {
                const cm = this.consoleArea.codeMirror;
                const $scroller = $(cm.getScrollerElement());
                const atBottom = $scroller[0].scrollHeight - $scroller.scrollTop() - $scroller.outerHeight() <= 0;
                cm.getDoc().setValue(i);
                cm.refresh();
                if (atBottom) cm.execCommand('goDocEnd');
            });
        this.statusObserver.next(this.consoleContent);
    }

    ngOnDestroy(): void {
        this.cleanUp();
    }

    cleanUp() {
        if (this.buildStatusSocket && this.buildStatusSocket.close) { this.buildStatusSocket.close(); }
    }

    createBuildStatusSocket() {
		if (this.buildStatusSocket) this.buildStatusSocket.close();
		this.buildStatusSocket = this.utils.createSocket('/buildStatus', this.buildId);

		this.buildStatusSocket.on('connected', (data) => {
			(data as any[]).forEach(event => this.statusEventHandler(event));
		});

		this.buildStatusSocket.on('log', (data) => {
			this.statusEventHandler(data)
		});
	}

    statusEventHandler(consoleEvent: any): void {
        console.log('build', consoleEvent);

        switch (consoleEvent.build_status) {
            case 'building':
                this.consoleLog.push(consoleEvent);
                break;
            case 'failure':
                this.consoleLog.push(consoleEvent);
                this.completedStatus = { success: false, message: `<b class="text-capitalize">${this.appApi.name}</b> rebuild failed`};
                break;
            case 'success':
                this.completedStatus = { success: true, message: `<b class="text-capitalize">${this.appApi.name}</b> rebuild successful`};
        }
        this.statusObserver.next(this.consoleContent);
    }

    get consoleContent() {
        return `Building ${this.appApi.name}...\n` + this.consoleLog.map(log => log.stream).join('\n');
    }
}