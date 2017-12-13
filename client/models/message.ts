import { MessageBody } from './messageBody';

export class Message {
	id: number;
	workflow_execution_uid: string;
	workflow_name: string;
	requires_reauthorization: boolean;
	subject: string;
	body: MessageBody[] = [];
	is_read: boolean;
	created_at: Date;
	read_at: Date;
}
