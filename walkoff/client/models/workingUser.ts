import { User } from './user';

export class WorkingUser {
	static toSave(workingUser: WorkingUser): User {
		const returnUser = new User();

		returnUser.id = workingUser.id;
		returnUser.username = workingUser.username;
		// TODO: currently the API requires roles, not role_ids. Update this when we change the API to role_ids
		returnUser.roles = (workingUser.roles as any);
		// returnUser.role_ids = workingUser.role_ids;
		returnUser.active = workingUser.active;

		returnUser.old_password = workingUser.currentPassword;
		returnUser.password = workingUser.newPassword;
		return returnUser;
	}

	id: number;
	username: string;
	roles: number[] = [];
	// role_ids: number[] = [];
	active: boolean;
	currentPassword: string;
	newPassword: string;
	confirmNewPassword: string;
}
