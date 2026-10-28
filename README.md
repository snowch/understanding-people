# Understanding people

A science-informed guide to understanding what drives people—including ourselves.

[Read the book](https://snowch.github.io/understanding-people/) · [Contents](contents.md) · [Evidence standards](evidence.md)

This is a complete first editorial draft: an introduction, twelve developed chapters, reading routes, a practical worksheet, an annotated source list, a glossary, and reading, author and support pages. All chapters include one habit to practise, an application check, key takeaways and a weekly exercise with optional local notes. Selected later chapters revisit earlier lessons. It has not undergone external subject-matter review.

The book draws on psychology, sociology, anthropology and decision science. Examples span work, friendship, family life, learning, public life and commercial decisions. Investigative interviewing and deception are assessed against evidence, including the limits of claims associated with the FBI.

## Build

Requires Python 3.11 or later.

```sh
python3 -m pip install -r requirements.txt
python3 scripts/build.py
python3 -m http.server 8000 --directory _site
```

Open http://localhost:8000. The build checks every generated local link and fragment. Static HTML, relative URLs and CSS work under the GitHub Pages project path without JavaScript or external fonts. A small optional script scrolls the current chapter into view within the sidebar.

The left-hand contents lists the introduction and all twelve numbered chapters above the supporting reading tools. All twelve chapters link directly to their text. The sidebar stays visible above 800px, with its own scrolling on shorter screens; smaller screens use an expandable Contents menu. The current page is highlighted in both layouts.

The header's install icon opens the native browser prompt when available, with manual installation instructions otherwise. It is hidden in an installed app. The manifest and PNG icons support installation and home-screen shortcuts; the service worker saves the book for offline reading after its first successful online load. Navigation prefers the network, with the saved edition as an offline fallback. Each build versions its cache from the generated contents and worker code; obsolete caches belonging to this book are removed when the updated worker activates after the old reading windows close. Other books' caches are left alone.

App icons are checked in. To regenerate them from `assets/app-icon.svg`, install Playwright and Chromium, then run `python3 scripts/generate_icons.py`. Normal builds do not need Playwright. The footer uses the same notice as Digital Design: © 2026 Christopher Snow.

Chapter 1 includes the approved illustrated video (5:22), with a poster, English WebVTT captions and a transcript in `assets/media/chapter-01/`. The build copies these assets and validates their page links, including the poster. MP4 files stream on demand and are excluded from automatic offline caching; the chapter text, poster, captions and transcript remain available offline. Keep the visible fictional-example caption beneath the player when updating the embed.

With a local server running, `python3 scripts/verify_install.py http://localhost:8000/` checks installation event handling, fallback instructions, responsive layout, app metadata and offline reading. The browser test simulates the native install events; it does not perform an operating-system installation.

`.github/workflows/pages.yml` validates pull requests and publishes pushes to `main` through GitHub Actions. GitHub Pages must use **GitHub Actions** as its source.

## Writing

Edit the Markdown files. Register new pages in `PAGES` in `scripts/build.py`, set their source path in `CHAPTERS`, and update `contents.md`. Keep the chapter anchors in the contents so existing links continue to resolve. Cite research beside the claim it supports and add an annotated entry in `references.md`. Distinguish research findings, interpretations and practical suggestions. All scenarios are fictional teaching examples, not evidence.

Practical reader actions use a sage-green `section.reader-action` panel with a labelled heading and checklist icon. Use `markdown="1"` on the section and give its heading an explicit ID referenced by `aria-labelledby`. Keep research explanations outside the panels, and make each action concrete. Use “Try this” for short rehearsals within a chapter. Group all “Put it into practice” work at the end, after the application check and takeaways. Give readers one main task; label any extra focus optional rather than presenting several equally required exercises. The styling includes mobile, dark-mode and print variants. General caveats belong in `how-to-use.md`; retain claim-specific qualifications beside the relevant finding.

Before the takeaways, include a “Can you use it?” section with 3–4 questions about a new fictional situation. Use separate closed `details.answer-check` reveals with useful-answer criteria, relevant limitations and a link back to the explanation. Readers answer before revealing; do not claim a score verifies understanding or long-term retention. Then include a “Key takeaways” section containing 3–5 short bullets, followed by weekly practice. Offer one small task; if there are alternatives, explicitly ask readers to choose one. Recap only ideas already explained, preserve evidence qualifications, and include one point about the reader’s own perspective. Use `section.key-takeaways` with `markdown="1"` and an `aria-labelledby="key-takeaways"` heading ID; its plain heading and thin divider distinguish the recap from an action. Supporting pages do not need chapter recaps.

Chapter 1 pairs its explanation video and worked example with one compact practice section after the takeaways. It contains recall of the three questions, one fresh scenario with a single example-answer reveal, and one task for the week. Additional bias exercises are collapsed under “More practice”; all note fields are optional and collapsed. Preserve the three existing note identifiers when editing so readers can still access saved notes. The other chapters retain their longer application checks. Optional answers use `details.answer-check`; supporting research detail uses `details.evidence-detail`. Both use native keyboard-accessible summaries and show their contents in print. Keep citations beside the claims they support, including inside optional evidence notes.

Use direct, everyday English. Prefer concrete questions such as “What did they say?” and “Why do you think they said it?” over abstract shorthand such as “What have you added?” or “Act on the impact”. Explain the idea through an example before naming a technical term. Apply the same standard to headings, exercises and research notes; a short sentence is only helpful if its meaning is clear.

Definitions use an outlined `section.definition` containing a visible Definition label and a semantic definition list (`dl`, `dt`, `dd`). Put each term in `dfn`, link it to `glossary.md#term-id`, and give its chapter definition the ID `definition-term-id`. Include a brief plain-English meaning and a clearly labelled example. Keep research findings, citations and qualifications outside the box in the following text. Related terms may share a box. Add the same meaning and example to the alphabetical glossary, with a link back to the precise chapter definition; update both copies together. Use boxes for terms readers need help with rather than explaining every ordinary word.

When an example changes, say so: “Here is a separate fictional example” or “Returning to [name]”. When an exercise asks readers to use their own lives, state that explicitly. Keep the details of a scenario consistent across its introduction, dialogue and exercises.

Introduce research before discussing it. Name the researcher or team and year, explain what they did (for example, reviewed earlier studies or ran experiments), then describe the finding and its limits. Do not assume “the review” or an author–year citation tells a general reader what work you mean. Use meaningful source links. Preserve scientific qualifications when simplifying language.

Definition examples should show how the concept works, not merely present a situation. Spell out the connection when it could be missed. Distinguish “may happen” from “always happens”; for example, people may be unaware of confirmation bias, but lack of awareness is not required. Keep the chapter and glossary wording identical.

Teach one short recall cue per chapter, with a concrete trigger for using it. Return to the same cue in the weekly exercise. Revisit selected earlier lessons in later chapters through a fresh scenario before showing the answer. Keep new scenarios, reader exercises and returns to the main story explicit.

Weekly notes use a stable marker such as `<!-- practice-notes: week-03 | Find one difficulty you can address -->`. The build renders labelled fields, a return date, download/delete controls and no-JavaScript guidance. Keep note IDs stable so revisions retain readers’ notes. `assets/practice.js` stores one versioned record per exercise and book path in localStorage, with no network transmission. Data is read as text, never inserted as HTML. Saving failures must remain visible. Deletion affects only that exercise; downloads are plain text. Print styles reveal note fields and mirror their full contents without textarea clipping. No reminders or cross-device sync are provided.

With a built site served locally, `python3 scripts/verify_practice.py http://localhost:8000/` checks chapter practice structure, keyboard reveals, note restoration/isolation, export/deletion, blocked and full storage, offline use, responsive layout and printing. This tests the website’s behaviour; it does not measure whether readers learned the material.
