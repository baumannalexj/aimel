// Keyboard behaviour is passed in, not baked in. A component says "something may want a chord
// here" and the caller decides which chord and what it does -- same reason Clickable takes onClick
// rather than knowing what a click means.

export enum Modifier {
  Meta = 'meta',
  Ctrl = 'ctrl',
  Shift = 'shift',
  Alt = 'alt',
}

interface ChordEvent {
  key: string
  metaKey: boolean
  ctrlKey: boolean
  shiftKey: boolean
  altKey: boolean
  preventDefault: () => void
}

/** A chord with no behaviour attached, so a caller can name one without owning what it does. */
export class KeyChord {
  key: string
  modifiers: Modifier[]

  constructor(key: string, modifiers: Modifier[]) {
    this.key = key
    this.modifiers = modifiers
  }

  boundTo(run: () => void): KeyCommand {
    return new KeyCommand(this.key, this.modifiers, run)
  }
}

export class KeyCommand {
  key: string
  modifiers: Modifier[]
  run: () => void

  constructor(key: string, modifiers: Modifier[], run: () => void) {
    this.key = key
    this.modifiers = modifiers
    this.run = run
  }

  // Every modifier the command wants must be held and every one it doesn't must not be, so
  // Cmd+Enter never fires on Cmd+Shift+Enter. A near-miss firing anyway is worse than nothing.
  matches(event: ChordEvent): boolean {
    if (event.key !== this.key) return false
    const held = {
      [Modifier.Meta]: event.metaKey,
      [Modifier.Ctrl]: event.ctrlKey,
      [Modifier.Shift]: event.shiftKey,
      [Modifier.Alt]: event.altKey,
    }
    return Object.values(Modifier).every(
      (modifier) => held[modifier] === this.modifiers.includes(modifier),
    )
  }
}

export class KeyCommands {
  private readonly commands: KeyCommand[]

  constructor(commands: KeyCommand[] = []) {
    this.commands = commands
  }

  /** True when a command ran, so the component knows the key was consumed. */
  handle(event: ChordEvent): boolean {
    const command = this.commands.find((candidate) => candidate.matches(event))
    if (!command) return false
    event.preventDefault()
    command.run()
    return true
  }
}
