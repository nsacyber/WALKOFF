import { Type } from 'class-transformer';

import { UserClaims } from './userClaims';

export class AccessToken {
	exp: number;

	fresh: boolean;

	iat: number;

	identity: number;

	jti: string;

	nbf: number;

	type: string;
	
	@Type(() => UserClaims)
	user_claims: UserClaims;
}
