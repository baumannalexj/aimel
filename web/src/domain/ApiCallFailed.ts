import { DomainException } from './DomainException'

// Everything the banner needs and nothing it doesn't. `status` is 0 when the request never got a
// response at all, which is how "the api isn't running" looks from here.
export class ApiCallFailed extends DomainException {
  readonly status: number
  readonly path: string

  constructor(status: number, path: string, message: string) {
    super(message)
    this.status = status
    this.path = path
  }
}
