import { test } from 'node:test'
import assert from 'node:assert/strict'
import { Timestamp } from './Timestamp.ts'

function isoAt(year: number, month: number, day: number, hours: number, minutes: number): string {
  return new Date(year, month - 1, day, hours, minutes).toISOString()
}

test('same-year timestamp shows lowercase weekday, no leading zeros on month/day', () => {
  const now = new Date()
  const iso = isoAt(now.getFullYear(), 9, 7, 14, 33) // 2026/9/7 is a monday
  const weekday = new Date(iso).toLocaleDateString('en-US', { weekday: 'short' }).toLowerCase()
  assert.equal(new Timestamp(iso).display(), `${weekday} 9/7 @ 14:33`)
})

test('cross-year timestamp replaces the weekday with the year', () => {
  const iso = isoAt(2024, 9, 7, 14, 33)
  assert.equal(new Timestamp(iso).display(), '2024/9/7 @ 14:33')
})

test('single-digit hours and minutes are still zero-padded', () => {
  const now = new Date()
  const iso = isoAt(now.getFullYear(), 1, 2, 9, 5)
  const weekday = new Date(iso).toLocaleDateString('en-US', { weekday: 'short' }).toLowerCase()
  assert.equal(new Timestamp(iso).display(), `${weekday} 1/2 @ 09:05`)
})

test('year getter reflects the underlying date', () => {
  assert.equal(new Timestamp(isoAt(2024, 9, 7, 14, 33)).year, 2024)
})
