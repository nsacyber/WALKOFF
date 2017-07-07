export class User {
	username: string;
	//Should never be populated when retrieving data
    private _password: string;
    get password(): string {
        return this._password;
    }
    set password(password: string) {
        this._password = password;
    }
	role: string[];
	active: boolean;
}