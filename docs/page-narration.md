# Page narration

The user selected **en-US-AndrewMultilingualNeural** on 3 November 2026 and explicitly requested voice narration for each book page. This replaces the earlier restriction on creating these recordings. The previous twelve-voice audition was evaluation material; this request selects Andrew for publication.

## Reader experience

All **136 substantive pages** receive one Andrew player below the title: introduction, twelve chapters, conclusion, reference entries, library, research/source pages, glossary, worksheet, reading/support and author pages. The three earlier audio compatibility notices remain routes to their current parent pages and have no independent narration. No extra navigation pages or map nodes are created for listening.

The warm paper, forest and sage theme is shared with the book. Each player has native controls, `preload="none"`, synthetic-voice identification, duration, an MP3 download and an exact plain-text spoken transcript. JavaScript adds speed selection, section playback and coordination so only one recording plays at a time. Section read links, the native player, transcript and download remain available without JavaScript. The section list starts closed and scrolls when long.

Audio is not precached by the service worker. Reading and the spoken transcripts remain available offline after the book is saved; listeners explicitly download MP3s for offline playback. No personal notes, API keys, microphone data or browser activity are sent for narration.

Earlier videos remain paused. Confirmation bias retains its existing detailed explanation and guided listening exercise as distinct optional recordings; those recordings and their research/transcript anchors are preserved. Their original Sonia/Ryan voices have not been represented as Andrew.

## What is spoken

`scripts/page_narration.py` extracts the authored main reading text from the built page, in order. It retains explanations, examples, research limitations, source labels, definitions, key takeaways and optional exercises. Tables are spoken row by row with their column headings. Navigation/search controls, scripts, form controls, reader-entered notes, recording controls and the transcripts of other recordings are excluded. Arrows are rendered as “then”; ampersands as “and”. Plain text and punctuation are normalized for speech without rewriting the research claims.

Before an example-answer reveal the narrator asks the listener to pause and consider their answer. Optional deeper practice is announced. Where a writing form occurs, the listener is told that optional notes are available on the page. This is a reading of the page, including its optional practice, rather than a newly authored lecture or a validated teaching assessment.

## Production

Normal builds require only the existing book dependencies and never call the TTS service. Production requires **edge-tts 7.3.1**, FFmpeg and ffprobe:

```sh
python scripts/synthesise_pages.py --plan
python scripts/synthesise_pages.py --workers 8
python scripts/build.py
```

The first command builds the current public text and writes a production plan under `/workspace/book-page-audio-cache/`. Set `BOOK_PAGE_AUDIO_CACHE` to use another task-specific cache directory. The production command sends only authored public narration through the configured HTTPS proxy to Microsoft Edge neural TTS. The requested voice is checked against the current catalogue. The service does not identify its underlying model; do not claim these recordings use Qwen or an OpenAI model.

Rate is **−2%**, matching the selected audition setting. Requests are split into manageable chunks; provider word-boundary text must match all words submitted for each chunk. Completed chunks and page records are cached by content/voice/rate so interruption does not require restarting the book. Network failures are retried; failed pages are reported rather than presented as published. Cached successes remain reusable.

Final MP3s target −16 LUFS / −1.5 dBTP, mono 24 kHz at 96 kbps. FFmpeg decodes each final file before it is accepted. Only the final MP3s, transcripts, production manifest and code/docs belong in Git. Raw chunks, partial outputs, catalogues, logs and intermediate renders stay outside the repo.

Files live in `assets/media/narration/`, mirroring the page routes. `audio/narration-manifest.json` records the voice, service/client version, rate, timestamp, exact spoken-text fingerprint, file hashes, duration and section times. Audio, transcript and playback-script URLs carry content hashes to refresh browser caches when those files change. The normal build verifies that every recording matches its current text/anchors and that its audio and transcript hashes match. A stale page fails with a production command to run; the build does not silently advertise an old recording beside changed teaching.

## Verification and limits

```sh
python scripts/test_page_narration.py
python scripts/build.py
python scripts/verify_page_narration.py
PEOPLE_NO_SCREENSHOTS=1 python scripts/verify_practice.py BASE_URL
PEOPLE_NO_SCREENSHOTS=1 python scripts/verify_navigation.py BASE_URL
python scripts/verify_chapter_revision.py BASE_URL
python scripts/verify_reference_library.py BASE_URL
PEOPLE_NO_SCREENSHOTS=1 python scripts/verify_confirmation_audio.py BASE_URL
```

The narration browser check starts its own local byte-range server under `/understanding-people/` when no URL is supplied. It can also check the deployed base URL. It checks every page's player, transcript, media URL/range response, hashes and anchors; representative playback, cold section seeking, speed, download, keyboard/no-JavaScript operation, responsive light/dark layouts, print hiding, non-overlapping existing audio and offline text. It creates no screenshots or recordings.

These checks verify matching text, decodable media and browser behaviour. Provider word alignment cannot establish pronunciation, naturalness, scientific accuracy or whether a listener understood the material. The recordings use synthetic speech and are identified as such on every page.
