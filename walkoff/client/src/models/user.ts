import { Type } from 'class-transformer';

import { Role } from './role';
import { WorkingUser } from './workingUser';

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

	@Type(() => Role)
	roles: Role[] = [];

	active: boolean;

	toWorkingUser(): WorkingUser {
		const returnUser = new WorkingUser();

		returnUser.id = this.id;
		returnUser.username = this.username;
		// returnUser.roles = user.roles;

		Array.isArray(this.roles) ?
			returnUser.role_ids = this.roles.map(r => r.id) :
			returnUser.role_ids = [];

		returnUser.active = this.active;

		return returnUser;
	}
}
