// SEAM — signature is settled, body is not. See the display() contract below.

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
    throw new Error('Timestamp.display is not implemented yet')
  }

  get year(): number {
    return this.at.getFullYear()
  }
}
