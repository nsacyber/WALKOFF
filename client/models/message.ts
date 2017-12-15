import { MessageBody } from './messageBody';

export class Message {
	id: number;
	workflow_execution_uid: string;
	workflow_name: string;
	requires_reauthorization: boolean;
	subject: string;
	body: MessageBody[] = [];
	created_at: Date;
	last_read_at?: Date;
	is_read: boolean;
	awaiting_action: boolean;
	acted_on_by?: string;
	acted_on_at?: Date;
	read_by?: string[];
}
