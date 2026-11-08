# Implementing the research coverage audit

8 November 2026. The eighteen development clusters in the [coverage audit](research-gap-audit.md) are implemented through 25 written references and connections from the existing chapters and entries. The library now has 136 references. These are sourced editorial explanations and practice suggestions, not a systematic review or validated assessment.

| Audit area | Written explanation |
| --- | --- |
| G01 Naming and belonging | [Names, respect and belonging](../reference/naming-and-belonging.md), including face and dignity. |
| G02 Assumptions and authority | [Assumptions in questions and decision rights](../reference/assumptions-and-authority.md), including implied meaning. |
| G03 Family membership and roles | [Family membership, roles and loyalties](../reference/family-membership.md), including cultural adaptation and roles after loss. |
| G04 Unequal treatment | [Different standards and unequal treatment](../reference/unequal-treatment.md). |
| G05 Invisible work | [Invisible work and shared responsibility](../reference/invisible-work.md), including coordination, kin-keeping and the limits of intent claims. |
| G06 Interaction cycles | [Pressure, withdrawal and interaction cycles](../reference/interaction-cycles.md). |
| G07 Helpful support | [Support that feels helpful](../reference/responsive-support.md), linked with declining help, listening, competence and autonomy. |
| G08 Workplace oversight | [Oversight, delegation and micromanagement](../reference/oversight-and-delegation.md). |
| G09 Influence | [Escalating requests and everyday influence](../reference/sequential-requests.md), including social-norm claims and variable results. |
| G10 Attachment | [Adult attachment](../reference/adult-attachment.md), using dimensions rather than fixed identities. |
| G11 Self-regulation | [Procrastination and making a start](../reference/procrastination-planning.md), including a cue, action, obstacle and review. |
| G12 Feedback and safety | [Feedback and speaking up](../reference/feedback-and-speaking-up.md). |
| G13 Personality detail | [Personality facets and situation differences](../reference/personality-facets.md). |
| G14 Exclusion and reputation | [Exclusion, gossip and reputation](../reference/exclusion-and-reputation.md), including audience-sensitive presentation. |
| G15 Comparison and envy | [Social comparison and envy](../reference/social-comparison.md). |
| G16 Gatekeeping | [Access, participation and gatekeeping](../reference/gatekeeping.md). |
| G17 Individual investigation | [Compare occasions and test an explanation](../reference/comparing-occasions.md), with an optional comparison template and saved practice notes. |
| G18 AI reflection | [Use AI without reinforcing a first impression](../reference/ai-reflection.md), with an adaptable prompt and source-checking guidance. |

Additional explanations cover [blame reversal and DARVO](../reference/blame-reversal.md), [changing criteria](../reference/changing-standards.md), [intense and inconsistent contact](../reference/intense-and-inconsistent-contact.md), [negotiation and repair](../reference/negotiation-and-mediation.md), [parentification](../reference/parentification.md), [shame and anger](../reference/shame-anger-and-repair.md), and [digital-message ambiguity](../reference/digital-misunderstandings.md). Popular labels are unpacked into conduct and alternatives; they are not certified as diagnostic categories or indicators of guilt.

## Content and reader journeys

The canonical expansion is in reference/entries/audit-expansion.json. Research summaries, access scope and limits are in reference/research-sources.json. The source bank has 102 records; 37 were added for this expansion. Earlier entries retain their IDs, URLs, note identifiers and authored content. New explanations connect back to them, and the build supplies a closed “Go deeper” disclosure in relevant earlier entries and foundations.

Each new reference explains the concept before a brief fictional example, compares alternatives and exceptions, considers the reader's contribution, offers three takeaways and finishes with one compact practice section. The existing local notes provide observation, interpretation, action and review fields. Additional research or a longer template stays optional. Suggested actions are editorial applications, not tested interventions supplied by this book.

The private app snapshots the canonical expansion through tools/sync_research_expansion.py. It adds 25 concepts to the existing map and reading routes, with 107 explained connections. The app has 196 nodes in total, including the existing 60 practice goals and skills. New reading pages lead to the existing saved-example journey; observations, reflection, action and review remain separate. Relevant earlier app entries link to the expansion too. Backup schema and existing record IDs remain unchanged.

The AI preview already required explicit context selection, editing, consent and separate storage of generated suggestions. The update makes the limits of model agreement visible and asks for information that could weaken the leading explanation. It does not claim that a prompt eliminates sycophancy or makes advice scientifically reliable.

## Written and recorded editions

No new audio, video or images are generated. The approved 136-section Andrew and Jenny recorded editions remain unchanged, as do their source scripts, manifests, transcripts and audiobook release assets.

The 25 new references are explicitly text-only. The revised library index and research-source guide do not present their earlier recordings as current. audio/written-editions.json binds each text-first page to its exact current reading fingerprint and, for revised recorded guides, retains the original recording/source fingerprints plus the reviewed current source hashes. The build validates retained media and rejects an unreviewed text change. It never synthesises speech or silently changes the approved manifest to match new writing.

The existing audiobook downloads are labelled as the recorded edition, so they do not imply coverage of the expanded text. Search and library cards offer Listen only when a current recording exists.

## Verification

The normal build checks local paths, anchors, recording integrity and fresh search vectors. Browser checks cover every written route, new practice-note persistence, mobile widths, keyboard disclosures, no-JavaScript reading, actual semantic inference, keyword fallback and offline search. The expanded search benchmark has 45 questions. The final measured run found expected reading among the first three for all 45, including the new headwords and earlier queries about criticism, interruption and understanding before disagreement. Early runs exposed weaker retrieval; reviewed concept aliases and ordinary-language phrases improved it without lowering the similarity threshold. This small benchmark is not a general accuracy rating.

The private app's browser checks cover offline reading and search, new map entries and explained links, saving a reflection and next step, reload, backup round trips and the existing provider/privacy behaviour. Image capture can be disabled with PEOPLE_NO_SCREENSHOTS=1 for text work. Automated checks establish structure and software behaviour; they do not establish scientific accuracy or improved collaboration in real life.
