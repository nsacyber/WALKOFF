import { User } from './user';
import { Role } from './role';

export class WorkingUser {
	static toUser(workingUser: WorkingUser): User {
		const returnUser = new User();

		returnUser.id = workingUser.id;
		returnUser.username = workingUser.username;
		returnUser.roles = workingUser.roles;
		returnUser.role_ids = workingUser.role_ids;
		returnUser.active = workingUser.active;

		returnUser.old_password = workingUser.currentPassword;
		returnUser.password = workingUser.newPassword;
		return returnUser;
	}

	id: number;
	username: string;
	roles: Role[] = [];
	role_ids: number[] = [];
	active: boolean;
	currentPassword: string;
	newPassword: string;
	confirmNewPassword: string;
}
