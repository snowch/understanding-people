# Concept-first chapter revision

Completed 3 November 2026. Chapters 2–12 now explain concepts before brief, clearly labelled fictional examples. Chapter 1 remains the earlier benchmark. Long running stories have been removed from the main explanations; deeper references carry the detail.

Each revised chapter retains one recall cue, definitions linked to the glossary, nearby research and its limits, three key takeaways, one compact recall/application/week exercise, optional deeper practice and the existing saved-note identifier. Six earlier-chapter recalls remain optional. The manipulation example was made self-contained and updated identically in the glossary.

## Scope and continuity

The revision preserves 190 earlier section/definition anchors and all existing chapter note IDs. `chapter-revision-anchors.json` records these published anchors; raw Markdown’s automatic chapter-title IDs are excluded because the existing builder did not publish them. Source-defined links that no longer have their own section remain as compatibility anchors near optional practice.

The eleven earlier chapter videos follow the previous stories. The overview also invites readers to watch each chapter. Their players are paused on the revised reading pages; existing assets remain in Git and direct media URLs remain available for compatibility, except Chapter 1 assets which stay excluded from Pages as before. Existing confirmation-bias reference audio remains. No replacement chapter recordings or images were created.

## Concision

Counts include Markdown, definitions, optional practice and compatibility anchors; they are not estimates of speaking time.

| Chapter | Before | Revised |
| --- | --- | --- |
| [02](../chapters/02-what-counts-as-knowing.md) | 1639 | 983 |
| [03](../chapters/03-needs-motives-goals.md) | 2296 | 1303 |
| [04](../chapters/04-beliefs-identity-history.md) | 1543 | 1030 |
| [05](../chapters/05-emotion-stress-coping.md) | 1686 | 1021 |
| [06](../chapters/06-personality-habits-situations.md) | 1693 | 996 |
| [07](../chapters/07-culture-groups-power.md) | 1760 | 1075 |
| [08](../chapters/08-questions-listening-disagreement.md) | 1711 | 1003 |
| [09](../chapters/09-truth-lies-uncertainty.md) | 1442 | 970 |
| [10](../chapters/10-motivation-influence-cooperation.md) | 1586 | 963 |
| [11](../chapters/11-conflict-manipulation-boundaries.md) | 1835 | 1219 |
| [12](../chapters/12-putting-understanding-to-work.md) | 1710 | 1084 |

Total: 18,901 → 11,647 words, 38.4% shorter.

## Verification

`python scripts/build.py` checks the complete site’s links and fragments. `scripts/verify_chapter_revision.py BASE_URL` checks every revised chapter, earlier anchors, glossary consistency, restored/edited notes and responsive widths without screenshots. `PEOPLE_NO_SCREENSHOTS=1 python scripts/verify_practice.py BASE_URL` checks all twelve chapters’ practice, keyboard controls, notes, downloads, deletion, storage failures, no-JavaScript/offline access and print styles. These checks concern publication and interaction, not scientific validation or proof of retention.
