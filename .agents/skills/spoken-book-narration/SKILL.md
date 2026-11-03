---
name: spoken-book-narration
description: Adapt Understanding people chapters and reference entries into spoken lessons, then produce paced Andrew narration with explicit paragraph and reflection pauses. Use for writing, revising, producing or reviewing book audio.
---

# Spoken book narration

Read `AGENTS.md`, `docs/page-narration.md`, and the canonical written entry first. Keep concepts before examples and preserve the qualifications attached to research and safety advice.

## Write for a listener

- Author a spoken script in `audio/spoken/SLUG.json`. Do not extract a web page and assume it is a listening script. Keep written content and audio as complementary formats of the same concept.
- Lead with the idea and why it matters. Connect paragraphs with natural transitions. Explain a technical term before depending on it. Clearly introduce each new fictional example; use a few examples to reinforce the explanation.
- Do not read UI labels, repeated headings/definitions, table column names, link text, “Go deeper”, note controls, bibliography entries, DOI strings or author–year fragments. Convert a useful table into a concise explanation or comparison.
- Introduce evidence conversationally: who reviewed or studied what, what it supports, and the qualification that affects the listener's judgment. Say a year when its date matters. Keep full citations and source links on the written page. Omitting a formal citation from speech must not omit the finding's limits or make an editorial suggestion sound validated.
- Treat lists as explanations. Use short sentences where helpful without making every sentence a separate, staccato clip. A spoken paragraph should carry one connected thought, normally two to four sentences.
- Give the listener a useful question, time to think and a restrained example answer. Keep longer written exercises and supplementary research optional on the page; explicitly say where to find them. Do not recite all hidden disclosures and old note panels.
- Preserve agency, uncertainty and support boundaries. A family resemblance is not a genetic diagnosis; a possible motive is not a finding about a person; respecting a refusal can be success.

## Produce actual pauses

- Use `en-US-AndrewMultilingualNeural` at the agreed rate unless the user chooses another voice. Do not claim the service identifies its underlying model.
- Keep each spoken paragraph as its own synthesis input. Never flatten several paragraphs into whitespace-separated text or split a request in the middle of a sentence.
- Insert PCM silence explicitly. Typical gaps are 800–1,000 ms between thoughts, 1,500–1,800 ms between topics, about 3,000 ms after a reflection question and at least 8,000 ms for a short exercise. Explain that listeners can pause the player for longer. Choose gaps for meaning, not a large constant delay after every sentence.
- Keep natural pauses inside each paragraph. Trim only excess leading/trailing silence, retaining guards around speech. Do not remove internal silences or use punctuation as a substitute for actual timing.
- Use `scripts/synthesise_spoken.py SLUG ...`. Its output updates only explicitly selected, authored lessons. Caches and raw takes stay outside Git. Normal builds must not call the speech service.
- Bind the script, its canonical written sources, its rendered-page fingerprint, the audio and transcript with checksums. Preserve section anchors and existing practice-note IDs.

## Review the result

- Check script fidelity and clarity before synthesis. Look particularly for citation fragments, repeated labels, unsupported brain explanations, flattened lists, missing qualifications and questions with no practical next step.
- Check provider word alignment, complete decode, actual silent gaps, section times, loudness and a matching transcript. Then check playback, seeking and downloads under the Pages project path.
- Automated word/file/browser checks cannot establish naturalness or approve a voice. Listen critically if an audio-listening capability is available. Otherwise say what was measured and provide working pilots for the user to hear; do not claim to have listened.
- For a broad quality revision, develop representative pilots first. Do not mass-regenerate other pages merely because technical checks pass. Stay within the agreed scope, and retain existing page URLs and learning records.

This is repository-local guidance. It is not an installed cloud skill, a new speech model, or a guarantee of human-sounding synthesis.
