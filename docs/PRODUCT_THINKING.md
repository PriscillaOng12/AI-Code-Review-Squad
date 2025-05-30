# Product Thinking

Building automated code review tools is as much about understanding developer workflows and pain points as it is about implementing technology.  This document explains the rationale behind **ai‑code‑review‑squad**, the personas it serves, and the roadmap guiding its evolution.

## Personas & Jobs to Be Done

| Persona      | Goals                                                         | Pain Points                                              |
|-------------|---------------------------------------------------------------|-----------------------------------------------------------|
| **Engineering Manager** | Reduce security risk and technical debt; ensure code quality and consistency across teams. | Lacks visibility into the effectiveness of manual code reviews; limited bandwidth of senior engineers. |
| **Developer** | Deliver high‑quality code quickly; learn from feedback. | Manual reviews are slow; feedback is inconsistent; security concerns are hard to spot. |
| **Security Engineer** | Identify and remediate vulnerabilities early in the development lifecycle. | Manual penetration testing and SAST tools catch issues late; alert fatigue from noisy findings. |
| **Product Manager** | Ship features faster while maintaining reliability. | Balancing speed and quality; quantifying improvements. |

## Why Multi‑Agent?

Modern AI models are powerful but not omnipotent.  Different specialised agents can excel at specific tasks, providing better coverage and explainability than a monolithic model.  We chose to implement separate agents for security, style, logic, performance and architecture because:

* **Coverage:** A security-focused agent can be tuned to catch OWASP Top 10 issues, while a style agent enforces code formatting and naming conventions.
* **Explainability:** Each agent reports its own findings, making it clear which class of issue was detected and how to remediate it.
* **Blast radius:** Isolating agents means that failures or hallucinations in one agent do not contaminate others.  We can roll out new models incrementally.

## KPIs & Metrics

We track a set of key performance indicators to measure impact and guide product decisions:

* **Time‑to‑First‑Critical (TTFC):** Median time from pull request creation to the first critical or high severity finding.
* **Critical Surfacing Rate:** Percentage of reviews that surface at least one critical finding.
* **False Positive Rate:** Ratio of dismissed findings within 24 hours to total findings.  A lower value indicates higher precision.
* **Triage Completion:** Percentage of findings that are acted upon (either resolved or exported to PR comments).

These KPIs are computed in the analytics notebook and surfaced in dashboards.  See `docs/ANALYTICS.md` for formulas and example queries.

## Roadmap

1. **Foundations (v1)** – Deliver a reliable and secure core product with GitHub integration, multi‑agent analysis, basic analytics and cloud‑native infrastructure.  This repository represents the culmination of that work.
2. **Collaborative triage (v1.5)** – Introduce conversation threads around findings, assign owners and integrate with issue trackers.  Add per‑project baselines to reduce noise.
3. **Custom rules & models (v2)** – Allow customers to author custom detection rules and provide fine‑tuned models.  Support plug‑and‑play for other VCS providers (GitLab, Bitbucket).
4. **Multi‑region & scaling (v3)** – Expand to multiple regions for low latency, active/active failover and enterprise SLAs.  Implement per‑tenant isolation of worker pools and data planes.

We welcome feedback and contributions that align with this vision.