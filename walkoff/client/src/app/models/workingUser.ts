import { User } from './user';

export class WorkingUser {
	id: number;

	username: string;
	
	role_ids: number[] = [];

	active: boolean;

	currentPassword: string;

	newPassword: string;

	confirmNewPassword: string;

	toSave(): User {
		const returnUser = new User();

		returnUser.id = this.id;
		returnUser.username = this.username;
		returnUser.roles = this.role_ids.map(id => ({ id }));
		returnUser.active = this.active;

		returnUser.old_password = this.currentPassword;
		returnUser.password = this.newPassword;
		return returnUser;
	}
}
