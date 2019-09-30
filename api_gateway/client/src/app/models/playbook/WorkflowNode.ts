import { Argument } from './argument';
import { GraphPosition } from './graphPosition';
import { Watcher } from '../api/watcher';
import { ActionType } from '../api/actionApi';

export interface WorkflowNode {

    id: string;
	
    action_type: ActionType;

	name: string;

	app_name: string;

	app_version: string;

	action_name: string;

  cmd ?: string;

  watchers ?: Watcher[];

	position: GraphPosition;

    arguments: Argument[];
    
    has_errors: boolean;

    all_errors: string[];

    clone(): WorkflowNode;
}
