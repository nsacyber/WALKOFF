import { WatcherSchema } from './watcherSchema';

import { Type } from 'class-transformer';

export class Watcher {
  id_: string;
  name: string;

  @Type(()=> WatcherSchema)
  arguments: WatcherSchema = new WatcherSchema();
}


