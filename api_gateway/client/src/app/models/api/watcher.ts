import { WatcherSchema } from './watcherSchema';

import { Type } from 'class-transformer';

export class Watcher {
  id_: string;
  name: string;

  arguments: WatcherSchema;
}


