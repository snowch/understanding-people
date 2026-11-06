# Course presentation

## Direction and design skill

This presentation follows Anthropic's [frontend-design skill](https://github.com/anthropics/skills/tree/main/skills/frontend-design), read on 6 November 2026, especially its two-pass plan/critique process, deliberate typography, useful rather than decorative structure, and restraint. Its guidance applies to design; publication stays in this existing GitHub Pages repository, directly on main as authorized.

The reader's main task is to understand a concept and use it. The screenshot showed the lesson text pushed below a large block of audio controls, repeated course labels and oversized navigation. The visual direction is a considered field guide: readable, distinctive type and calm navigation, with a compact, accessible listening instrument beside the text.

## Plan before implementation

| Token | Value | Purpose |
| --- | --- | --- |
| Paper | `#f7f6f0` | Established warm reading surface |
| Ink | `#233a32` | Main reading text |
| Forest | `#2a604c` | Actions, links and current location |
| Sage | `#e8eee5` | Practice and quiet selected states |
| Rule | `#d7ded3` | Grouping and separators |
| Muted | `#56665c` | Secondary text with useful contrast |

Newsreader supplies the reading and display typography; Public Sans supplies controls and navigation. Both are self-hosted with their OFL licenses, including Latin and Latin-extended subsets. There are no runtime font/CDN requests. Reading is left-aligned, normally below 70 characters per line, with deliberate serif leading and generous paragraph breaks.

```text
Brand                                  Contents   Settings   Star   Install
──────────────────────────────────────────────────────────────────────────
Explore the guide       Library / Topic
  The book              Lesson title
  Reference library     [ Play ] ─────────── 0:00 / 4:15
    current topic       Voice: Jenny    Speed: 1×    Transcript   Download
    current entry       ▸ Sections
  Practice
  About & sources       The concept and its useful distinctions…
                        Example / evidence / practice
```

On small screens, navigation becomes its existing disclosure and the player controls wrap in a deliberate reading order. Dark mode uses the same hierarchy with appropriate contrast; print and no-JavaScript behavior remain functional. Motion only responds to a user action, and respects reduced motion.

## Critique of the plan

A cream-and-serif palette alone is a common template. Here it is retained because it is the book's established identity and the user's earlier preference. The distinctive work must instead come from the typography, reading rhythm and a useful, compact player. Remove the repeated course/draft eyebrow from reference pages, avoid decorative uppercase labels, reduce redundant sidebar branding and give the actual explanation the first-screen space it needs. Spend the visual emphasis on the play control and the lesson title, rather than treating every secondary control as an outlined card.

## Boundaries

This is presentation work. Preserve canonical teaching, reference sources, existing anchors and note IDs, all Andrew/Jenny recordings and their manifests. Retain native audio as the no-JavaScript fallback, synthetic-voice disclosure, download/transcript links, exact voice-specific seeking, saved preferences and deliberate playback. Audio must never load merely because a page or a saved voice preference is displayed.

Validate the screenshot's reference page, foundations, library, settings and practice pages on phone, tablet and desktop, in both color schemes. Inspect actual screenshots and verify keyboard playback/seeking, storage/error behavior, no-JavaScript controls, print, offline reading and project-path links. Generated previews stay outside Git. Technical checks do not establish teaching outcomes or a human listening judgment.

## First implementation review

The screenshots were reviewed on phone, tablet and desktop, with matching dark views. The typography and compact player make the explanation visibly more prominent. The second pass removed extra padding around the on-page menu and the decorative outgoing arrow on the internal book link. It also strengthened the unplayed slider track, retained 44-pixel play/mute targets, and made a playback error expose the transcript/download recovery paths.

The screenshot's reference entry, `reference/deception.html`, was measured before publication against the preceding live edition with Jenny selected. CSS pixels, closed controls, identical viewport widths:

| Width | Earlier player | New player | Earlier explanation starts | New explanation starts |
| ---: | ---: | ---: | ---: | ---: |
| 390 | 492 | 201 | 1,010 | 598 |
| 834 | 405 | 161 | 893 | 520 |
| 1024 | 405 | 161 | 902 | 526 |
| 1440 | 405 | 161 | 934 | 499 |

The new design check covers eight page types at five widths, in light and dark, including loaded local fonts, contrast, navigation breakpoints, no horizontal overflow, no external requests and no unsolicited audio. It also exercises keyboard play/pause and cold seeking, mute, voice-specific slider duration, advanced resources, visible playback recovery, no-JavaScript native controls and print. Existing voice, narration, notes, navigation and installation checks remain separate regression gates. No narration, spoken scripts, source research or saved-note identifiers are changed by the design work.

## Completed verification

The static build passed all links and anchors across 140 pages. The new design check passed all eight representative page types at five widths in both color schemes. The existing voice-settings journey, both 136-page Andrew/Jenny narration checks, chapter-revision, practice/notes, reference-library, navigation, optional confirmation-audio and installation/offline checks passed. Twelve existing parser, speech-gap and cache/interruption unit checks also passed.

Both narration manifests, all 272 MP3s and all 272 transcripts were checked against their recorded hashes and preserved; canonical teaching, research and authored speech files have no changes. No TTS service was called. Normal course builds include the font files and their licenses and require no external font service. Public deployment and the final live browser checks follow publication to main.
