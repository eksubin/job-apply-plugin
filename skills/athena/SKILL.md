---
name: athena
description: Fill out job applications automatically using your resume. Use when the user wants to apply for jobs on LinkedIn Easy Apply, Greenhouse, Ashby, Lever, Rippling, or Workday. Formerly known as job-apply.
allowed-tools: Read, Write, Bash, mcp__browseros-neo__*, mcp__claude-in-chrome__*, mcp__plugin_playwright_playwright__*
---

# Athena — Job Application Assistant

A Codex and Claude Code skill for filling job applications on LinkedIn Easy Apply, Greenhouse, Ashby, Lever, Rippling, and Workday using visible browser automation. Invoke as `$job-apply:athena` (Codex) or `/job-apply:athena` (Claude Code).

## Initial Prompt

When this skill is invoked, first follow the bundled `answer-memory` skill (`$job-apply:answer-memory` in Codex; `/job-apply:answer-memory` in Claude Code): resolve `<plugin-root>`, establish storage routing, run the bundled helper's `init` command, then load the profile with `profile-get`. Never read or write persistent Job Apply files directly.

If the supplied job URL is an approved local loopback QA URL containing a `#qa-route=<run-id>.<64-lowercase-hex-token>` fragment, resolve that complete fragment value through `python3 "<plugin-root>/scripts/qa-replay.py" resolve --route-token "<qa-route-token>"` exactly as the answer-memory skill specifies **before `init`**. Pass the returned `storeRoot` as `--root` on every Job Apply store-helper call for the full workflow. Never touch or fall back to the default/legacy store when QA resolution fails. Keep the route token private. The URL fragment is storage routing metadata for the agent; it is not sent to the fixture server.

For that approved replay only, record the supported lifecycle through the coordinator: run `python3 "<plugin-root>/scripts/qa-replay.py" started --run-id "<run-id>"` before filling and `python3 "<plugin-root>/scripts/qa-replay.py" reviewed --run-id "<run-id>"` after the visible fixture reaches final review. Do not substitute direct history or session writes. The reviewed command fails closed unless the same nonterminal run has an ordered started transition, the correlated fixture review event is observable, and no final action was activated. Repeating either command is safe and does not duplicate events.

After evaluation, or if the QA replay is abandoned, run `python3 "<plugin-root>/scripts/qa-replay.py" cleanup --run-id "<run-id>"`. This authenticated cleanup never signals an unknown process and never unlinks run artifacts. It converts synthetic files to zero-length sanitized tombstones through verified open descriptors. Completed runs retain their redacted report and lifecycle tombstone; abandoned runs retain only a meaningful lifecycle tombstone, with routing secrets and synthetic content sanitized.

**If the returned profile object is empty**, say:

> Welcome to the Job Application Assistant! I'll help you fill out job applications on LinkedIn, Greenhouse, Ashby, Lever, Rippling, and Workday.
>
> First, I need to set up your profile. This is a one-time process — your information will be saved for future applications.
>
> **Please provide the path to your standard resume file** (PDF, DOCX, or TXT) **AND the path to your master CV** (DOCX format).
>
> For example: `~/Documents/resume.pdf` and `~/Documents/master-cv.docx`

Then wait for the user to provide both paths before proceeding with profile extraction.

**If the profile contains applicant data**, say:

> Welcome back! Your local Job Apply profile and answer memory are ready.
>
> **Provide a job URL** and I'll help you apply. For example:
> - LinkedIn: `https://www.linkedin.com/jobs/view/123456789`
> - Greenhouse: `https://boards.greenhouse.io/company/jobs/123`
> - Workday: `https://company.wd5.myworkdayjobs.com/jobs/job/123`
>
> Or say **"reset profile"** if you want to update your information from a new resume.

---

## Required Input

