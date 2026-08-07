# McLoughlin.world — Live Website Architecture Overview

This document records the current public architecture of **McLoughlin.world** so the open-source repository stays aligned with the live knowledge infrastructure.

**Public site:** https://www.mcloughlin.world/

**Repository:** `EduLinked-coder/McLoughlin.World`

## Public knowledge infrastructure

McLoughlin.world publishes permanent, citable knowledge for inclusion, capability and intelligent organisations alongside machine-readable representations designed for direct use by software and AI systems.

The current public homepage reports:

- **93 published concepts**;
- **17 glossaries and concept schemes**;
- **6 open data formats**;
- **CC BY 4.0** as the knowledge licence.

These counts describe the live website and should be treated as time-sensitive publication metadata rather than hard-coded invariants.

## Primary public layers

The public information architecture currently exposes these primary layers:

1. **Publications** — long-form and release-oriented public knowledge.
2. **Glossaries** — controlled vocabularies and concept schemes.
3. **Concepts** — permanent concept-level pages.
4. **Datasets** — linked data, ontologies, semantic mappings, taxonomies, validation artefacts and other machine-readable resources.
5. **About** — context for McLoughlin.world and its public infrastructure purpose.
6. **Contact** — public contact pathway.
7. **Releases** — explicit version and release surface.

## Publication rule

The live site states a clear publication rule:

> Everything important should exist as a permanent, citable webpage. Every webpage should also have a machine-readable representation.

Repository artefacts should preserve that rule wherever practical.

## Human-readable and machine-readable publication

The public model is deliberately dual-surface:

### Human-readable

Glossaries, concepts, documentation and research should exist as full webpages at stable URLs.

### Machine-readable

The same underlying knowledge should be available through interoperable semantic or structured formats such as:

- JSON-LD;
- RDF;
- Turtle;
- JSON;
- CSV;
- validation or schema artefacts where applicable.

## Versioning

Definitions, identifiers, provenance and changes should be published through explicit releases rather than silently overwritten.

## Featured ontology publication

The live homepage currently features **SSA Ontology v0.1.0**, described as a versioned semantic dataset for inclusion that publishes lived-experience-derived concepts as permanent webpages and interoperable semantic data.

The repository should therefore treat the SSA Ontology and SSA Lexicon as public knowledge infrastructure rather than as isolated glossary documents.

## Repository alignment rule

When the website and repository differ:

1. verify the current public website;
2. preserve canonical public URLs;
3. update repository documentation and machine-readable artefacts to match verified public state;
4. do not invent unpublished website content;
5. preserve provenance and release history;
6. keep legal or jurisdiction-sensitive claims explicitly time-bound.

## Source of truth note

The live website is the source of truth for what is currently published publicly. The repository is the open-source development, documentation and interoperability surface and should be maintained closely enough that contributors can understand the current public system without reverse-engineering the website.