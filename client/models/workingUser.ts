import { User } from './user';
import { Role } from './role';

export class WorkingUser {
	static toUser(workingUser: WorkingUser): User {
		const returnUser = new User();

		returnUser.id = workingUser.id;
		returnUser.username = workingUser.username;
		returnUser.roles = workingUser.roles;
		returnUser.active = workingUser.active;

		//TODO: update once we merge the pw-fix branch in, need to submit current password as well
		returnUser.old_password = workingUser.currentPassword;
		returnUser.password = workingUser.newPassword;
		return returnUser;
	}

	id: number;
	username: string;
	roles: Role[];
	active: boolean;
	currentPassword: string;
	newPassword: string;
	confirmNewPassword: string;
}
