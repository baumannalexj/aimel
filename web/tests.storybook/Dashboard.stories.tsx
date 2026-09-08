// Storybook stories for the dashboard's happy paths, one per scenario you gave.
//
// SKELETON: these do not run yet. Storybook is not installed -- see tests.storybook/README.md for
// the exact packages and why I did not install them without asking. The bodies are real, so this
// becomes a working suite the moment it is installed; only the import on the next line is aspirational.
import type { Meta, StoryObj } from '@storybook/react'
import { expect, waitFor, within, userEvent } from '@storybook/test'
import App from '../src/App'
import { FakeApi, SEED, stubFetch } from './fakeApi'

// One fake per story, installed before render and restored after, so no story leaks into the next.
function withFakeApi(api: FakeApi) {
  return (Story: () => JSX.Element) => {
    const { restore } = stubFetch(api)
    // eslint-disable-next-line react-hooks/rules-of-hooks
    setTimeout(restore, 0)
    return <Story />
  }
}

const meta: Meta<typeof App> = {
  title: 'Dashboard',
  component: App,
}
export default meta

type Story = StoryObj<typeof App>

/**
 * I can see a list of read and unread emails.
 *
 * Asserts the distinction is visible, not merely present in the data: an unread thread carries its
 * count, a read one does not.
 */
export const ReadAndUnreadAreDistinguishable: Story = {
  decorators: [withFakeApi(new FakeApi())],
  play: async ({ canvasElement }) => {
    const screen = within(canvasElement)
    await waitFor(() => expect(screen.getByText('fix the flaky auth test')).toBeInTheDocument())

    // Unread thread shows its count; the read one has nothing to show.
    await expect(screen.getByLabelText(/fix the flaky auth test, 1 unread/)).toBeInTheDocument()
    await expect(screen.queryByLabelText(/ship it behind a flag, \d+ unread/)).toBeNull()
  },
}

/**
 * When I click an unread email then it is marked as read.
 *
 * Asserts the round trip happened, not just that a class changed -- markRead must actually be called
 * with that email's uuid, and the sidebar count must follow it.
 */
export const OpeningAnUnreadThreadMarksItRead: Story = {
  decorators: [withFakeApi(new FakeApi())],
  play: async ({ canvasElement }) => {
    const api = new FakeApi()
    const screen = within(canvasElement)

    await waitFor(() => expect(screen.getByText('ship it behind a flag')).toBeInTheDocument())
    await userEvent.click(screen.getByLabelText(/fix the flaky auth test/))

    await waitFor(() => expect(api.markReadCalls).toContain('email-1'))
    await waitFor(() =>
      expect(screen.queryByLabelText(/fix the flaky auth test, 1 unread/)).toBeNull(),
    )
  },
}

/**
 * When I can see the thread I can reply, Cmd+Enter sends, and I do not get an unread notification
 * for my own reply.
 *
 * The last assertion is the one that matters and the one that has broken twice. Unread is the
 * RECIPIENT's queue: the reply must be waiting for the agent while never counting as unread for the
 * human. Marking it read instead deletes it from the agent's poll before the agent sees it.
 */
export const CmdEnterSendsAndDoesNotNotifyMe: Story = {
  decorators: [withFakeApi(new FakeApi())],
  play: async ({ canvasElement }) => {
    const api = new FakeApi()
    const screen = within(canvasElement)

    await waitFor(() => expect(screen.getByText('fix the flaky auth test')).toBeInTheDocument())
    await userEvent.click(screen.getByRole('button', { name: 'Reply' }))

    const box = screen.getByPlaceholderText('Write a reply…')
    await userEvent.type(box, 'Looks good, merging.')
    await userEvent.keyboard('{Meta>}{Enter}{/Meta}')

    await waitFor(() => expect(api.replyCalls).toHaveLength(1))
    await expect(api.replyCalls[0].html).toContain('Looks good, merging.')

    // My own reply must not raise my unread count on this thread.
    await waitFor(() =>
      expect(screen.queryByLabelText(/fix the flaky auth test, \d+ unread/)).toBeNull(),
    )
  },
}

/**
 * Given many threads across sessions, the agent filter lists sessions by name, and picking one
 * narrows the list to that session's threads -- plural, so it is a filter and not a thread jump.
 *
 * PENDING UI-10: the session dropdown does not exist yet. The selectors below name what it should
 * expose; adjust them to whatever it actually renders rather than treating them as fixed.
 */
export const FilteringByAgentSession: Story = {
  decorators: [withFakeApi(new FakeApi())],
  play: async ({ canvasElement }) => {
    const screen = within(canvasElement)
    await waitFor(() => expect(screen.getByText('fix the flaky auth test')).toBeInTheDocument())

    await userEvent.click(screen.getByLabelText(/agent filter/i))
    await userEvent.click(screen.getByRole('option', { name: /aaaa1111/ }))

    // Both of the second session's threads survive; neither of the first session's does.
    await waitFor(() => expect(screen.getByText('second session, first thread')).toBeInTheDocument())
    await expect(screen.getByText('second session, second thread')).toBeInTheDocument()
    await expect(screen.queryByText('fix the flaky auth test')).toBeNull()
  },
}

/**
 * I can send a new email to that session.
 *
 * PENDING: compose does not exist. UI-10 explicitly defers it and UI-9 owns the multi-recipient send
 * path, so this stays a skeleton until one of them lands a compose surface.
 */
export const ComposingToASession: Story = {
  decorators: [withFakeApi(new FakeApi())],
  play: async () => {
    // TODO(UI-10): open compose from the filtered list, pick the session, send, and assert the new
    // thread appears with that session's colour.
  },
}
