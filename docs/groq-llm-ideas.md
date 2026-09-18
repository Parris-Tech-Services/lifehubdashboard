# Groq LLM integration ideas (LifeHub)

This document expands on ideas for non-intrusive Groq (LLM) flavor integration across LifeHub. The goal: add delight and helpful micro-copy without leaking user content or creating brittle dependencies. All Groq usage must be:

- gated behind a user toggle per-feature (and a global Groq toggle),
- opt-in (the API key is stored locally only),
- rate-limited and token-capped, and
- fail-safe: provide canned fallbacks when no key or a failure occurs.

This file contains: short feature descriptions, privacy constraints, recommended prompts, UI placement, localStorage keys, and a pragmatic implementation roadmap (small, incremental tasks). Use this as the product + engineering spec.

## Privacy & safety rules (non-negotiable)
- Never send file contents or sensitive text to Groq. Only send metadata (file names, ages, simple stats) or short user-provided prompts.
- Persist the API key only in localStorage (encrypted storage is possible but out of scope for now). Indicate clearly in the UI that the key stays local.
- Keep token and request caps (e.g., maxTokens ≤ 180 for flavor lines, ≤ 60 for one-liners) and add a simple cooldown (e.g., 1 request / 5s per feature).
- Provide explicit UI opt-outs per feature (tavern, dice, npc chat, quest generator).

## Suggested localStorage keys and toggles
- `lifehub_groq_key` — the saved API key (string).
- `lifehub_groq_enabled` — global boolean toggle if the user wants any Groq usage.
- `lifehub_groq_tavern_enabled` — tavern flavor toggle.
- `lifehub_groq_dice_enabled` — dice flavor toggle.
- `lifehub_groq_quest_enabled` — quest generator toggle.
- `lifehub_groq_last_call` — timestamp of last call to enforce cooldowns (optional per-feature keys also ok).

## Feature ideas (with example prompts and safe payloads)

1) Tavern Talk (quick win)
	 - When enabled, call Groq once on load and every N seconds to produce a one-line flavor. Send only: small stats object and current daily modifier.
	 - Prompt (system): "You are a tavern bard dropping a one-line tavern talk for a productivity dashboard. Keep it under 20 words, playful, reference chores/stats lightly. Avoid instructions. One line only."
	 - Prompt (user): `Stats: ${JSON.stringify(stats)}. Daily modifier: ${modifier || 'none'}. Reply with one tavern line.`
	 - Fallback: rotate a small static list of canned tavern lines.

2) Dice roller flavor (quick win)
	 - After a roll (loot/encounter), optionally ask Groq for a short 1-line flavor text using the roll context (e.g., "rolled 2d6+3 for loot: coin, ring"). Keep maxTokens small.
	 - Prompt (system): "You are a playful GM narrator. Provide a 1-sentence flavor line for a dice or loot roll. Keep it under 18 words. Do not repeat the roll text."

3) Quest generator
	 - On user request ("Groq reroll"), send constrained metadata: recent file names, counts, and a summary of user activity (number of tasks completed, quick stats). Ask for a short quest: goal + XP reward.
	 - Prompt example: "Generate a one-line daily quest for a productivity dashboard. Input: { files: [...names], tasksCompleted: X, inbox: Y }. Output: short goal and XP reward (e.g., 'File 10 docs — 50 XP')."

4) NPC chat (existing)
	 - Keep the current in-character chat functionality. Add a small "Summarize day" verb that sends only metadata (counts + visible NPC persona) and asks Groq to produce a short summary.

5) Resurface blurbs
	 - When opening a dormant file, optionally ask Groq for a one-sentence "why this matters" using filename and age only. This can be shown inline as a subtle hint.

6) Copilot story-mode (search summaries)
	 - For search queries that are explicitly narrative (e.g., start with "summarize" or "what changed"), call Groq with a list of file names and timestamps. Never send file contents.

## Implementation notes & helper patterns
- Centralize Groq calls via a single helper: `callGroq(messages, { maxTokens, temperature })` which handles keys, retries across candidate models, cooldowns, and errors. (There is already such a helper in `dashboard.js`.)
- Provide a UI snippet to set the key and toggles (already present). Show clear status and model info when a call succeeds.
- For each feature, provide a local fallback list so users without a key still get a good experience.

## Minimal incremental roadmap (I can implement these in order)

Phase A — quick wins (small, low-risk)
	1. Tavern Talk: wire the existing `groqTavernLine()` to the tavern panel with a toggle and cooldown. (Already partially implemented; add toggles and fallback rotation.)
	2. Dice flavor: wire `groqDiceFlavor(text)` to the dice/loot roll flow (honoring toggle and token caps).

Phase B — per-request UX and tooling
	3. Quest generator button + UI: button that collects metadata and calls Groq for a single-line quest. Persist last generated quest.
	4. Resurface blurbs: hook into file-open events to optionally show a Groq blurb.

Phase C — advanced but still local-first
	5. Copilot story-mode: when a narrative search is detected, call Groq with metadata and show one-line summary.
	6. Analytics: add a small usage meter (calls per day) and warn when close to a soft cap.

Phase D — polish
	7. Accessibility: ensure ARIA labels & focus flows for Groq dialogs and key-entry forms.
	8. Tests: add unit tests for the `callGroq` helper (mock fetch) and jsdom tests for tavern/dice fallbacks.

## Example UI wiring (pseudocode)

The dashboard already contains `callGroq`, `groqTavernLine`, and `groqDiceFlavor` helpers. A minimal wiring looks like:

```js
if (localStorage.getItem('lifehub_groq_tavern_enabled') === '1') {
	setInterval(() => {
		const last = Number(localStorage.getItem('lifehub_groq_last_call') || '0');
		if (Date.now() - last > 5000) {
			groqTavernLine().then(() => localStorage.setItem('lifehub_groq_last_call', String(Date.now()))).catch(()=>{});
		}
	}, 7000);
}
```

## Next steps I can take now
1. Implement Tavern Talk toggle + cooldown + fallback rotation and ensure UI shows when Groq is used.
2. Wire dice flavor to the dice roll flow and respect a per-feature toggle and small token limit.

If you'd like me to proceed, say "Do Tavern + Dice" and I'll:
- Update `docs/groq-llm-ideas.md` (done), add toggle UI and persistence if missing, implement the feature wiring in `dashboard.js`, run syntax checks and small jsdom tests, and report back the files changed and how to try it locally.

If you prefer a different pair from the roadmap (e.g., Quest generator + Resurface), tell me which and I'll start there instead.

