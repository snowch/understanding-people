# Single-file offline audiobooks

The user requested a chaptered Android audiobook and a download from the book, emphasizing that separate chapter downloads would be onerous. The download page therefore offers one complete M4B per voice, plus an optional smaller course-only M4B per voice. A person downloads one file for the chosen edition; chapters are internal markers, not separate downloads.

The complete editions contain all 136 authored recordings, beginning with introduction → chapters 1–12 → conclusion, then reference entries in catalogue/topic order, then supporting guides. The course-only editions contain just the first fourteen tracks. Andrew and Jenny remain separate files and have independently measured durations and chapter boundaries. The book and its reference library keep their existing pages and player URLs.

## Packaging

Read the local spoken-narration skill before audio work. This task reuses the approved recordings and performs no new speech synthesis or editorial rewriting. It preserves their decoded audio, including reflection prompts and pauses, and encodes the combined result as mono 24 kHz AAC-LC in an M4B container. Narration remains synthetic and carries the existing voice ID. The book's existing icon is embedded unchanged as cover artwork.

`scripts/package_audiobooks.py` decodes each existing MP3 once to PCM and records exact sample counts and decoded hashes. It derives chapter starts from those sample counts, rather than adding MP3 container durations, which can accumulate encoder-padding errors. All chapter names are embedded in both the QuickTime and Nero chapter representations. Metadata is placed before the audio for fast start/seeking. Each file receives the audiobook media-kind tag and author, voice and edition metadata.

The source MP3s, narration manifests, authored scripts, written teaching and personal reading notes are untouched. `audio/audiobook-manifest.json` records provenance, exact ordering and sample boundaries, each final checksum/size/duration and immutable release URLs. The normal website build verifies catalogue/source bindings and never calls FFmpeg or TTS. A narration change requires an explicit new audiobook edition and manifest update; do not silently serve a stale bundle as the current book.

```sh
python scripts/package_audiobooks.py --release-tag audiobooks-2026-11-07
python scripts/build.py
```

Large release files are written to `/workspace/audiobook-release/`; temporary PCM/metadata stays under `/workspace/audiobook-packaging-cache/`. The combined WAVs are removed after encoding. Neither directory is inside the repository or Pages output. Keep final M4Bs, checksum list and a copy of the manifest in the release artifacts, not in Git or the approximately 905 MB website. Release hosting avoids exceeding the Pages size budget or duplicating narration in its offline cache.

## Validate and publish

If the session credential cannot authenticate to `uploads.github.com`, the explicit `audiobook-build-*` tag workflow can reproduce the approved files on GitHub Actions and upload them with the repository token. It pins the Debian FFmpeg package used for the approved build and requires exact file sizes and SHA-256 matches before any upload. It only uploads to an existing draft release; publishing and public-download verification remain separate steps. Push the build tag only when intentionally running this production job.

The packager verifies AAC-LC/mono/sample rate, embedded artwork, media kind, duration, fast-start placement, both complete chapter tables and full audio decode. Browser checks exercise actual M4B playback and cold chapter seeks with byte-range delivery, as well as the download page's responsive layout, names, scope, single-file links, preference highlighting, no automatic downloads and no-JavaScript links. These checks establish packaging and delivery properties; they are not a listening assessment or a test on a physical Android device.

Use an immutable release tag. Complete and review files/page/manifest locally, commit the source on main, then push the tag pointing to that commit. Create the release as a draft, upload the four verified M4Bs, `SHA256SUMS.txt` and `audiobook-manifest.json`, and verify the asset names/sizes/checksums before making the release public. Publish and verify its public downloads before pushing main, so the Pages update cannot expose links to unavailable draft assets. The release tag and main then point to the same source commit. Do not overwrite earlier published editions in place.

After main's Pages deployment succeeds, verify the live download page, the single-file links, expected public response sizes and representative byte ranges. The M4Bs belong to GitHub Releases, so they must not be precached by the book's service worker. No GitHub account is needed for public release downloads.

## Reader guidance

Keep `.m4b` intact and put each downloaded edition in its own book folder, for example `Audiobooks/Understanding people (Jenny)`. In Smart AudioBook Player choose the parent `Audiobooks` folder as the library root, then refresh. This avoids treating different voices or editions as sequential parts of one book. Download before a journey and leave written/on-screen exercises until parked. Chapter markers and resume are handled by the audiobook app; the website does not read the app's bookmarks or sync personal notes into the audio.
