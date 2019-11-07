import { Type } from 'class-transformer';

import { Role } from './role';

export class User {
	id: number;

	username: string;

	/**
	 * Used to verify the user's old password on edit. Should never be populated when retrieving data.
	 */
	old_password: string;

	/**
	 * Used for setting password on add/edit. Leave null or empty to not change password.
	 * Should never be populated when retrieving data.
	 */
	password: string;

	//@Type(() => Role)
	roles: string[] = [];

	active: boolean;
}