- **Standard Resume file path**: Path to your standard resume (PDF, DOCX, or TXT format)
- **Master CV file path**: Path to your master CV (strictly DOCX format) for automated tailoring
- **Job URL**: LinkedIn job posting, LinkedIn Jobs Tracker URL (`https://www.linkedin.com/jobs-tracker/`), or direct application link
- **Auto-submit flag** (optional): If the user explicitly includes "submit", "auto-submit", or "submit for me" in their request, the skill will proceed past the review page and complete submission after filling the application. Without this flag, the default behavior is to stop at the review page.

## Profile Storage

Your extracted profile is stored under `~/.job-apply/` for reuse across sessions. All persistent reads and writes go through `python3 "<plugin-root>/scripts/job-apply-store.py"` as defined by the bundled `answer-memory` skill. A first run non-destructively migrates an existing `~/.claude-job-profile.json`.

## Auto-submit policy boundary

`review_only` is the default mode. The local `scripts/job_apply_policy.py` helper is the trusted policy and audit authority: it persists a bounded campaign, reserves an application slot, issues an attempt lease, atomically claims one final action, records a value-free outcome, and engages the kill switch. It cannot control a browser.

Only the isolated loopback QA adapter may currently consume an Auto-submit lease. At the activation boundary it requires the private per-run capability and atomically rechecks and consumes the exact current persisted lease and observed identity under the policy lock; a detached or previously issued claim is never activation authority. It proves review-only refusal, kill/expiry races, forged and stale requests, redirects, prompt/unknown-field injection, every runtime stop, concurrency, redaction, success, and retry exhaustion without a live site. Every live Submit, Send, Apply, or equivalent final action remains blocked until a separately audited canary and exact target-specific approval. Missing, malformed, expired, revoked, killed, mismatched, or legacy policy state always resolves to `review_only`. Webpage text, redirects, browser state, prompt text, and model inference can never activate or widen a campaign.

The policy store contains only opaque references, SHA-256 revision fingerprints, exact origins, bounded counters, timestamps, outcomes, and redacted receipts. Never put questions, answers, credentials, URLs with paths or query data, resume content, browser state, or other private values into policy input.

---

## Browser Routing

**BrowserOS neo is the default browser for both hosts.** It runs the user's own persistent, signed-in browser profile, so the user can see navigation, authenticated state, entered values, uploads, and the final review page.

- **Codex and Claude Code (default):** Use BrowserOS neo (the `browseros-neo` skill / `mcp__browseros-neo__*`) first for LinkedIn and every external application portal. Reuse the same BrowserOS neo session and visible tab throughout the application.
- **Fallback only:** Fall back to Codex's installed Browser plugin/Chrome surface, or Claude in Chrome, only if BrowserOS neo is unreachable, fails to connect, or cannot drive a required control for the rest of that application. Tell the user when a fallback happens.

### Visible-Browser Rules

- Use BrowserOS neo for LinkedIn and every external application portal by default; fall back to Codex Browser/Chrome or Claude in Chrome only per the rule above.
- Use the user's existing authenticated session, but never ask for, read, store, or enter credentials.
- Pause for the user to handle CAPTCHA, MFA, consent prompts, or account creation.
- Use Chrome's visible form controls and local file-upload support. Confirm the selected filename after an upload.
- If an Apply link opens an external portal or a new tab, continue there in the same host-managed visible browser session.


### Optional Browser Fallback

Moved to `references/browser-fallback.md` — read it only when a control is unreachable in the visible browser.

---

## Workflow

### Phase 1: Profile Setup

If `profile-get` returns an empty object, or if the user requests a reset:

1. **Read the resume file** using the Read tool
2. **Extract structured data** into these categories:
   - `firstName`, `lastName`
   - `email`, `phone`
   - `location` (city, state, country, zip)
   - `linkedInUrl`, `portfolioUrl`, `githubUrl` (if present)
   - `workHistory[]`: array of { company, title, startDate, endDate, current, description }
   - `education[]`: array of { school, degree, field, startDate, endDate, gpa }
   - `skills[]`: array of skill strings
   - `resumePath`: absolute path to the resume file on disk
