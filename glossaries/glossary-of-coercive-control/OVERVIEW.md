# Glossary of Coercive Control — Overview

Canonical public URL:

https://www.mcloughlin.world/glossaries/ssa-lexicon/glossary-of-coercive-control/

**Version:** `1.0.0`  
**Primary namespace:** `CCI-*`  
**Pattern namespace:** `CCP-*`

## Purpose

The Glossary of Coercive Control provides a controlled human-readable and machine-readable vocabulary for recognising, describing, exchanging, and reasoning about observable behaviours, effects, and patterns associated with coercive control.

It is designed for people, AI systems, safeguarding platforms, researchers, service providers, and case-management systems that need a shared vocabulary without turning observations directly into legal conclusions or automated labels.

## Canonical reasoning model

`Observation -> Evidence -> Indicator -> Pattern -> Risk Assessment -> Safeguarding Action -> Authorised Human Decision`

Coercive control is treated as pattern-sensitive. Individual behaviours are not independently conclusive.

## Core object family

- `CC-OBSERVATION`
- `CC-EVIDENCE`
- `CC-INDICATOR`
- `CC-PATTERN`
- `CC-TEMPORAL-PATTERN`
- `CC-IMPACT`
- `CC-RISK-ASSESSMENT`
- `CC-SAFEGUARDING-ACTION`
- `CC-JURISDICTION-RULE`
- `CC-SOURCE-AUTHORITY`
- `CC-MACHINE-POLICY`

## Core indicator domains

The glossary covers observable concepts including:

- threats and intimidation;
- surveillance and monitoring;
- isolation;
- economic and financial control;
- restriction of movement and autonomy;
- identity, document, and credential control;
- housing, financial, immigration, care, transport, and communication dependency;
- psychological control;
- technology-facilitated control;
- post-separation control.

## Pattern vocabulary

Canonical patterns include:

- `CCP-AUTONOMY-EROSION` — progressive erosion of autonomy;
- `CCP-ISOLATION-DEPENDENCY` — increasing isolation combined with dependency;
- `CCP-SURVEILLANCE-INTIMIDATION` — monitoring reinforced by threatened or actual consequences;
- `CCP-ECONOMIC-DEPENDENCY` — financial control that creates or maintains reliance;
- `CCP-MOVEMENT-CONTROL` — multiple mechanisms restricting physical autonomy;
- `CCP-DIGITAL-CONTROL` — systematic technology-facilitated monitoring or restriction;
- `CCP-ESCALATING-CONTROL` — increasing frequency, severity, or scope over time;
- `CCP-POST-SEPARATION-CONTROL` — control continuing or changing form after separation;
- `CCP-MULTI-DOMAIN-CONTROL` — control operating across several areas of life;
- `CCP-FEAR-COMPLIANCE` — behaviour changing because of anticipated consequences.

## Context, agency, and counterevidence

Systems should consider:

- whether conduct is isolated or repeated;
- whether apparent agreement is voluntary, pressured, coerced, compelled, or unknown;
- whether consent can be safely withdrawn;
- consequences for refusal or resistance;
- fear and reduced autonomy;
- dependency and escalation;
- supporting evidence;
- counterevidence;
- plausible alternative explanations.

Compliance must not automatically be interpreted as consent.

## Australian jurisdiction layer

Legal status is represented separately from semantic recognition.

The glossary supports machine-readable jurisdiction records so systems can distinguish national safeguarding concepts from jurisdiction-specific legal tests and commencement states.

A match against a `CCI-*` indicator does not establish that any criminal, civil, family-law, or other statutory test has been satisfied.

## Machine decision boundary

AI and automated systems may:

- recognise candidate indicators;
- translate everyday descriptions into candidate concepts;
- correlate observations over time;
- identify possible escalation and multi-domain patterns;
- surface evidence and counterevidence;
- preserve uncertainty;
- identify relevant jurisdiction information;
- recommend appropriate safeguarding review.

AI and automated systems must not:

- automatically label a person an abuser;
- automatically label a person a victim-survivor;
- represent a safeguarding assessment as a legal finding;
- assume one jurisdiction's law applies nationally;
- infer abuse from demographic characteristics;
- equate ordinary disagreement with coercive control;
- automatically contact the person suspected of exercising control;
- unnecessarily disclose sensitive information;
- initiate punitive action solely from an automated assessment.

## Machine-readable package

The glossary is designed to support:

- HTML;
- JSON;
- JSON-LD;
- CSV;
- Turtle / RDF;
- RDF/XML;
- JSON Schema validation;
- machine-readable examples;
- provenance and source registries;
- distribution manifests;
- integrity manifests and checksums.

## Cross-glossary interoperability

Related concepts may link to the Glossary of Human Trafficking without asserting equivalence.

Examples include:

- `CCI-MOVEMENT-RESTRICTION` related to `HTI-RESTRICTION-OF-MOVEMENT`;
- `CCI-DOCUMENT-PASSPORT` related to `HTI-DOCUMENT-RETENTION`;
- `CCI-PSYCHOLOGICAL-INTIMIDATION` related to `HTI-THREATS`.

## Governance principle

People describe experiences. Machines identify candidate concepts. Evidence establishes context. Patterns support assessment. Jurisdiction rules determine legal relevance. Authorised humans make consequential decisions.
