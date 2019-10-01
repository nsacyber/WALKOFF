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
    sseErrorTimeout: any;
    consoleLog: any[] = [];
    statusObserver: Observer<any>;
    statusSubscription: Subscription;
    completedStatus: { success: boolean, message: string};

    constructor(public activeModal: NgbActiveModal, public appService: AppService, public utils: UtilitiesService,
        public toastrService: ToastrService, public authService: AuthService) { }

    ngOnInit(): void {
        this.getSSE();

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

    ngOnDestroy(): void {}

    cleanUp() {
        if (this.statusEventSource && this.statusEventSource.close) { this.statusEventSource.close(); }
    }

    getSSE() {
        if (this.statusEventSource) this.statusEventSource.close();
        return this.authService.getEventSource(`api/streams/build/build_log?build_id=${this.buildId}`)
            .then(eventSource => {
                this.statusEventSource = eventSource;
                this.statusEventSource.onerror = (e: any) => this.statusEventErrorHandler(e);
                this.statusEventSource.addEventListener('log', (e: any) => this.statusEventHandler(e));
            });
    }

    statusEventHandler(message: any): void {
        if (this.sseErrorTimeout) {
            clearTimeout(this.sseErrorTimeout);
            delete this.sseErrorTimeout;
        }

        console.log('c', message);
        const consoleEvent = JSON.parse(message.data); //plainToClass(ConsoleLog, (JSON.parse(message.data) as object));

        switch (consoleEvent.build_status) {
            case 'building':
                this.consoleLog.push(consoleEvent);
                break;
            case 'failure':
                this.consoleLog.push(consoleEvent);
                this.completedStatus = { success: false, message: `<b class="text-capitalize">${this.appApi.name}</b> rebuild failed`};
                break;
            case 'Success':
                this.completedStatus = { success: true, message: `<b class="text-capitalize">${this.appApi.name}</b> rebuild successful`};
        }
        this.statusObserver.next(this.consoleContent);
    }

    statusEventErrorHandler(e: any) {
        console.log(e);
        if (this.sseErrorTimeout) return;
        this.sseErrorTimeout = setTimeout(async () => {
            try {
                await this.appService.getApis();
                delete this.sseErrorTimeout;
            }
            catch (e) {
                this.cleanUp();
                const options = { backdrop: undefined, closeButton: false, buttons: { ok: { label: 'Reload Page' } } }
                this.utils.alert('The server stopped responding. Reload the page to try again.', options)
                    .then(() => location.reload(true))
            }
        }, 5 * 1000)
    }

    get consoleContent() {
        return `Building ${this.appApi.name}...\n` + this.consoleLog.map(log => log.stream).join('\n');
    }
}