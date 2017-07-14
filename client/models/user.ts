import { Role } from './role'

export class User {
	id: number;
	username: string;
	//Should never be populated when retrieving data
	private _password: string;
	get password(): string {
		return this._password;
	}
	set password(password: string) {
		this._password = password;
	}
	roles: Role[];
	active: boolean;

	static toWorkingUser(user: User): WorkingUser {
		let returnUser = new WorkingUser;

		returnUser.id = user.id;
		returnUser.username = user.username;
		returnUser.roles = user.roles;
		returnUser.active = user.active;

		return returnUser;
	}
}

export class WorkingUser {
	id: number;
	username: string;
	roles: Role[];
	active: boolean;
	currentPassword: string;
	newPassword: string;
	confirmNewPassword: string;
}