import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'dateFormat',
  standalone: true
})
export class DateFormatPipe implements PipeTransform {
  transform(value: string | Date | null | undefined, format: 'short' | 'medium' | 'long' | 'full' = 'medium'): string {
    if (!value) return '';

    const date = typeof value === 'string' ? new Date(value) : value;

    if (isNaN(date.getTime())) return '';

    const options: Intl.DateTimeFormatOptions = this.getFormatOptions(format);

    return new Intl.DateTimeFormat('en-US', options).format(date);
  }

  private getFormatOptions(format: string): Intl.DateTimeFormatOptions {
    switch (format) {
      case 'short':
        return { month: 'numeric', day: 'numeric', year: '2-digit' };
      case 'medium':
        return { month: 'short', day: 'numeric', year: 'numeric' };
      case 'long':
        return { month: 'long', day: 'numeric', year: 'numeric' };
      case 'full':
        return { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' };
      default:
        return { month: 'short', day: 'numeric', year: 'numeric' };
    }
  }
}
