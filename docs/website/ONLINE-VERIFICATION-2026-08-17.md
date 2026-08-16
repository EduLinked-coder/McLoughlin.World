# Live-site verification — 17 August 2026

This record captures online verification performed against the public McLoughlin.world website on 17 August 2026. It supplements the site export and should be treated as a point-in-time verification record, not a permanent substitute for the live site.

## Verified public homepage state

The public homepage currently identifies McLoughlin.world as public knowledge infrastructure and reports:

- 93 published concepts;
- 17 glossaries and concept schemes;
- 6 open data formats;
- CC BY 4.0 knowledge licence.

It describes a dual-publication rule: important resources should exist as permanent, citable webpages and also have machine-readable representations. The homepage identifies SSA Ontology v0.1.0 as the featured versioned semantic dataset.

Public source: https://www.mcloughlin.world/

## Verified Datasets layer

The Datasets page states that the infrastructure includes linked data, ontologies, semantic mappings, taxonomies, validation artefacts and other machine-readable resources. It exposes dedicated links for:

- SSA Ontology downloads;
- SSA Ontology releases;
- general Releases;
- Ontology.

Public source: https://www.mcloughlin.world/datasets/

## Generic Releases page discrepancy

The generic `/releases/` page currently renders a heading followed by placeholder text (`Enter your content here`). This must not be interpreted as evidence that SSA Ontology v0.1.0 is unpublished: the homepage and Datasets layer separately advertise the SSA release and its dedicated release/download surfaces.

Repository documentation must therefore distinguish:

1. the generic site-wide Releases page;
2. the dedicated SSA Ontology releases surface;
3. the actual v0.1.0 release record and published serialisations.

Public source: https://www.mcloughlin.world/releases/

## Canonical-root rule

The current public ontology/lexicon identity is rooted at:

`https://www.mcloughlin.world/glossaries/ssa-lexicon/`

The older `/ssa/` route is a compatibility/legacy repository surface and must not be represented as the canonical ontology root.

## Repository validation state

The repository now includes a deterministic publication-state validator and GitHub Actions workflow.

The first workflow run completed successfully on `main`:

- workflow: `Validate publication state`;
- run: `31974197400`;
- commit: `dde356fe1e708b791ef19db2698fe28254af4333`;
- conclusion: `success`.

The validator checks repository-side canonical identity, release metadata, concept and scheme counts, knowledge licence, required release artefact declarations, 93 unique concept slugs, the `/ssa/` compatibility boundary and the current master JSON-LD metadata.

A later validator revision also validates the machine-readable ecosystem authority map, verification status and SSA v0.1.0 citation metadata.

## Repository licence boundary

GitHub repository metadata currently reports no repository-level licence.

This does not change the verified **CC BY 4.0** licence for published SSA knowledge content. It means repository software, scripts, Jekyll templates, workflows and tooling still require an explicit licensing decision rather than inheriting CC BY 4.0 by assumption.

This decision is tracked in GitHub issue #4.

## Verification policy

When the website, a historical repository file and an export disagree:

1. verify current public state online where possible;
2. use the current live canonical URL as publication authority;
3. retain older routes only as explicitly labelled compatibility or historical surfaces;
4. preserve release/version history rather than silently rewriting historical evidence;
5. do not infer availability of a machine-readable artefact solely from a generic navigation link;
6. distinguish a published artefact from a repository-side reconstruction until hashes or byte identity are verified;
7. distinguish verified knowledge-content licensing from unresolved software/tooling licensing.

## Known next verification targets

The dedicated SSA Ontology download and release URLs should be hash-verified against repository copies when their bytes are directly retrievable. Until then, repository reconstructions must retain `site-export-derived` or equivalent provenance and must not claim byte-for-byte identity with the hosted release files.

The hosted-file comparison is tracked in GitHub issue #3.
