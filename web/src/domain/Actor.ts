// A real `enum` isn't erasable syntax, so this is the object-literal replacement.
export const Actor = {
  Human: 'human',
  AiAgent: 'ai_agent',
} as const

export type Actor = (typeof Actor)[keyof typeof Actor]

export function parseActor(value: string): Actor {
  switch (value) {
    case Actor.Human:
      return Actor.Human
    case Actor.AiAgent:
      return Actor.AiAgent
    default:
      throw new Error(`unexpected actor from api: "${value}"`)
  }
}
