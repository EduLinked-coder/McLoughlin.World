# Glossary of Human Trafficking — Overview

Canonical public URL:

https://www.mcloughlin.world/glossaries/ssa-lexicon/glossary-of-human-trafficking/

## Purpose

The Glossary of Human Trafficking provides a controlled human-readable and machine-readable vocabulary for recognising, describing, exchanging, and reasoning about observable indicators associated with human trafficking, exploitation, coercion, and safeguarding.

The glossary is designed for people, AI systems, case-management platforms, safeguarding systems, labour-compliance systems, researchers, and data pipelines that need a shared vocabulary without collapsing observations into automated victim or offender determinations.

## Canonical reasoning model

`Observation -> Evidence -> Indicator -> Pattern -> Risk Assessment -> Safeguarding Action -> Authorised Human Decision`

The glossary intentionally separates observable facts from consequential conclusions.

## Core object family

- `HT-INDICATOR`
- `HT-OBSERVATION`
- `HT-EVIDENCE`
- `HT-PATTERN`
- `HT-TEMPORAL-PATTERN`
- `HT-RISK-ASSESSMENT`
- `HT-SAFEGUARDING-ACTION`
- `HT-SOURCE-AUTHORITY`
- `HT-JURISDICTION-RULE`
- `HT-MODEL-DETECTION-MAPPING`
- `HT-MACHINE-POLICY`

## Core indicator domains

The glossary covers observable concepts including:

- abuse of vulnerability;
- deception;
- restriction of movement;
- isolation;
- physical or sexual violence;
- intimidation and threats;
- retention of identity documents;
- withholding of wages;
- debt bondage;
- abusive working or living conditions;
- excessive overtime;
- coercive recruitment and dependency patterns.

## Evidence model

Machine reasoning should preserve:

- supporting evidence;
- corroborating evidence;
- counterevidence;
- alternative explanations;
- source reliability;
- temporal context;
- uncertainty and confidence;
- provenance.

Individual indicators are not independently conclusive.

## Machine decision boundary

AI and automated systems may:

- recognise candidate indicators;
- correlate observations;
- identify possible patterns;
- surface missing evidence and counterevidence;
- preserve uncertainty;
- recommend safeguarding review;
- explain why a concern was surfaced.

AI and automated systems must not:

- automatically declare a person a trafficking victim;
- automatically declare another person a trafficker;
- automatically initiate punitive or enforcement action;
- expose identities unnecessarily;
- infer trafficking from demographic characteristics;
- treat a single keyword or indicator as proof.

## Cross-glossary interoperability

The Human Trafficking glossary is designed to interoperate with related SSA Lexicon vocabularies, including the Glossary of Coercive Control. Related concepts may be linked where the same observable conduct is relevant in different contexts, while preserving distinct meanings and legal frameworks.

Examples include:

- `HTI-RESTRICTION-OF-MOVEMENT` related to `CCI-MOVEMENT-RESTRICTION`;
- `HTI-DOCUMENT-RETENTION` related to `CCI-DOCUMENT-PASSPORT`;
- `HTI-THREATS` related to `CCI-PSYCHOLOGICAL-INTIMIDATION`.

A cross-glossary relationship means related concept, not equivalence.

## Governance principle

People describe experiences. Machines identify candidate concepts. Evidence establishes context. Patterns support assessment. Jurisdiction rules determine legal relevance. Authorised humans make consequential decisions.
