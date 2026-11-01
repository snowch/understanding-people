# Understanding people

A science-informed guide to understanding what drives people—including ourselves.

[Read the book](https://snowch.github.io/understanding-people/) · [Contents](contents.md) · [Evidence standards](evidence.md)

This is a complete first editorial draft: an introduction, twelve developed chapters, a conclusion, reading routes, a practical worksheet, an annotated source list, a glossary, and reading, author and support pages. Chapters include one habit to practise, key takeaways and a compact practice section: recall, one fresh situation and one task for the week. Deeper exercises and selected earlier-chapter recalls are optional, under “More practice”. Local notes are optional too. It has not undergone external subject-matter review.

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

The introduction includes a 1:40 illustrated course overview in `assets/media/introduction/`, using the same accessible player, captions and transcript as the chapters. The unnumbered conclusion, “What to take with you”, follows Chapter 12 in the chapter navigation and reading sequence. It recaps the course, links back to all twelve chapters and offers one short self-check. Keep it separate from the supporting reading tools and preserve the twelve chapter numbers.

Chapters 2–12 include one illustrated explanation video, with a poster, English WebVTT captions and a transcript in `assets/media/chapter-NN/`. Chapter 1 video and audio are paused while its concept-led text is revised; the earlier source assets remain in Git but are excluded from the published output. Chapters 2–12 run roughly 3½–4 minutes each. The build copies these assets and validates their page links, including the posters. MP4 files stream on demand and are excluded from automatic offline caching; chapter text, posters, captions and transcripts remain available offline. Keep the visible fictional-example caption beneath every player. Narration is synthetic (Microsoft Edge Sonia); authored scripts follow the chapter explanations and transcripts link to their source sections. Video review includes source/visual checks, caption timing, full decoding and automated speech recognition; it is not a claim of human listening or external subject-matter review.

With a local server running, `python3 scripts/verify_install.py http://localhost:8000/` checks installation event handling, fallback instructions, responsive layout, app metadata and offline reading. The browser test simulates the native install events; it does not perform an operating-system installation.

`.github/workflows/pages.yml` validates pull requests and publishes pushes to `main` through GitHub Actions. GitHub Pages must use **GitHub Actions** as its source.

## Writing

Edit the Markdown files. Register new pages in `PAGES` in `scripts/build.py`, set their source path in `CHAPTERS`, and update `contents.md`. Keep the chapter anchors in the contents so existing links continue to resolve. Cite research beside the claim it supports and add an annotated entry in `references.md`. Distinguish research findings, interpretations and practical suggestions. All scenarios are fictional teaching examples, not evidence.

Practical reader actions use a sage-green `section.reader-action` panel with a labelled heading and checklist icon. Use `markdown="1"` and an explicit heading ID referenced by `aria-labelledby`. Keep research explanations outside action panels. The styling includes mobile, dark-mode and print variants. General caveats belong in `how-to-use.md`; retain claim-specific qualifications beside the relevant finding.

Use Chapter 1’s revised rhythm: explain each concept in plain English, add a short example, explain how to use it and its limits, then provide evidence near the claim. Keep longer cases optional. Finish with brief key takeaways and one compact “Put it into practice” section. Existing chapters retain their earlier videos until separately revised. Include recall of the chapter’s question, one clearly labelled fresh fictional situation with a single example-answer reveal, and one small task for the week. Ask readers to answer before revealing. The examples offer useful-answer criteria, not scores or proof of long-term retention. Keep any safety distinction needed to choose the weekly task visible.

Put longer exercises and selected earlier-chapter recalls inside closed “More practice” details. Notes are optional and closed too. Preserve existing heading anchors and all fourteen note identifiers so readers can still find links and access saved notes. Optional answers use `details.answer-check`; supporting research detail uses `details.evidence-detail`. Both use native keyboard-accessible summaries and show their contents in print. Keep citations beside the claims they support.

Use `section.key-takeaways` with `markdown="1"` and an `aria-labelledby="key-takeaways"` heading ID; its plain heading and thin divider distinguish the recap from an action. Recap only ideas already explained, preserve evidence qualifications, and include the reader’s own perspective. Supporting pages do not need chapter recaps.

Use direct, everyday English. Prefer concrete questions such as “What did they say?” and “Why do you think they said it?” over abstract shorthand such as “What have you added?” or “Act on the impact”. Explain the idea through an example before naming a technical term. Apply the same standard to headings, exercises and research notes; a short sentence is only helpful if its meaning is clear.

Definitions use an outlined `section.definition` containing a visible Definition label and a semantic definition list (`dl`, `dt`, `dd`). Put each term in `dfn`, link it to `glossary.md#term-id`, and give its chapter definition the ID `definition-term-id`. Include a brief plain-English meaning and a clearly labelled example. Keep research findings, citations and qualifications outside the box in the following text. Related terms may share a box. Add the same meaning and example to the alphabetical glossary, with a link back to the precise chapter definition; update both copies together. Use boxes for terms readers need help with rather than explaining every ordinary word.

When an example changes, say so: “Here is a separate fictional example” or “Returning to [name]”. When an exercise asks readers to use their own lives, state that explicitly. Keep the details of a scenario consistent across its introduction, dialogue and exercises.

Introduce research before discussing it. Name the researcher or team and year, explain what they did (for example, reviewed earlier studies or ran experiments), then describe the finding and its limits. Do not assume “the review” or an author–year citation tells a general reader what work you mean. Use meaningful source links. Preserve scientific qualifications when simplifying language.

Definition examples should show how the concept works, not merely present a situation. Spell out the connection when it could be missed. Distinguish “may happen” from “always happens”; for example, people may be unaware of confirmation bias, but lack of awareness is not required. Keep the chapter and glossary wording identical.

Teach one short recall cue per chapter, with a concrete trigger for using it. Return to the same cue in the weekly exercise. Revisit selected earlier lessons in later chapters through a fresh scenario before showing the answer. Keep new scenarios, reader exercises and returns to the main story explicit.

Weekly notes use a stable marker such as `<!-- practice-notes: week-03 | Find one difficulty you can address -->`. The build renders labelled fields, a return date, download/delete controls and no-JavaScript guidance. Keep note IDs stable so revisions retain readers’ notes. `assets/practice.js` stores one versioned record per exercise and book path in localStorage, with no network transmission. Data is read as text, never inserted as HTML. Saving failures must remain visible. Deletion affects only that exercise; downloads are plain text. Print styles reveal note fields and mirror their full contents without textarea clipping. No reminders or cross-device sync are provided.

With a built site served locally, `python3 scripts/verify_practice.py http://localhost:8000/` checks chapter practice structure, keyboard reveals, note restoration/isolation, export/deletion, blocked and full storage, offline use, responsive layout and printing. This tests the website’s behaviour; it does not measure whether readers learned the material.


## Book/app reference pilot and audio

The [declining-help reference](reference/declining-help.md) is the first developed book/app example. Its authored source is `reference/declining-help.json`; the normal build renders its Markdown with `scripts/build_reference.py`. The private app has an offline snapshot with a source checksum and explicit foundation links. Refresh that snapshot using the app's `tools/sync_book_pilot.py`. Book and app records remain separate; the book gives navigation instructions for the downloaded app and offers its own equivalent note fields. This pilot does not constitute a depth revision of the twelve chapters.

Chapter 1 media is paused. Its previous video and audio assets remain in Git for possible future revision, but the build excludes both `assets/media/chapter-01/` and `assets/media/audio/chapter-01/` from Pages. The old audio-page URL is a short notice linking to the revised text and is excluded from navigation. The normal build no longer calls the audio transcript generator. Production scripts and narration sources are archived context, not the current chapter edition.

`python scripts/verify_chapter_one.py http://localhost:8000/` checks the revised text, media removal, glossary consistency and mobile/desktop layout. `scripts/verify_audio_pilot.py` is the historical audio-production check; it is not a check of the currently published edition. Earlier practice-note IDs remain available in a collapsed panel so the rewrite does not hide existing notes.

## Deeper bias references

`reference/biases.json` is the canonical content for the confirmation-bias and correspondence-bias entries. The build renders both pages through `scripts/build_bias_references.py`; do not hand-edit their generated Markdown. Chapter 1 and the glossary link to them. Each entry explains mechanisms, recognition, limits and possible change, with source links and local practice notes. The app uses a checked-in offline snapshot refreshed with its `tools/sync_bias_references.py`. Public pages link to the private download and explain the access and local-file limitations.

With the book served, run `python scripts/verify_bias_references.py http://localhost:8000/` to check navigation, saved notes and responsive layouts. Sources were checked against publisher, PubMed and institutional research records on 2026-11-01; these classic studies support the stated claims, not a claim of exhaustive literature review or validation of our exercises.

## Optional listening exercise

The confirmation-bias reference links to a 3:50 listen–compare–replay exercise, with two voices, writing pauses, an accessible transcript and local answer fields. `audio/confirmation-bias-exercise.json` is the authored source. `scripts/synthesise_listening.py` generates the final MP3 and manifest; `scripts/build_listening_page.py` generates the page and rejects stale source/audio hashes. The repeated message uses the identical audio segment. See `audio/BUILD-NOTES.md` for production and automated review details.

Run `python scripts/verify_listening.py BASE_URL` against a server supporting byte ranges (as GitHub Pages does) to check playback, replay seeking and saved answers. Core page reading and notes work offline; download the MP3 explicitly for offline listening. Chapter 1’s old media stays removed.

The confirmation-bias reference’s **Listen** section links to both a detailed explanation and the short exercise. The detailed narration is authored in `audio/confirmation-bias-explained.json`; render it with `python scripts/synthesise_listening.py confirmation-bias-explained`. Its page includes section playback, speed selection, the full transcript, nearby research references and an MP3 download. Build checks require the reference’s displayed duration to match the audio manifest. `python scripts/verify_confirmation_audio.py BASE_URL` checks these links, optional loading, section playback and accessible layouts. Audio production caches remain outside the repository.

## Navigation and the reference library

The sidebar has four sections: The book, Reference library, Practice, and About & sources. Only the current section opens automatically. Reference and audio pages show their current topic, recordings and breadcrumb; they are not added as global top-level links. Chapter Previous/Next links follow Introduction → chapters 1–12 → Conclusion. Audio pages link back to their reference entry. Existing URLs and practice-note IDs are preserved.

`reference/catalog.json` defines the reference topics, entries, search descriptions and keywords. `scripts/book_navigation.py` builds the library index and contextual navigation. Recordings are read from each entry’s existing `listenings` metadata in `reference/biases.json`, so titles and durations remain shared with the app. Add a reference to the catalogue when publishing it; do not add individual entries or recordings to the global sidebar. The library is fully readable without JavaScript; `assets/library.js` filters the existing entries locally when available.

Run `python scripts/build.py` for all local-link and fragment checks, then `python scripts/verify_navigation.py http://localhost:8767/understanding-people/` against a local preview. This checks topic search, four-section navigation, breadcrumbs, recording return links, chapter order, mobile layouts and the no-JavaScript fallback.
