# Search by meaning

The Search page combines passage-level sentence embeddings with local BM25 keyword matching across the 136 reading pages: chapters, references, glossary and supporting guides. Search is a utility, not another lesson or graph node. The reference library retains its instant catalogue filter and links to the whole-book search.

## Reader experience

Readers can describe a situation without knowing its technical name. One result per page shows an original passage and heading, with Read, Listen and Practise links when available. Six results appear first; more remain optional. Search retrieves existing writing; it does not generate interpretations, establish motives or diagnose people. Clinical reference material is labelled. General questions favour behavioural explanations, while named clinical terms remain searchable. Catalogue and bibliography pages receive less weight for ordinary questions and remain available for resource/source searches.

Bare short terms are phrased as definition questions for the sentence model; the reader's original query is retained. A small reviewed navigation vocabulary in `assets/search/query.mjs` bridges matriarch, patriarch, peacemaker and scapegoat to existing topics, in both whole-book search and the library filter. The UI gives the term's ordinary meaning, explicitly says there is no dedicated reference article, and labels the related readings Related topic. Glossary definitions can appear alongside those readings; their Listen in context links lead to the relevant parent lesson. These are editorial reading connections, not claims that the target passage defines the role or that a role implies harmful behaviour. Matriarch and patriarch use the same neutral family-role destinations. Unknown words are not assigned invented definitions, the similarity threshold is retained, and a future dedicated entry takes precedence over the bridge. This vocabulary is not an exhaustive dictionary and does not add reference pages or narration.

Keywords return first. Meaning search is selected by default but starts only on submission; unchecking it leaves quick keyword search. A visible note states the first-use download (about 47 MB). Progress, stop, clear, empty results, failure recovery and no-JavaScript browse links remain available. Semantic-file failures must preserve working keyword results. Input uses no form field name or URL query parameter. The application does not store queries in localStorage, browser history, analytics or a server. No API key or remote inference is used.

## Licensed local engine

The engine is quantized `Xenova/all-MiniLM-L6-v2` at the immutable revision in `assets/search/engine.json`. Mean pooling, unit normalization, a 256-token limit and 384 dimensions are shared between production and browser inference. The self-hosted Transformers.js 3.8.1 bundle and matching ONNX Runtime Web WASM run in a dedicated worker with one thread, without WebGPU, SharedArrayBuffer or special Pages headers. Remote model loading is disabled.

Model weights, tokenizer, runtime and WASM are in `assets/search/`. `engine.json` records original URLs, versions, sizes and SHA-256 values; the build validates them. Apache-2.0/MIT licenses and ONNX Runtime third-party notices are retained. `assets/search/NOTICE.txt` records attribution. Normal builds need only the existing Python build dependencies and never download a model or compute embeddings. Search changes no teaching, research, narration, recordings or saved-note identifiers.

## Passage and vector freshness

`scripts/book_search.py` parses built prose into heading-linked, overlapping passages, excluding navigation, controls, note fields, audio transcripts and duplicate cross-reference/bibliography sections. It preserves paragraph boundaries and anchors. The index contains original book text, never reader-entered notes. `scripts/prepare_search.py` explicitly embeds passages on CPU using the checked-in model/tokenizer and stores signed-int8 rows in `vectors.bin`. Cosine comparisons normalize each row at retrieval time.

`vectors.json` binds the exact passage catalogue, engine and vector bytes. The normal build recreates the catalogue and rejects stale vectors. The browser checks vector length and SHA-256 before meaning search; failure leaves keywords working. The entry script, ranking module, worker, metadata and vectors carry a build version to avoid mixing HTTP-cached editions.

When indexed prose changes, update approved writing/narration through their existing workflows, then use a project-local production environment:

```sh
python -m pip install -r requirements.txt -r scripts/search-requirements.txt
python scripts/prepare_search.py --rebuild
python scripts/build.py
python scripts/verify_search.py --screenshots
```

`--rebuild` renders a staging edition that skips only the vector-freshness gate; reading/narration checks remain. Always finish with the normal build before publishing. Production caches and temporary screenshots stay outside Git. This workflow synthesizes no speech, images or video.

## Offline use and hosting

The service worker precaches the small search UI, catalogue and vectors. The heavy runtime, model and WASM are excluded from automatic installation. Requested model assets are cached lazily in a separate engine-version cache, reused across writing-only updates and removed when the engine version changes. Results never fetch audio on arrival. Browser storage is best effort: meaning search works offline after a successful cached use; cleared or evicted storage requires another download.

For a future engine upgrade, use new model/runtime filenames or versioned directories before changing weights/runtime bytes. Update worker paths and provenance together so an older controlling worker or HTTP cache cannot supply an earlier engine under an unchanged URL. Regenerate vectors and repeat actual inference/offline checks. The build enforces a conservative 1,000,000,000-byte Pages output budget; audiobooks remain in Releases.

## Verification

`scripts/verify_search.py` uses the actual model in Chromium. It exercises `docs/search-questions.json`, word-only search, deduplication, heading/listening/practice destinations, failed downloads, cancellation, no query transmission/storage, all-local requests, responsive light/dark layouts and no-JavaScript browsing. The offline journey checks that a fresh install does not cache the model, performs a requested semantic search, reloads offline and runs a different query through fresh inference.

The question set is a small regression benchmark, not proof that every situation retrieves the right reading. Check weak and unrelated results; never present similarity as a diagnosis or confidence percentage. Automated checks do not establish scientific accuracy, clinical suitability or learning outcomes. Desktop emulation is not a physical-device performance test.

On 8 November 2026 all fifteen selected questions returned an expected reading among their first three results. The Dad/refusing-help question returned Declining help first. The existing reading-design, navigation, narration and offline-installation checks were also run alongside the new search checks. These are measured regression results for the selected cases, not a general accuracy rating.

After the matriarch report, the set was expanded to 22 questions including role labels and other short terms. All seven added headwords remain in the report. Matriarch, patriarch, peacemaker, scapegoat, introvert and procrastination found expected reading among the first three. Micromanaging remains a known weak retrieval, so the measured result is 21/22 rather than a claim of complete vocabulary coverage. The four vocabulary bridges are editorial navigation aids and are tested in word-only search as well as actual browser inference.

## Reference expansion on 8 November 2026

The expanded corpus has 161 reading pages and 1,956 passages. New references are text-first and their search cards do not offer nonexistent recordings. Reviewed concept aliases (for example mental load and invisible work) identify actual developed explanations. Ordinary-language phrases can contribute a bounded ranking boost; role bridges remain explicitly related reading, and unknown terms receive no invented definition. The library word filter includes the same reviewed aliases. The final local actual-model benchmark found expected reading in the first three for all 45 selected queries, alongside the offline, fallback and privacy checks. This is a regression result for those questions, not proof of general accuracy.

## Reading guide addition — 10 November 2026

The corpus now includes `reading/books.html`: 162 reading pages and 2,074 passages. Book and textbook queries can surface the reading guide; its directory weighting preserves the priority of concept explanations for ordinary behaviour questions. The browser benchmark now includes five book-selection/title queries and passed all 53 expected-reading-in-top-three checks. These are regression cases, not a general accuracy claim. The new guide is text-only and its result offers no nonexistent audio.

Known book-title and author aliases are derived from the guide’s verified headings and author credits. Exact title requests can retrieve the guide without the word “book”, including punctuation variants. Ambiguous one-word titles such as Personality, Influence and Behave are not standalone exact aliases. The Nettle title/author regression also checks the destination section anchor.
