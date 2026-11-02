# Working on Understanding people

Read the editing and build guidance in `README.md` before changing book content or presentation.

## Concepts first, examples in support

- Apply this approach to chapters and reference entries: explain the concept in plain English first, then use a brief, clearly labelled example where it helps readers understand or apply that point.
- The main explanation must stand on its own. As an editorial check, remove the examples mentally: the reader should still understand the concept, its practical use and its limits. Do not make readers reconstruct the explanation from a fictional story.
- Explain what each example illustrates when the connection could be missed. Explicitly identify a new scenario or a return to an earlier one. Examples illustrate ideas; they are not research evidence.
- Keep longer worked cases optional, in a closed, keyboard-accessible disclosure after the relevant explanation. Do not repeat the same lesson through several stories or add an example to every paragraph by default.
- For developed chapters and reference entries, finish the teaching with brief key takeaways and one compact “Put it into practice” section. Put deeper exercises behind optional disclosure. Give readers a place to record answers when asking them to reflect on their own situation.
- Introduce research in everyday language: who did it, when, what kind of work it was, what it supports and what it cannot establish. Keep citations and necessary qualifications beside the claims. Possible explanations are not exhaustive lists, diagnoses or established motives.
- Include the reader's own behaviour and contribution where relevant. Practice should connect observation, an action within the reader's control, and a later review of understanding or collaboration.

## Shared content and verification

- Reference stubs are explicitly unfinished outlines. Keep their status visible in the page, library and sidebar; do not advertise practice, recordings or an evidence review they do not contain. Edit `reference/stubs.json` and `reference/catalog.json`, then build; do not hand-edit generated stub Markdown. Research leads require verification before supporting claims. When developing an entry, remove its stub record, change the catalogue status to `developed`, and author the full entry while preserving its URL and app node ID. Follow the concepts-first rules above for developed content.
- Edit canonical shared sources rather than only generated pages. For declining help, edit `reference/declining-help.json`; the build generates its Markdown. Sync the app snapshot using that repository's `tools/sync_book_pilot.py` and rebuild the app when changing shared content. See `README.md` for other generated entries.
- Preserve existing URLs, heading anchors and practice-note identifiers so revisions retain links and readers' saved notes.
- Run `python scripts/build.py` for content changes; it checks local links and anchors. Use relevant browser checks and visually inspect phone and desktop layouts when changing presentation or interactions. Automated checks verify behaviour and structure, not scientific accuracy or learning outcomes. Documentation-only rule changes need a diff review, not a full browser run.
