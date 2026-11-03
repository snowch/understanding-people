# Book narration

The user chose **en-US-AndrewMultilingualNeural** on 3 November 2026. The first release provided whole-page readings on 136 substantive pages. Listening feedback then identified a production failure: paragraphs were flattened into continuous input and citation/page-label text was spoken literally. Successful file and browser checks had not established listening quality.

## Current scope

Four pages now pilot authored spoken lessons: Chapter 1, confirmation bias, correspondence bias and declining help. Their top player says **Listen to this lesson**. The other 132 page readings remain unchanged; they are the earlier format, not revised lessons. The three earlier audio compatibility notices still route to their parent content and receive no independent narration. No new reference pages, sidebar branches or graph nodes are created for listening.

Before audio work, read and use [the repository-local spoken narration skill](../.agents/skills/spoken-book-narration/SKILL.md). This is local authoring/production guidance, not an installed cloud skill or a new speech model. Representative recordings need a listening judgment before this approach is extended across the library; automated checks alone cannot provide that judgment.

## Write an adaptation

Each pilot's canonical spoken script is `audio/spoken/SLUG.json`. It names its parent page and canonical written sources, and contains connected spoken paragraphs grouped into sections that link to existing reading anchors. Paragraphs are authored for listening, not extracted from HTML.

Explain the concept before the example. Use conversational research attribution that explains what the work supports and its limits. Full formal citations, source links, detailed tables, optional research discussions and longer exercises remain on the written page. Do not read page labels, bibliography strings, link instructions or hidden note controls aloud. The lesson's transcript contains what is spoken, with clearly bracketed directions for longer pauses; it is not presented as the entire written page.

The pilots preserve the written meanings and limits. Confirmation bias concerns the checking process, not proof that a belief is false. Circumstances can matter without excusing harmful behaviour. Family resemblance does not establish a help-refusal gene. Respecting a refusal can be a useful outcome. Main teaching, examples, source links and saved practice notes on the written pages are unchanged.

## Produce actual timing

Requires `edge-tts==7.3.1`, FFmpeg and ffprobe:

```sh
python scripts/synthesise_spoken.py chapter-01 confirmation-bias correspondence-bias declining-help --plan
python scripts/synthesise_spoken.py chapter-01 confirmation-bias correspondence-bias declining-help
python scripts/build.py
```

The producer accepts explicit script names. It does not enumerate the whole book and create new recordings automatically. Only public, authored script text is sent through the configured HTTPS proxy to Microsoft Edge neural TTS. Voice and rate remain Andrew at −2%; the service does not expose its underlying model name.

Every spoken paragraph is a separate synthesis request. Word-boundary text must match the complete submitted paragraph. It is never split mid-sentence or joined to the next paragraph as whitespace. Natural internal pauses remain. Leading/trailing excess silence is trimmed only at the outer edges, retaining guards of 80 and 120 milliseconds around speech.

PCM silence is inserted explicitly: normally 850–1,000 milliseconds between connected thoughts, 1,400–1,600 milliseconds at topic transitions, three seconds after selected reflection questions, and nine or ten seconds for a practice question. The spoken prompt also tells listeners they can pause the player for longer. The choice of gap belongs to the script, not to punctuation or the text extractor.

Final MP3s target −16 LUFS / −1.5 dBTP, mono 24 kHz at 96 kbps. The producer decodes the final MP3 and measures the centres of every requested gap, excluding 80 milliseconds at each edge to allow for codec windows. A missing/non-silent gap fails production. It also verifies full decode, duration and section timing before checkpointing the selected page.

Raw takes, temporary WAV files, intermediate MP3s and logs stay under `/workspace/book-spoken-cache/`, or `BOOK_SPOKEN_CACHE` when explicitly configured. Only final recordings/transcripts, authored scripts, production metadata and code/docs go in Git.

## Integrity and compatibility

The final files keep their existing `assets/media/narration/` paths, mirroring page routes. `audio/narration-manifest.json` preserves records for unchanged pages. A spoken-lesson record binds the script and timing policy, canonical written-source hashes, the rendered teaching fingerprint, MP3/transcript checksums, measured silent gaps and section times.

The normal Pages build is offline and never calls a speech service. It rejects a changed script/source or mismatched final file so an old recording is not silently advertised beside revised teaching. A source change calls for editorial review of the spoken adaptation, not automatic page extraction and synthesis. The old `synthesise_pages.py` retains `--plan` for inventory and legacy functions for inspection; default verbatim production is retired.

Players retain native controls, `preload="none"`, synthetic-voice identification, duration, download, transcript, optional speed and section playback. Script/media URLs use content hashes so browsers request a revised recording. The native player, section read links, download and transcript work without JavaScript. Audio is not precached; the book's text/transcripts and notes remain available offline after saving the book. MP3s can be downloaded explicitly for offline listening.

Earlier chapter videos remain paused. Confirmation bias retains the two existing optional recordings with their original Sonia/Ryan voices, labelled separately from Andrew's new top player. Their old URLs, transcript/research anchors and practice-note IDs are retained. No personal notes, credentials or microphone input are used for narration.

## Verification and its limits

```sh
python scripts/test_spoken_narration.py
python scripts/build.py
python scripts/verify_page_narration.py
python scripts/verify_spoken_pilots.py BASE_URL
python scripts/verify_chapter_revision.py BASE_URL
PEOPLE_NO_SCREENSHOTS=1 python scripts/verify_practice.py BASE_URL
```

The tests check real PCM gaps, preservation of internal silence, script/citation formatting, source/file integrity, spoken-player labels/transcripts, MP3 range delivery, playback/seek, responsive layouts and preserved written practice. The general narration check can start its own local range server; public-URL checks honour the configured HTTPS proxy and accept GitHub's MP3 media type.

Provider alignment, energy measurements, loudness and browser checks do not establish naturalness, pronunciation, scientific accuracy or reader learning. Report exactly which checks ran. Do not claim to have listened when no audio-listening capability was available. Provide working pilots for the user to hear and judge before proposing a larger regeneration.
