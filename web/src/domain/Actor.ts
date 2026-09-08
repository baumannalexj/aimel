// Values are the wire values the python api sends, so parsing is a lookup rather than a mapping.
export enum Actor {
  Human = 'human',
  AiAgent = 'ai_agent',
}

export function parseActor(value: string): Actor {
  if (isActor(value)) return value
  throw new Error(`unexpected actor from api: "${value}"`)
}

function isActor(value: string): value is Actor {
  return Object.values<string>(Actor).includes(value)
}
