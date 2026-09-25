# Optional browser fallback (Claude Code only)

Read this only when a specific control cannot be reached in the visible browser.

## Optional Browser Fallback

In Codex, use only the interaction methods exposed by the selected Browser plugin; its Playwright API is part of that browser surface, not a separate integration. In Claude Code, a separate Playwright integration is not required and may be used only when **all** of the following are true:

1. The user already has a Playwright integration configured in Claude Code.
2. Claude in Chrome cannot reach a specific iframe, upload widget, or custom control after a reasonable visible attempt.
3. The fallback does not require transferring login state or credentials.

Use the fallback only for the blocked control, then return to the visible review workflow. If these conditions are not met, explain which field is blocked and leave it for the user to complete manually.

## Separate Playwright Integration (Claude Code Optional Fallback Only)

In Codex, stay inside the selected Browser plugin surface. In Claude Code, if a separate Playwright integration is already configured and Claude in Chrome cannot reach a specific iframe or custom control, it may be used only for that blocked field. Do not require it, do not transfer authenticated state or credentials, and do not use it to activate Submit, Send, or any equivalent final action. If the fallback is unavailable or unsuccessful, leave the field for the user.
