import { Role } from './role';
import { WorkingUser } from './workingUser';

export class User {
	static toWorkingUser(user: User): WorkingUser {
		const returnUser = new WorkingUser();

		returnUser.id = user.id;
		returnUser.username = user.username;
		// returnUser.roles = user.roles;

		Array.isArray(user.roles) ?
			returnUser.role_ids = user.roles.map(r => r.id) :
			returnUser.role_ids = [];

		returnUser.active = user.active;

		return returnUser;
	}

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
	roles: Role[] = [];
	active: boolean;
}
