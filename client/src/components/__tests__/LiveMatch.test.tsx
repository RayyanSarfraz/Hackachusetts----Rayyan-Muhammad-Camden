import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import App from '../../App'
import { AppProvider } from '../../state/AppContext'

function renderApp() {
  return render(
    <AppProvider>
      <App />
    </AppProvider>,
  )
}

function mockMatchResponse(overrides: Record<string, unknown> = {}) {
  return {
    profile: {
      age: 54,
      primary_condition: 'Alcohol Use Disorder',
      location: { state: 'MA', city: 'Boston' },
      conditions: [{ value: 'Alcohol Use Disorder', source: 'user' }],
      symptoms: [],
      medications: [],
    },
    model_available: true,
    query: 'Alcohol Use Disorder',
    retrieval_available: true,
    matching_available: false,
    results: [
      {
        trial_id: 'NCT07219953',
        distance: 0.61,
        metadata: {},
        trial: {
          nct_id: 'NCT07219953',
          title: 'A Study of Brenipatide in Participants With Alcohol Use Disorder',
          phase: 'PHASE3',
          conditions: ['Alcohol Use Disorder'],
          status: 'RECRUITING',
          city: '',
        },
      },
    ],
    questions: [
      {
        question_id: 'q_sex',
        required_fact_key: 'sex_for_eligibility',
        display_question: "What is the patient's sex for eligibility screening?",
        answer_type: 'text',
        related_trial_ids: [],
        source_criterion_ids: [],
      },
    ],
    detail: null,
    ...overrides,
  }
}

async function addNoteAndSearch() {
  // Live mode is the default. Add a note via the intake tray, then search.
  const textarea = screen.getByPlaceholderText(/paste notes here/i)
  fireEvent.change(textarea, { target: { value: 'has alcohol use disorder' } })
  fireEvent.click(screen.getByRole('button', { name: /add text document/i }))
  fireEvent.click(screen.getByRole('button', { name: /find matching trials/i }))
}

describe('LiveMatch (real engine flow)', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true,
      json: async () => mockMatchResponse(),
    })) as unknown as typeof fetch)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('searches the engine and renders matched trials + extracted facts', async () => {
    renderApp()
    await addNoteAndSearch()

    expect(await screen.findByText(/matched trials/i)).toBeInTheDocument()
    expect(
      screen.getByText(/Brenipatide in Participants With Alcohol Use Disorder/i),
    ).toBeInTheDocument()
    expect(screen.getByText('NCT07219953', { exact: false })).toBeInTheDocument()
    // Extracted summary shows what the engine pulled.
    expect(screen.getByText(/what we extracted/i)).toBeInTheDocument()
    // POSTs to the engine match endpoint.
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/engine/match/'),
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('renders a clarifying-question form and refines on submit', async () => {
    renderApp()
    await addNoteAndSearch()

    const form = await screen.findByText(/a few details improve matching/i)
    expect(form).toBeInTheDocument()

    const sexInput = screen.getByLabelText(/sex for eligibility/i)
    fireEvent.change(sexInput, { target: { value: 'female' } })
    fireEvent.click(screen.getByRole('button', { name: /refine matches/i }))

    // Second call carries the answer in the body.
    expect(fetch).toHaveBeenCalledTimes(2)
    const lastCall = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[1]
    expect(String(lastCall[1].body)).toContain('female')
  })

  it('shows an honest message when retrieval is unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true,
      json: async () =>
        mockMatchResponse({
          retrieval_available: false,
          results: [],
          detail: 'Trial retrieval is unavailable: no vector store configured.',
        }),
    })) as unknown as typeof fetch)

    renderApp()
    await addNoteAndSearch()

    expect(await screen.findByText(/retrieval is unavailable/i)).toBeInTheDocument()
  })
})
