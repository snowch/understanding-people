# Current coverage

The 8 November expansion brings both voices to 161 substantive pages, adding 25 references and refreshing two guides. The other 134 recordings per voice remain unchanged. New reference MP3s stream from the immutable release and remain on demand; transcripts stay in Pages. See [narration expansion](narration-expansion.md). The details below record the earlier 136-page second-voice rollout.

# Narrator choice and reading preferences

The user authorized Jenny as a second full-book narrator on 5 November 2026. Both Andrew (`en-US-AndrewMultilingualNeural`) and Jenny (`en-US-JennyNeural`) cover all 136 substantive book/reference pages. Settings is a utility page with controls and previews, not a new learning node or narrated chapter.

## Reader experience

Open Settings from any header or expand Choose a section beside a lesson to find Voice settings. A 25-second preview uses the actual Chapter 1 recording; it does not change the selected narrator. Choose a voice and starting playback speed using native radio/select controls. Changes save automatically in this browser on this device. Every main lesson also has a voice selector.

Changing narrator pauses playback, updates the duration, section buttons, MP3 and transcript links, and retains an approximate place within the same section. The listener presses Play to continue. A section chosen after switching replaces that retained position. After a finished lesson, changing voice starts afresh. Download filenames identify the narrator. Recordings have independent timings; Andrew's timestamps are never used to seek within Jenny. Earlier optional confirmation-bias recordings retain their original voices and controls.

Preferences are scoped to the book's installation path in localStorage, versioned separately from practice notes. Reset restores Andrew and normal speed without deleting notes. Other tabs receive preference updates without starting playback. Corrupt or unknown values fall back to defaults; blocked/full storage leaves the current page usable with a visible explanation. Preferences do not sync between devices. No personal notes, credentials or microphone data are used.

The header, back-to-reading link, native Andrew player and direct Jenny MP3 links remain usable without JavaScript. Saving preferences, section switching and preview buttons require JavaScript. Return links are checked for the book's own origin/path rather than accepting an external destination. Audio remains on demand and is excluded from offline precaching; Settings and reading preferences work with saved offline text, while recordings need an explicit download for offline listening.

## Content and production

Canonical `audio/spoken/*.json` files remain unchanged. `spoken_narration.for_voice` copies a script and selects the authorized voice; prose, research qualifications, source bindings and requested pauses remain identical. Every Jenny transcript matches its Andrew counterpart. New MP3s retain the same pacing/word verification, waveform-gap checks and normalization policy. Jenny's independent durations total approximately 10.05 hours. Technical checks do not establish a human listening judgment.

`scripts/narration_voices.py` registers authorized voice IDs, output paths and bitrates. Andrew keeps `audio/narration-manifest.json` and all existing `assets/media/narration/` URLs. Jenny uses `audio/narration-jenny-manifest.json` and `assets/media/narration/jenny/`. Andrew's 136 recording/transcript pairs and manifest are preserved. Jenny is encoded at mono 24 kHz/80 kbps; this keeps both editions comfortably inside the static-site size budget while retaining the source speech and all measured gaps. Cache and intermediate files stay outside Git.

```sh
python scripts/synthesise_spoken.py --voice jenny --all --plan
python scripts/synthesise_spoken.py --voice jenny --all --workers 20 --page-workers 6
python scripts/build.py
python scripts/verify_voice_settings.py
python scripts/verify_spoken_pilots.py --voice jenny --all
python scripts/verify_page_narration.py
python scripts/verify_page_narration.py --voice jenny
```

Normal builds require complete, current editions, verify both sets of source/file hashes and never synthesize audio. Partial production is checkpointed for retry and must not be published. The browser check covers previews, keyboard selection, local persistence, switching while playing, replacement seeks, no automatic fetching, cross-tab updates, safe return paths, storage errors, reset/note isolation and no-JavaScript links. General narration checks retain playback, download, offline text, responsive and light/dark coverage. Use a public base URL to repeat checks after the Pages deployment. Screenshots for Settings presentation review are temporary verification artifacts and are not added to the book.

## Completed local checks

The build passed all links and anchors across 140 routes. All 136 Jenny MP3s passed full delivered-file/transcript checksums, cold section playback and decoded-gap measurements: 1,724 requested pauses. Both narrators passed the 136-page range/transcript/player checks, including no unsolicited MP3 requests, speed, optional-player separation, download, no-JavaScript and offline reading. The original four Andrew pilots also passed their full delivered-file checks.

Settings passed previews without selection, keyboard choice, cross-page/reload and cross-tab preferences, independent voice timings and download names, pause/position retention, replacing a pending seek, restarting a finished lesson, defaults without deleting notes, corrupt/blocked storage, safe return links and offline settings with no MP3 precache. Phone and desktop layouts were inspected in light and dark themes. Installation and shared navigation regressions passed; the navigation check now follows the primary lesson's Listen link, preserving the older optional-audio anchors separately. Twelve existing parser, speech-gap and cache/interruption unit checks passed. The output is approximately 904.3 MB, below the 1 GB Pages budget. All 136 original Andrew MP3/transcript pairs, manifest records and authored scripts remain unchanged.

These are technical and presentation checks. Public deployment and live-URL checks follow publication to main; they do not establish a human listening judgment.

Live testing additionally caught a pending-playback race: replacing a recording could reject its earlier `play()` promise and overwrite the new voice's status with a false error. Playback requests are now superseded explicitly, and intentional aborts are ignored. Deterministic same-task section/voice changes and rapid preview comparisons cover the regression, including the slower public network path.
