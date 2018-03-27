import * as moment from 'moment';

export class Metric {
    count: number = 0;

    avg_time: string = '0:00:00.000000';

    get display_avg_time() : string {
        let duration = moment.duration(this.avg_time);
        return duration.asSeconds() >= 1 ? duration.asSeconds() + ' s' : duration.asMilliseconds() + ' ms';
    }

    get display_text(): string {
        return (this.count > 0) ? `${this.count} (${this.display_avg_time})` : '0';
    }
}