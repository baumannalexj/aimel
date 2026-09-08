import { test } from 'node:test'
import assert from 'node:assert/strict'
import { hashToHex, participantColor } from './ParticipantColor.ts'

const HEX = /^#[0-9A-Fa-f]{6}$/

test('hashToHex is stable across calls', () => {
  const seed = 'alexander.baumann@aimel.com'
  assert.equal(hashToHex(seed), hashToHex(seed))
})

test('participantColor is stable and normalises the address first', () => {
  const first = participantColor('Alexander.Baumann@Aimel.com')
  const second = participantColor('  alexander.baumann@aimel.com  ')
  assert.equal(first, second)
  assert.match(first, HEX)
})

test('a handful of realistic addresses do not all collide onto one colour', () => {
  const addresses = [
    'alexander.baumann@aimel.com',
    'claude-0bd9c0c5@aimel.com',
    'claude-abc12345@aimel.com',
    'someone.else@aimel.com',
    'another.user@aimel.com',
  ]
  const colours = new Set(addresses.map(participantColor))
  assert.ok(colours.size > 1, `expected spread across addresses, got one colour for all: ${[...colours]}`)
})
