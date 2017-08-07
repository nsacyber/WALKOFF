import { Component } from '@angular/core';

import { PlaybookService } from './playbook.service';

@Component({
	selector: 'playbook-component',
	templateUrl: 'client/playbook/playbook.html',
	// styleUrls: ['client/playbook/playbook.css'],
	providers: [PlaybookService]
})
export class PlaybookComponent {

	constructor(private playbookService: PlaybookService) {
    }

    ngAfterViewInit() {

        let addLink = (script: string) => {
            let s = document.createElement("link");
            s.rel = "stylesheet";
            s.href = script;
            document.body.appendChild(s);
        }

        let addScript = (script: string) => {
            let s = document.createElement("script");
            s.type = "text/javascript";
            s.src = script;
            s.async = false;
            document.body.appendChild(s);
        }

        addLink('client/node_modules/jqueryui/jquery-ui.min.css');
        addLink('client/playbook/plugins/cytoscape/cytoscape.js-panzoom.css');
        addLink('client/node_modules/jstree/dist/themes/default/style.min.css');
        addLink('client/playbook/playbook.css');

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
        addScript("client/playbook/main.js");

    };
}
