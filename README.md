# McLoughlin.World

McLoughlin.World is an **open-source public knowledge infrastructure** and publishing workspace for controlled vocabularies, semantic artefacts, datasets, concepts, research, workflows, and documentation created by **Sarah Ailish McLoughlin** and associated with McLoughlin.world and the broader **EduLinked-Systems** ecosystem.

The repository is intended to make important human-readable knowledge and machine-operable public-interest infrastructure openly inspectable, reusable, interoperable, and improvable while preserving clear provenance, attribution, versioning, governance boundaries, and human accountability.

**Live website:** https://www.mcloughlin.world/

## Current public website state

The live McLoughlin.world homepage currently reports:

- **93 published concepts**;
- **17 glossaries and concept schemes**;
- **6 open data formats**;
- **CC BY 4.0** knowledge licensing.

These figures are time-sensitive publication metadata and may change as the public knowledge base grows.

The live site is organised around the following public infrastructure layers:

- **Publications**;
- **Glossaries**;
- **Concepts**;
- **Datasets**;
- **Releases**;
- **About**;
- **Contact**.

Repository documentation for the current public architecture is maintained under:

- [docs/website/OVERVIEW.md](docs/website/OVERVIEW.md)
- [docs/website/GLOSSARIES.md](docs/website/GLOSSARIES.md)
- [docs/website/DATASETS.md](docs/website/DATASETS.md)
- [docs/website/PUBLICATION-MODEL.md](docs/website/PUBLICATION-MODEL.md)

## Publication rule

McLoughlin.world follows a dual-publication model:

> **Everything important should exist as a permanent, citable webpage. Every webpage should also have a machine-readable representation.**

Human-readable pages are paired, where appropriate, with standards-based semantic and structured representations such as JSON-LD, RDF, Turtle, JSON, CSV and validation artefacts.

Definitions, identifiers, provenance and changes should be published through explicit releases rather than silently overwritten.

## SSA Ontology and SSA Lexicon

The live site currently features **SSA Ontology v0.1.0**, a versioned semantic dataset for inclusion that publishes lived-experience-derived concepts as permanent webpages and interoperable semantic data.

McLoughlin.world publishes human-readable and machine-readable controlled vocabularies through the **SSA Lexicon**. These glossaries are designed so people, AI systems, software, researchers, safeguarding systems, and data pipelines can refer to the same concepts using stable identifiers, explicit provenance, versioned definitions, and clear decision boundaries.

The public homepage currently features SSA Lexicon glossaries covering:

- Accessibility Abuse;
- Coercive Collaboration;
- Digital Sovereignty;
- Institutional Mimicry;
- Structural Disappearance.

The broader public Glossaries layer also exposes the SSA Lexicon / Ontology, Taxonomy for Recognising Extraction, Glossary of Autistic Communication, Splaining Glossary and Lived Experience Glossary.

See [docs/website/GLOSSARIES.md](docs/website/GLOSSARIES.md) for the current public glossary architecture and canonical links.

## Safeguarding vocabularies

The architecture separates observable information from consequential conclusions. Machine-readable safeguarding vocabularies should support recognition, evidence handling, counterevidence, pattern analysis, uncertainty, provenance, and referral while preserving human review for consequential decisions.

### Glossary of Human Trafficking

Canonical public URL:

https://www.mcloughlin.world/glossaries/ssa-lexicon/glossary-of-human-trafficking/

Repository overview:

[glossaries/glossary-of-human-trafficking/OVERVIEW.md](glossaries/glossary-of-human-trafficking/OVERVIEW.md)

The glossary defines machine-readable concepts for observable trafficking and exploitation indicators, observations, evidence, counterevidence, patterns, risk assessment, safeguarding actions, source authorities, jurisdiction rules, and machine-policy boundaries.

Its canonical reasoning model is:

`Observation -> Evidence -> Indicator -> Pattern -> Risk Assessment -> Safeguarding Action -> Authorised Human Decision`

Automated systems may recognise and correlate indicators, but the vocabulary does not authorise automated victim determination, trafficker determination, punitive action, or unnecessary identity disclosure.

### Glossary of Coercive Control

Canonical public URL:

https://www.mcloughlin.world/glossaries/ssa-lexicon/glossary-of-coercive-control/

Repository overview:

[glossaries/glossary-of-coercive-control/OVERVIEW.md](glossaries/glossary-of-coercive-control/OVERVIEW.md)

**Version:** `1.0.0`  
**Primary namespace:** `CCI-*`  
**Pattern namespace:** `CCP-*`

The glossary provides a controlled human-readable and machine-readable vocabulary for recognising, describing, and reasoning about observable behaviours, effects, and patterns associated with coercive control.

Its canonical reasoning model is:

`Observation -> Evidence -> Indicator -> Pattern -> Risk Assessment -> Safeguarding Action -> Authorised Human Decision`

The model is intentionally pattern-sensitive. Individual behaviours are not independently conclusive. Systems using the vocabulary should consider context, repetition, fear, autonomy, dependency, consequences for resistance, escalation, counterevidence, alternative explanations, and jurisdiction-specific legal requirements.

The coercive-control package is designed to support multiple representations, including:

- human-readable HTML;
- JSON;
- JSON-LD;
- CSV;
- Turtle / RDF;
- RDF/XML;
- JSON Schema validation;
- machine-readable examples;
- source and provenance registries;
- distribution and integrity manifests.

Legal status is represented separately from semantic recognition. A match against a `CCI-*` indicator does not establish that any Australian criminal, civil, family-law, or other jurisdiction-specific legal test has been satisfied.

## Machine-governance principle

> **People describe experiences. Machines identify candidate concepts. Evidence establishes context. Patterns support assessment. Jurisdiction rules determine legal relevance. Authorised humans make consequential decisions.**

## Repository governance

This repository is open source and supports public inspection, collaboration, interoperability, and reuse subject to the repository's applicable licence terms.

The **live website is the source of truth for what is currently published publicly**. This repository is the open-source development, documentation, semantic interoperability and release-support surface. Where the two drift, the repository should be reconciled against verified public state without inventing unpublished content.

Open publication does not remove the safeguards attached to the vocabularies themselves. Publication of a controlled vocabulary does not convert a machine-generated assessment into a legal, clinical, safeguarding, or enforcement determination.

Machine-readable artefacts should preserve, where applicable:

- stable canonical identifiers;
- semantic versioning;
- source authority and provenance;
- evidence and counterevidence;
- confidence and uncertainty;
- jurisdiction and commencement status;
- explicit prohibited automated actions;
- human review requirements for consequential action.

## Open-source status and attribution

McLoughlin.World is published as an **open-source project**.

Original authorship and provenance remain attributed to **Sarah Ailish McLoughlin**. Open-source availability is intended to enable transparent inspection, responsible reuse, contribution, adaptation, and interoperability while maintaining source attribution and the governance and safeguarding boundaries documented in this repository.

The live website currently identifies **CC BY 4.0** as its knowledge licence. Repository-level software, code, third-party materials and other artefacts may require separate explicit licence terms; those terms should not be inferred solely from the website knowledge-licence statement.

© 2025-2026 Sarah Ailish McLoughlin.