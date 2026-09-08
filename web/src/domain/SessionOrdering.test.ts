import { test } from 'node:test'
import assert from 'node:assert/strict'
import { ClaudeSession } from './ClaudeSession.ts'
import { ThreadSummary } from './ThreadSummary.ts'
import { Anything, filtered, sorted } from './Ordering.ts'
import {
  ByLastActiveDescending,
  ByProjectThenLastActive,
  ThreadsByUpdatedDescending,
  ThreadsOfSession,
} from './SessionOrdering.ts'

// The real classes import only types, which erase, so node resolves nothing at runtime and these
// can be constructed for real instead of faked. See tests/README.md for why that matters here.
function session(id: string, project: string, lastActiveAt: string, title = ''): ClaudeSession {
  return new ClaudeSession(id, id, project, title, '', lastActiveAt)
}

function thread(session: string, updatedAt: string): ThreadSummary {
  return new ThreadSummary(`t-${session}-${updatedAt}`, 'subject', session, session.slice(0, 8), '#000000', 1, 0, 'e1', updatedAt)
}

test('sessions order most recently active first', () => {
  const list = [
    session('old', 'a', '2026-08-11T23:31:29+00:00'),
    session('new', 'b', '2026-09-08T04:35:43+00:00'),
    session('mid', 'c', '2026-09-08T03:43:15+00:00'),
  ]

  assert.deepEqual(
    sorted(list, new ByLastActiveDescending()).map((s) => s.shortUuid),
    ['new', 'mid', 'old'],
  )
})

test('sorting does not mutate the array it was given', () => {
  const list = [
    session('a', 'p', '2026-01-01T00:00:00+00:00'),
    session('b', 'p', '2026-02-01T00:00:00+00:00'),
  ]

  sorted(list, new ByLastActiveDescending())

  assert.deepEqual(list.map((s) => s.shortUuid), ['a', 'b'])
})

test('project ordering falls back to activity inside a project', () => {
  const list = [
    session('z-late', 'zebra', '2026-01-01T00:00:00+00:00'),
    session('a-early', 'apple', '2026-01-01T00:00:00+00:00'),
    session('a-late', 'apple', '2026-05-01T00:00:00+00:00'),
  ]

  assert.deepEqual(
    sorted(list, new ByProjectThenLastActive()).map((s) => s.shortUuid),
    ['a-late', 'a-early', 'z-late'],
  )
})

test('filtering to a session keeps that session and drops the rest', () => {
  const list = [
    thread('one', '2026-01-01T00:00:00+00:00'),
    thread('two', '2026-01-02T00:00:00+00:00'),
    thread('one', '2026-01-03T00:00:00+00:00'),
  ]

  const kept = filtered(list, new ThreadsOfSession('one'))

  assert.equal(kept.length, 2)
  assert.ok(kept.every((one) => one.session === 'one'))
})

test('Anything keeps everything, so a cleared filter needs no null check', () => {
  const list = [thread('one', '2026-01-01T00:00:00+00:00'), thread('two', '2026-01-02T00:00:00+00:00')]

  assert.equal(filtered(list, new Anything<ThreadSummary>()).length, 2)
})

test('threads order newest activity first', () => {
  const list = [thread('a', '2026-01-01T00:00:00+00:00'), thread('b', '2026-03-01T00:00:00+00:00')]

  assert.deepEqual(
    sorted(list, new ThreadsByUpdatedDescending()).map((t) => t.session),
    ['b', 'a'],
  )
})

test('a session labels itself with its own name when it has one', () => {
  const named = session('a', 'p', '2026-01-01T00:00:00+00:00', 'Tiny email server with HTML for Claude agents')

  assert.equal(named.label(), 'Tiny email server with HTML for Claude agents')
})

test('an untitled session falls back to its opening prompt, then to a placeholder', () => {
  const untitled = new ClaudeSession('b', 'b', 'p', '', 'what I first asked', '2026-01-01T00:00:00+00:00')
  const blank = new ClaudeSession('c', 'c', 'p', '', '', '2026-01-01T00:00:00+00:00')

  assert.equal(untitled.label(), 'what I first asked')
  assert.equal(blank.label(), '(no prompt yet)')
})
