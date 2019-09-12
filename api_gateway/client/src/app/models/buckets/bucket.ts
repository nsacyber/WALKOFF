import { Type } from 'class-transformer';
import { classToClass, Exclude } from 'class-transformer';
import { BucketTrigger } from './trigger';

export class Bucket {
  id: number;

  name: string;

  description: string;

  @Type(() => BucketTrigger)
  triggers: BucketTrigger[] = []

  @Exclude()
  isHidden: boolean = true;

  constructor() { }

  clone() {
    return classToClass(this, { ignoreDecorators: true });
  }
}

