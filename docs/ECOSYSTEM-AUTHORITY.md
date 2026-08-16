# McLoughlin.world ecosystem authority map

This document records the repository boundaries found during the 17 August 2026 ecosystem search. Its purpose is to prevent adjacent research, archive, product and historical repositories from becoming accidental competing sources of truth for the public McLoughlin.world knowledge infrastructure.

## Canonical public publication repository

### `EduLinked-coder/McLoughlin.World`

Role: open-source development, documentation, semantic interoperability and release-support repository for McLoughlin.world.

Canonical-publication rule: the live website remains the source of truth for what is currently published publicly. This repository should mirror and support that public state while preserving provenance, releases and compatibility history.

Canonical ontology/lexicon root:

`https://www.mcloughlin.world/glossaries/ssa-lexicon/`

## Adjacent repositories reviewed

### `EduLinked-coder/SSA-Website`

Observed state: private, very small historical workspace. Its README still contains 2025 all-rights-reserved and development-workspace language.

Authority classification: `legacy_noncanonical`.

Rule: do not import its IP/licensing or production-authority statements into current McLoughlin.world publication metadata without explicit review. It is evidence of historical development context, not current public publication authority.

### `EduLinked-coder/SSA_Resistance_Archive-`

Observed state: private archive-named repository with minimal content footprint.

Authority classification: `archive_noncanonical`.

Rule: material may be useful as provenance/history but must not silently override current term definitions, canonical URLs, release status or licensing.

### `EduLinked-coder/wiki`

Observed state: private general workspace.

Authority classification: `supporting_noncanonical` unless a specific artefact is separately designated authoritative.

### `EduLinked-coder/charter`

Observed state: private governance-oriented repository.

Authority classification: `governance_reference`.

Rule: governance content may inform McLoughlin.world processes, but ontology term definitions and public release identity remain controlled by the public publication surface and explicit release records.

### `EduLinked-coder/Advocacy-AI`

Observed state: private application/research repository.

Authority classification: `downstream_or_adjacent_system`.

Rule: AI implementations may consume published concepts but must not become the canonical source for glossary definitions or public ontology releases.

### `EduLinked-coder/SYSTEMS-CODEX`

Observed state: private systems/governance repository.

Authority classification: `operational_reference`.

Rule: operational conventions may be reused when compatible, but public knowledge identity must remain independently citable from McLoughlin.world.

### `EduLinked-coder/metadata-sovereignty`

Observed state: private candidate product-authority boundary for EduLinked Metadata Sovereignty. Its README explicitly states that the public research repository is independently usable and that private/public boundaries must remain isolated except through human-reviewed sanitised packages.

Authority classification: `private_product_boundary`.

Rule: do not copy private implementation details, product strategy or protected topology into McLoughlin.world. Publicly appropriate concepts may only cross through an intentional, reviewed publication decision.

### `EduLinked-Systems/metadata-sovereignty-ai-research`

Observed state: public research repository focused on authorship, consent, provenance, accessible communication and AI-processing governance. It contains a versioned machine-operable research contract and deterministic validator.

Authority classification: `public_research_reference`.

Useful reusable principles include:

- authorship and provenance should be explicit;
- consent and AI-processing permissions should be represented structurally;
- missing permission should be treated as no permission in governed workflows;
- automated validation checks completeness and internal consistency but does not replace evidence appraisal, consent verification, accessibility audit or human publication approval.

Rule: reference or adapt these principles where appropriate; do not duplicate that research corpus into McLoughlin.World or create an automatic public/private dependency.

## Authority precedence

For McLoughlin.world knowledge publication, use this order when sources conflict:

1. current live canonical public page;
2. explicit current release record and verified published artefact;
3. current McLoughlin.World repository representation;
4. verified site export snapshot;
5. governance/reference repositories for their defined domain only;
6. research repositories;
7. archives and legacy workspaces.

A lower-level source may provide evidence that triggers review, but it does not silently override a higher-level source.

## Cross-repository publication rule

Content from an adjacent repository may enter McLoughlin.World only when all of the following are true:

- the source and authorship are identified;
- publication authority is clear;
- licensing/consent permits publication;
- the resource does not expose private topology, credentials, personal data or protected product strategy;
- canonical identifiers are assigned or preserved;
- provenance is retained;
- existing McLoughlin.world concepts are checked before creating duplicates;
- consequential safeguarding or legal claims retain their human-review boundaries.

## No-new-repository conclusion

The ecosystem review does not establish a gap requiring a new repository for the SSA Ontology or McLoughlin.world public knowledge infrastructure. `EduLinked-coder/McLoughlin.World` can absorb the missing public release, concept registry, documentation and interoperability artefacts. Creating another ontology repository would increase source-of-truth ambiguity without an evidenced capability benefit.
