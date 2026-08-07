# McLoughlin.world — Publication Model

McLoughlin.world is designed as **public knowledge infrastructure** rather than a conventional content website.

## Core rule

The current live-site publication rule is:

> Everything important should exist as a permanent, citable webpage. Every webpage should also have a machine-readable representation.

This repository should support that rule by maintaining source documentation, semantic artefacts, schemas, provenance and release metadata alongside the public pages.

## Permanent human-readable surfaces

Human-facing publication should prioritise:

- stable canonical URLs;
- complete webpages rather than download-only archives;
- clear titles and descriptions;
- provenance and version information;
- cross-links between glossaries, concepts, datasets and releases.

## Machine-readable surfaces

Machine-facing publication should use standards-based representations appropriate to the underlying resource, including:

- JSON-LD;
- RDF;
- Turtle;
- JSON;
- CSV;
- JSON Schema and validation artefacts where relevant.

## Traceable releases

Definitions, identifiers, provenance and changes should be represented through explicit releases rather than silently overwritten.

At minimum, important semantic releases should identify:

- resource name;
- canonical URL;
- semantic version;
- representation files;
- source/provenance information;
- schema or validation version where applicable;
- integrity hashes where applicable;
- change history.

## Stable identifiers

Once a semantic identifier has been publicly adopted, updates should normally revise its definition or metadata through versioning rather than rename the identifier casually.

Breaking identifier changes require explicit migration documentation.

## Cross-layer architecture

The public knowledge graph should be understood as:

`Publication -> Glossary / Concept Scheme -> Concept -> Dataset Representation -> Release`

A resource may participate in more than one layer, but each representation should preserve a single canonical identity.

## Open-source and knowledge licensing

The live homepage currently identifies **CC BY 4.0** as the knowledge licence. Repository-level software and other artefacts may require separate explicit licensing terms, and those terms should not be inferred solely from the website's knowledge-licence statement.

## Consequential machine use

For safeguarding, legal, accessibility, institutional or other high-impact domains, machine-readable publication must preserve the distinction between:

- semantic recognition;
- evidence;
- interpretation;
- risk assessment;
- jurisdiction-specific rules;
- authorised human decision.

Publishing a vocabulary does not authorise automated consequential action.