# McLoughlin.world — Datasets Layer

**Public index:** https://www.mcloughlin.world/datasets/

The Datasets layer provides structured resources supporting McLoughlin.world's public knowledge infrastructure.

The live site describes this layer as including linked data, ontologies, semantic mappings, taxonomies, validation artefacts and other machine-readable resources. Datasets are intended to be versioned, openly described and suitable for long-term interoperability and reuse.

## Current public dataset entry points

The live Datasets index exposes:

- **SSA Ontology downloads**;
- **SSA Ontology releases**;
- **Releases**;
- **Ontology**.

These routes form the public discovery surface for machine-readable knowledge and release history.

## Distribution model

McLoughlin.world's current publication model uses multiple interoperable formats. The homepage reports **6 open data formats** and describes machine-readable publication through JSON-LD, RDF, Turtle, JSON and CSV, with other validation artefacts used where appropriate.

For controlled vocabularies and semantic datasets, repository artefacts should aim to provide:

- canonical structured JSON;
- JSON-LD;
- CSV exports;
- Turtle / RDF;
- RDF/XML where required for compatibility;
- JSON Schema or other validation contracts where meaningful;
- source/provenance registries;
- manifests and checksums for release integrity.

## SSA Ontology

The live homepage currently identifies **SSA Ontology v0.1.0** as the featured semantic dataset.

It is described as a versioned semantic dataset for inclusion, publishing lived-experience-derived concepts as permanent webpages and interoperable semantic data.

Repository documentation should keep ontology versioning, glossary versioning and individual concept identifiers distinguishable.

## Versioning rule

Machine-readable resources should not be silently overwritten where doing so would obscure semantic change.

A release should preserve, where applicable:

- semantic version;
- canonical identifier;
- release date;
- provenance;
- schema version;
- change record;
- checksums;
- representation manifest.

## Safeguarding vocabularies

The Human Trafficking and Coercive Control glossary work extends this same dataset architecture into safeguarding-oriented controlled vocabularies.

Their machine-readable representations must preserve decision boundaries so semantic recognition cannot be mistaken for an automated legal, victim, offender or enforcement determination.