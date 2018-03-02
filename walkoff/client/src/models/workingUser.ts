import { User } from './user';

export class WorkingUser {
	static toSave(workingUser: WorkingUser): User {
		const returnUser = new User();

		returnUser.id = workingUser.id;
		returnUser.username = workingUser.username;
		returnUser.roles = workingUser.role_ids.map(id => ({ id }));
		returnUser.active = workingUser.active;

		returnUser.old_password = workingUser.currentPassword;
		returnUser.password = workingUser.newPassword;
		return returnUser;
	}

	id: number;
	username: string;
	// roles: number[] = [];
	role_ids: number[] = [];
	active: boolean;
	currentPassword: string;
	newPassword: string;
	confirmNewPassword: string;
}
