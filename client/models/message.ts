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
	awaiting_response: boolean;
	responded_by?: string;
	responded_at?: Date;
	read_by?: string[];
}
