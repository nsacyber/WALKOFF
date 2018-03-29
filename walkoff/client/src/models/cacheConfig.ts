export class CacheConfig {

    static getDefault(): CacheConfig {
		return {
			type: 'disk',
            directory: './data/cache',
            shards: 8,
            timeout: 0.01,
            retry: true,
		} as CacheConfig;
	}

    type: string = 'disk';
	directory: string;
	shards: number;
	timeout: number;
	retry: boolean;
	host: string;
	port: number;
	unix_socket_path: string;
}
