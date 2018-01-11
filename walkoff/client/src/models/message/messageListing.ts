export class MessageListing {
	id: number;
	subject: string;
	created_at: Date;
	awaiting_response: boolean;
	is_read: boolean;
	last_read_at: Date;
}
