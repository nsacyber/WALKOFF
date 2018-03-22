import { Type } from 'class-transformer';

import { MessageBody } from './messageBody';

export class Message {
	id: number;

	workflow_execution_id: string;

	workflow_name: string;

	requires_reauthorization: boolean;

	subject: string;

	@Type(() => MessageBody)
	body: MessageBody[] = [];

	created_at: string;

	last_read_at?: string;

	is_read: boolean;

	awaiting_response: boolean;

	responded_by?: string;

	responded_at?: string;

	read_by?: string[] = [];
}
