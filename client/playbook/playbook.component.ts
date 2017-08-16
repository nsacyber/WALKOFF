import { Component } from '@angular/core';

import { PlaybookService } from './playbook.service';

@Component({
	selector: 'playbook-component',
	templateUrl: 'client/playbook/playbook.html',
	styleUrls: [
        // 'client/node_modules/jstree/dist/themes/default/style.min.css',
        // 'client/node_modules/datatables/media/css/jquery.dataTables.min.css',
		'client/node_modules/jqueryui/jquery-ui.min.css',
		'client/playbook/plugins/cytoscape/cytoscape.js-panzoom.css',
		'client/playbook/playbook.css'
    ],
	providers: [PlaybookService]
})
export class PlaybookComponent {

	constructor(private playbookService: PlaybookService) {
    }

    ngAfterViewInit() {
        let removeScript = () => {
            let indx = 0;
            while (indx < document.body.childNodes.length) {
                if ('localName' in document.body.childNodes[indx]
                    && (document.body.childNodes[indx].localName == 'link'
                    || document.body.childNodes[indx].localName == 'script')) {
                        document.body.removeChild(document.body.childNodes[indx]);
                } else {
                    indx++;
                }
            }
        }

        let addScript = (script: string) => {
            let s = document.createElement("script");
            s.type = "text/javascript";
            s.src = script;
            s.async = false;
            document.body.appendChild(s);
        }

        removeScript();

        // addLink('client/node_modules/jqueryui/jquery-ui.min.css');
        // addLink('client/playbook/plugins/cytoscape/cytoscape.js-panzoom.css');
        // addLink('client/node_modules/jstree/dist/themes/default/style.min.css');
        // addLink('client/node_modules/datatables/media/css/jquery.dataTables.min.css');
        // addLink('client/playbook/playbook.css');

        addScript("client/node_modules/jquery-migrate/dist/jquery-migrate.min.js");
        addScript("client/node_modules/jqueryui/jquery-ui.min.js");
        addScript("client/playbook/plugins/cytoscape/cytoscape.min.js");
        addScript("client/playbook/plugins/cytoscape/cytoscape-undo-redo.js");
        addScript("client/playbook/plugins/cytoscape/cytoscape-panzoom.js");
        addScript("client/playbook/plugins/cytoscape/cytoscape-edgehandles.js");
        addScript("client/playbook/plugins/cytoscape/cytoscape-clipboard.js");
        addScript("client/playbook/plugins/cytoscape/cytoscape-grid-guide.js");
        addScript("client/node_modules/json-editor/dist/jsoneditor.min.js");
        addScript("client/node_modules/jstree/dist/jstree.min.js");
        addScript("client/playbook/plugins/notifyjs/notify.min.js");
        addScript('client/node_modules/datatables/media/js/jquery.dataTables.min.js');
        addScript("client/playbook/main.js");

    };
}
