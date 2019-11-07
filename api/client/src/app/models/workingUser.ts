import { User } from './user';

export class WorkingUser {
	id: number;

	username: string;
	
	role_ids: string[] = [];

	active: boolean;

	currentPassword: string;

	newPassword: string;

	confirmNewPassword: string;

	public static toUser(workingUser: WorkingUser): User {
		const returnUser = new User();

		returnUser.id = workingUser.id;
		returnUser.username = workingUser.username;
		returnUser.roles = workingUser.role_ids;
		returnUser.active = workingUser.active;

		returnUser.old_password = workingUser.currentPassword;
		returnUser.password = workingUser.newPassword;
		return returnUser;
	}

	public static fromUser(user: User): WorkingUser {
		const returnUser = new WorkingUser();

		returnUser.id = user.id;
		returnUser.username = user.username;
		// returnUser.roles = user.roles;

		Array.isArray(user.roles) ?
			returnUser.role_ids = user.roles :
			returnUser.role_ids = [];

		returnUser.active = user.active;

		return returnUser;
	}
}
