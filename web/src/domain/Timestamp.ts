const WEEKDAYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']

export class Timestamp {
  private readonly at: Date

  constructor(iso: string) {
    this.at = new Date(iso)
  }

  /**
   * `wed 9/7 @ 14:33` in the browser's timezone.
   *
   * When the year is not the current year the weekday is replaced by it: `2024/9/7 @ 14:33`.
   * A year that isn't now is the thing you need to see; the weekday only helps for recent mail.
   */
  display(): string {
    const isCurrentYear = this.year === new Date().getFullYear()
    const datePrefix = isCurrentYear ? WEEKDAYS[this.at.getDay()] : String(this.year)
    const separator = isCurrentYear ? ' ' : '/'
    const month = this.at.getMonth() + 1
    const day = this.at.getDate()
    const hours = String(this.at.getHours()).padStart(2, '0')
    const minutes = String(this.at.getMinutes()).padStart(2, '0')
    return `${datePrefix}${separator}${month}/${day} @ ${hours}:${minutes}`
  }

  get year(): number {
    return this.at.getFullYear()
  }
}
