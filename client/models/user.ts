import { Role } from './role'

export class User {
	id: number;
	username: string;
	//Used to verify the user's old password on edit. Should never be populated when retrieving data.
	old_password: string;
	//Used for setting password on add/edit. Leave null or empty to not change password. Should never be populated when retrieving data.
	password: string;
	roles: Role[];
	active: boolean;

	static toWorkingUser(user: User): WorkingUser {
		let returnUser = new WorkingUser();

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

	static toUser(workingUser: WorkingUser): User {
		let returnUser = new User();

		returnUser.id = workingUser.id;
		returnUser.username = workingUser.username;
		returnUser.roles = workingUser.roles;
		returnUser.active = workingUser.active;

		//TODO: update once we merge the pw-fix branch in, need to submit current password as well
		returnUser.old_password = workingUser.currentPassword;
		returnUser.password = workingUser.newPassword;
		console.log(returnUser);
		return returnUser;
	}
}