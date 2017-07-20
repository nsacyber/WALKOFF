import { Case } from './case'

export class Event {
	id: number;
  timestamp: Date;
  event_type: string;
  ancestry: string[];
  message: string;
  note: string;
  data: Object;
  cases: Case[];
}