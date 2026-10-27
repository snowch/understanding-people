# Understanding people

A science-informed guide to understanding what drives people—including ourselves.

[Read the book](https://snowch.github.io/understanding-people/) · [Contents](contents.md) · [Evidence standards](evidence.md)

This is a complete first editorial draft: an introduction, twelve developed chapters, reading routes, a practical worksheet, an annotated source list, and reading, author and support pages. All chapters include key takeaways and practical exercises. It has not undergone external subject-matter review.

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

With a local server running, `python3 scripts/verify_install.py http://localhost:8000/` checks installation event handling, fallback instructions, responsive layout, app metadata and offline reading. The browser test simulates the native install events; it does not perform an operating-system installation.

`.github/workflows/pages.yml` validates pull requests and publishes pushes to `main` through GitHub Actions. GitHub Pages must use **GitHub Actions** as its source.

## Writing

Edit the Markdown files. Register new pages in `PAGES` in `scripts/build.py`, set their source path in `CHAPTERS`, and update `contents.md`. Keep the chapter anchors in the contents so existing links continue to resolve. Cite research beside the claim it supports and add an annotated entry in `references.md`. Distinguish research findings, interpretations and practical suggestions. All scenarios are fictional teaching examples, not evidence.

Practical reader actions use a sage-green `section.reader-action` panel with a labelled heading and checklist icon. Use `markdown="1"` on the section and give its heading an explicit ID referenced by `aria-labelledby`. Keep research explanations outside the panels, and make each action concrete. The styling includes mobile, dark-mode and print variants. General caveats belong in `how-to-use.md`; retain claim-specific qualifications beside the relevant finding.

End each chapter with a “Key takeaways” section containing 3–5 short bullets, followed by its final practice panel. Recap only ideas already explained, preserve evidence qualifications, and include one point about the reader’s own perspective. Use `section.key-takeaways` with `markdown="1"` and an `aria-labelledby="key-takeaways"` heading ID; its plain heading and thin divider distinguish the recap from an action. Supporting pages do not need chapter recaps.

Chapter 1 models a focused teaching sequence: a central distinction, a worked example, a short attempt before revealing an answer, and a closing recall-and-application exercise. Optional answers use `details.answer-check`; supporting research detail uses `details.evidence-detail`. Both use native keyboard-accessible summaries and show their contents in print. Keep citations beside the claims they support, including inside optional evidence notes.

Use direct, everyday English. Prefer concrete questions such as “What did they say?” and “Why do you think they said it?” over abstract shorthand such as “What have you added?” or “Act on the impact”. Explain the idea through an example before naming a technical term. Apply the same standard to headings, exercises and research notes; a short sentence is only helpful if its meaning is clear.
