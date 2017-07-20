import { Role } from './role'

export class User {
	id: number;
	username: string;
	//Should never be populated when retrieving data
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
		console.log(workingUser);
		let returnUser = new User();

		returnUser.id = workingUser.id;
		returnUser.username = workingUser.username;
		returnUser.roles = workingUser.roles;
		returnUser.active = workingUser.active;

		//TODO: update once we merge the pw-fix branch in, need to submit current password as well
		// returnUser.currentPassword = workingUser.currentPassword;
		returnUser.password = workingUser.newPassword;

		return returnUser;
	}
}