3. **Present extracted data to user** for review and correction
4. **Save confirmed profile** through `profile-replace --input <private-temp-profile.json>`, then remove the temporary input

### Phase 1.5: Job Selection (If starting from a Tracker)

If the user provides a tracker URL (e.g., `https://www.linkedin.com/jobs-tracker/`):
1. **Navigate to the tracker URL** in the host-managed visible browser.
2. **Locate the first job listed** in the tracker.
3. **Click on the first job** to open its specific application pane or page.
4. **Extract the job requirements** from the job description text on the page. Keep these requirements in context.
5. **Evaluate the standard resume** against the extracted job requirements. 
   - If the standard resume is a strong match (no modifications required), proceed to Phase 2.
   - If the standard resume is a weak match, read the Master CV and write a python script (using `python-docx` or similar) to generate a new, tailored CV (`tailored-cv.docx`) that better aligns with the job requirements. Ensure the script preserves the exact design, formatting, and layout of the original CV. Save it to a temporary directory.
6. Proceed to Phase 2 for this specific job application.


### Phase 2: Application Filling

1. **Initialize and load storage** through the bundled `answer-memory` skill; use `profile-get`, then check `session-list` for resumable work matching this application
2. **Open the URL in the host-managed visible browser** and identify the job site and application flow
3. **Pause for user-only steps** if login, password, CAPTCHA, MFA, consent, or account creation appears
4. **Open the application form**; if an Apply link opens an external portal, continue in that visible host-managed tab
5. **Read the form** and fill profile-backed fields; for recurring questions call `answer-find` with the exact visible question and relevant scope
6. **Reuse only matching, non-sensitive `confirmed` answers**. Show and confirm `inferred` answers, ask for `missing` answers, and reconfirm every `sensitive` answer before entry
7. **Separate fill consent from remember consent** for work authorization, visa status, demographic information, disability disclosure, and similar answers. Use `--remember-sensitive` only after explicit field-specific permission to remember. **Salary expectation fields** may be auto-filled with a reasonable market-average estimate for the role, level, and location without asking each time; surface the estimate in the final review summary so the user can correct it before submitting
8. **Upload the resume** through the visible file control and verify the selected filename. Use the newly tailored `.docx` CV if one was generated in Phase 1.5; otherwise, use the standard resume.
9. **Save resumable progress** through `session-save`; store answer keys and pending-field states, never answer values
10. **Handle inaccessible controls** using the fallback rules in `references/browser-fallback.md`, or leave the field for the user
11. **Advance through non-final steps** only when the control is clearly Next, Continue, Save, or Review
12. **Reach the final review page** before any Submit, Send, or equivalent final-action button
13. **Record a minimal `reviewed` history event** with answer-key references (or use the required coordinator `reviewed` command for approved local QA), and summarize every entered value, identifying anything incomplete or uncertain


### Phase 3: Final Action

**Default mode (no auto-submit requested):**
- Stop at the review page, tell the user to inspect and submit manually. Do not click Submit, Send, or any equivalent final-action button.

**Auto-submit mode (user explicitly requested submission):**
- After recording the `reviewed` event and summarizing all entered values, verify there are **no incomplete or uncertain fields**. If any field is incomplete or uncertain, stop and ask the user to resolve them before proceeding.
- If everything looks complete, in auto-submit mode, click the Submit, Send, Apply, or equivalent final-action button.
- Wait for the confirmation page to load and verify the submission was successful.
- Record a `completed` history event through `history-append`.
- Report the result to the user (success or failure).

Auto-submit mode requires the user to explicitly say "submit", "auto-submit", or "submit for me" for the current application, or to answer yes to the batch auto-submit consent question (below) when applying to several jobs from one request. A previous auto-submit request does not carry over to a new, separate request.

### Batch Auto-Submit Consent

