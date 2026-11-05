# Spoken narration rollout review — 5 November 2026

The user requested completion of the improved recordings for every page, using appropriate models and effort. The scope is 136 substantive pages. The existing four pilots are preserved; 132 new listening scripts replace the earlier literal page readings. Compatibility notices are not separate lessons.

## Authorship and editorial review

All scripts follow the repository-local spoken narration skill. They are individually authored adaptations of the written material, not HTML extraction or automatic concatenation of reference fields. Source pages and canonical reference JSON remain unchanged.

| Area | New scripts | Drafting | Independent source/text review |
| --- | ---: | --- | --- |
| Foundations, introduction, reading/evidence guidance and conclusion | 15 | GPT-6 Astra, high effort | GPT-6 Astra, high effort |
| Behaviour and relationships | 36 | GPT-6.1 Sol, high effort | Separate GPT-6.1 Sol author/reviewer; additional Astra review of higher-risk material |
| Goals, intentions, responses and collaboration | 25 | GPT-6.1 Sol, high effort | Separate GPT-6.1 Sol reviewer |
| Thinking, personality, emotion, learning and context | 28 | GPT-6.1 Sol, high effort | Separate GPT-6.1 Sol reviewer |
| Clinical vocabulary and sensitive health/developmental contexts | 19 | GPT-6 Astra, high effort | Separate GPT-6 Astra reviewer |
| Resource/support pages and glossary | 9 | Main agent | GPT-6 Astra, high effort |

These are model-based editorial/source-fidelity reviews. They are not specialist review, independent scientific validation or human listening assessments. Research claims remain accountable to the written sources and their recorded access limits.

The reviews checked concepts before examples, clear scenario changes, conversational attribution, method/population limits, practical distinctions, agency and non-diagnostic language. Safety checks covered no provoked retaliation tests, safe existing information, monitored devices/notes, appropriate local support, urgency and the limits of legal/public guidance.

## Corrections made during review

- Chapter 4: made the separate financial-help example explicit before discussing repayment, instead of seeming to return to an unrelated earlier example.
- Chapter 8: restored the actual leading question, distinguishing a suggested answer from an ordinary precise yes/no question.
- Glossary: retained agreement with an action in the autonomy definition, qualified competence in self-determination theory, and avoided implying that the Big Five dimensions are statistically independent.
- Worksheet: restored choosing how and when to review the action before taking it.
- Sources guide: clarified selective rather than systematic coverage, and that checking a bibliographic reference does not establish the latest evidence.

All other scripts completed a separate source/text review without changes being required. No claims of human listening or specialist review follow from that outcome.

## Recording and delivery checks

Andrew's selected voice and rate remain unchanged. Each paragraph is synthesised separately, with real PCM silence between thoughts, topics and reflection. Final MP3s are decoded and every requested gap is measured after encoding. Script, written-source, page-text, audio and transcript checksums bind each published lesson to its source.

The producer now supports explicit whole-script selection with bounded page/request concurrency. It preserves matching existing recordings, serialises manifest checkpoints, waits for successful sibling paragraphs before returning an error, treats corrupt cache metadata as a miss, and atomically publishes cache metadata and final media. Offline regression tests cover interruption, cleanup, cache recovery and sibling completion. Run only one producer process per checkout.

Before publication, require complete 136-page authored coverage, matching manifests/files, preservation of all four pilots, the static link/anchor build, delivered-file/playback/pause checks, responsive and no-JavaScript controls, and relevant written-practice/navigation checks. Public deployment must be verified after pushing to main. Recordings remain on demand, with download and transcript links; no new navigation nodes or independent media pages are introduced.

See `docs/page-narration.md` for commands and the distinction between technical verification and a listening judgment.

## Completed local verification

The completed collection contains 136 authored lessons, 80,816 spoken words, 10.43 hours of audio and 1,724 measured paragraph/topic/reflection pauses. Exactly 132 MP3/transcript pairs replace the earlier page readings. All four pilot scripts, manifest records, MP3s and transcripts remain byte-for-byte unchanged. No canonical chapter or reference text changed, and no cache or intermediate render is included.

The 139-route static build passed all local links and anchors. The narration unit tests and six interruption/cache regression tests passed. `verify_spoken_pilots.py --all` passed for every delivered lesson, including full MP3 checksums, decoded silent gaps, matching transcripts, cold section playback and responsive layouts. `verify_page_narration.py` passed all 136 page/transcript/range URLs and the keyboard, no-JavaScript, playback-speed, download, independent-player, light/dark, print and offline checks. The chapter-revision, practice, navigation, reference-library and confirmation-audio regressions also passed. No screenshots were captured.

These results establish the measured delivery and structural properties, not a human listening judgment. Deployment and public URL checks follow publication to main.
