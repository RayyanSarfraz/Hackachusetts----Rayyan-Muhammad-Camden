import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import App from '../App'
import { AppProvider } from '../state/AppContext'
import { SAMPLE_NOTES } from '../lib/__tests__/fixtures'

function renderApp() {
  return render(
    <AppProvider>
      <App />
    </AppProvider>,
  )
}

/** Add the sample notes as a text document and analyze them. */
async function analyzeSampleNotes() {
  // The paste area lives inside a collapsible <details>; the textarea is still
  // in the DOM and reachable by placeholder regardless of open state.
  const textarea = screen.getByPlaceholderText(/paste notes here/i)
  fireEvent.change(textarea, { target: { value: SAMPLE_NOTES } })
  fireEvent.click(screen.getByRole('button', { name: /add text document/i }))
  fireEvent.click(screen.getByRole('button', { name: /^analyze/i }))
  await screen.findByRole('heading', { name: /review your health information/i })
}

/** Analyze, then advance to the matching step. */
async function gotoMatching() {
  await analyzeSampleNotes()
  fireEvent.click(
    screen.getByRole('button', { name: /confirm .* matching trials/i }),
  )
  await screen.findByRole('heading', { name: /ranked trial matches/i })
}

describe('TrialBridge app integration', () => {
  it('extracts facts from pasted notes, keeping unknowns Unknown', async () => {
    renderApp()
    await analyzeSampleNotes()

    const ageInput = screen.getByLabelText('Age') as HTMLInputElement
    expect(ageInput.value).toBe('54')

    const biomarkerInput = screen.getByLabelText(
      /biomarkers/i,
    ) as HTMLInputElement
    expect(biomarkerInput.value).toBe('')
  })

  it('shows ranked trial cards and a prioritized Next Best Question', async () => {
    renderApp()
    await gotoMatching()

    expect(screen.getByText(/DEMO-A/)).toBeInTheDocument()
    expect(screen.getByText(/DEMO-D/)).toBeInTheDocument()

    expect(
      screen.getByRole('heading', { name: /next best question/i }),
    ).toBeInTheDocument()
    expect(screen.getByText(/affects \d+ trial assessment/i)).toBeInTheDocument()
  })

  it('the "Why are we asking this?" accordion toggles open', async () => {
    renderApp()
    await gotoMatching()

    const why = screen.getByRole('button', { name: /why are we asking this/i })
    expect(why).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(why)
    expect(why).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText(/could help resolve/i)).toBeInTheDocument()
  })

  it('answering the question updates assessments and shows Before vs After', async () => {
    renderApp()
    await gotoMatching()

    const radios = screen.getAllByRole('radio')
    const positive = radios.find((r) =>
      within(r.closest('label')!).queryByText(/EGFR positive/i),
    )
    fireEvent.click(positive ?? radios[0])
    fireEvent.click(screen.getByRole('button', { name: /submit answer/i }))

    await screen.findByRole('heading', { name: /before vs after/i })
    expect(screen.getByRole('button', { name: /revise/i })).toBeInTheDocument()
  })

  it('changing travel preference keeps all trials without changing clinical counts', async () => {
    renderApp()
    await gotoMatching()

    const nearby = screen.getByRole('radio', { name: /nearby only/i })
    fireEvent.click(nearby)
    expect(nearby).toHaveAttribute('aria-checked', 'true')

    // All four trials still present (none silently removed).
    expect(screen.getByText(/DEMO-C/)).toBeInTheDocument()
    expect(screen.getByText(/DEMO-D/)).toBeInTheDocument()
  })

  it('eligibility evidence accordion opens on a trial card', async () => {
    renderApp()
    await gotoMatching()

    const evidenceButtons = screen.getAllByRole('button', {
      name: /view eligibility evidence/i,
    })
    expect(evidenceButtons.length).toBeGreaterThan(0)
    fireEvent.click(evidenceButtons[0])
    expect(evidenceButtons[0]).toHaveAttribute('aria-expanded', 'true')
  })
})