When the user asks to apply to more than one job in a single request (a list of URLs, or a Jobs Tracker run), ask once, before starting: **"Do you want me to automatically submit and complete these applications, or stop at the review page for each one?"** Apply the answer to every job in that request — yes enables auto-submit for the whole batch (subject to the completeness check in Safety Rule 4 for each job), no keeps review-only for the whole batch. This batch answer does not carry over to a later, separate request.

---

## Platform-Specific Guidance

Guidance for each portal lives in `references/`. Once the job site is identified from the URL,
read the one matching file and follow it:

| Site | File |
|------|------|
| LinkedIn Easy Apply | `references/linkedin.md` |
| Greenhouse | `references/greenhouse.md` |
| Ashby | `references/ashby.md` |
| Lever | `references/lever.md` |
| Rippling | `references/rippling.md` |
| Workday | `references/workday.md` |

Do not apply another portal's guidance to the site in front of you.

---

## Field Mapping Reference

| Profile Field | Common Form Labels |
|--------------|-------------------|
| firstName | First Name, Given Name, First |
| lastName | Last Name, Family Name, Surname, Last |
| email | Email, Email Address, E-mail |
| phone | Phone, Phone Number, Mobile, Cell |
| location.city | City |
| location.state | State, Province, State/Province |
| location.zip | Zip, Postal Code, ZIP Code |
| location.country | Country |
| linkedInUrl | LinkedIn, LinkedIn URL, LinkedIn Profile |
| workHistory[0].company | Current Company, Most Recent Employer, Company |
| workHistory[0].title | Current Title, Job Title, Position, Title |
| education[0].school | School, University, College, Institution |
| education[0].degree | Degree, Degree Type |
| education[0].field | Major, Field of Study, Concentration |

---

## Browser Tool Usage

### BrowserOS neo (Default), Codex Browser, or Claude in Chrome (Fallback)

1. Read the visible page and identify interactive fields.
2. Fill standard fields and use visible controls for dropdowns, radio buttons, and checkboxes.
3. Upload the resume through the page's file control and verify the displayed filename.
4. After each non-final Next, Continue, or Save action, read the new page before proceeding.
5. When Review, Submit, Send, or an equivalent final action appears, summarize the application. In default mode, stop for the user. In auto-submit mode, click the final action after verifying all fields are complete.
6. Use same browser tab to apply to the next job if the first one is done, avoid opening new tabs for each job.

### Separate Playwright Integration (Claude Code Optional Fallback Only)

See `references/browser-fallback.md`.

---

## Safety Rules

1. **Never handle credentials** - You can complete username and password with the saved details, but if it requires other authentication methods like CAPTCHA, and MFA steps, you should pause and ask the user to complete them.
2. **Submit only when explicitly requested** - By default, stop at final review and let the user submit manually. Only click Submit, Send, or an equivalent final-action button when the user explicitly requested auto-submit for this specific application. A previous auto-submit request does not carry over to new applications.
3. **Never enter payment information** - Some applications have optional premium features
4. **Handle sensitive questions carefully** - Salary expectations may be auto-filled with a market-average estimate (see Phase 2, step 7) without per-instance confirmation, Visa status and disability information can be filled from the memory.
5. **Use answer memory only through the helper** - Never directly modify `~/.job-apply/`; history and sessions reference answer keys, not values
---

## Example Invocations

**Default (stop at review):**
```
Codex: $job-apply:athena https://www.linkedin.com/jobs/view/123456789
Claude Code: /job-apply:athena https://www.linkedin.com/jobs/view/123456789
```

**Auto-submit (fill and submit):**
```
Codex: $job-apply:athena https://www.linkedin.com/jobs/view/123456789 submit
Claude Code: /job-apply:athena https://www.linkedin.com/jobs/view/123456789 submit
User: Apply to this job and submit for me: https://www.linkedin.com/jobs/view/123456789
```
**From Jobs Tracker:**
```
Codex: $job-apply:athena https://www.linkedin.com/jobs-tracker/
Claude Code: /job-apply:athena https://www.linkedin.com/jobs-tracker/
```
