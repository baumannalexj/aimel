// What the repository throws after switching on ResponseError.kind. The root container catches
// these and shows a toast or a red banner -- see web/ARCHITECTURE.md, "Errors". The repository
// picks which variant and message; these classes just give it something phrased for a human.

export abstract class DomainException extends Error {
  constructor(message: string) {
    super(message)
    this.name = this.constructor.name
  }
}

export class ServiceUnavailableException extends DomainException {
  constructor(message = 'Cannot reach the mail service. Check that it is running and try again.') {
    super(message)
  }
}

export class EmailNotFoundException extends DomainException {
  constructor(message = 'That email could not be found.') {
    super(message)
  }
}

export class EmailDeletedException extends DomainException {
  constructor(message = 'That email has been deleted and can no longer be acted on.') {
    super(message)
  }
}

export class InvalidReplyException extends DomainException {
  constructor(message = "That reply isn't valid. Check the body and try again.") {
    super(message)
  }
}

export class ServiceFaultException extends DomainException {
  constructor(message = 'The mail service ran into a problem. Try again shortly.') {
    super(message)
  }
}

export class UnexpectedResponseException extends DomainException {
  constructor(message = 'The mail service returned something unexpected.') {
    super(message)
  }
}
