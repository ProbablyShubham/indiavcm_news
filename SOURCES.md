# Source strategy

The feed is intentionally **source-configured and reviewable**. `config/sources.yml` contains the discovery queries and can be changed without editing Python.

The initial set covers four layers:

1. **Indian carbon-market regulation and institutions** — Indian Carbon Market / CCTS, Bureau of Energy Efficiency, government and UNFCCC Article 6 coverage.
2. **Registry and standards activity** — Verra, Gold Standard, integrity/standards bodies and methodology developments relevant to India.
3. **Indian VCM project activity** — carbon projects, issuance/retirement, project sectors and developers.
4. **Independent reporting** — broader Indian/business/environment reporting, with deterministic relevance filtering and deduplication.

Google News RSS is the common discovery transport in v1 because it is public, needs no API key, and can target official domains as well as topic queries. The collector also supports ordinary RSS/Atom URLs (`type: rss`) so direct publisher feeds can be substituted or added whenever they are available and stable.

## Editorial / data principles

- Inclusion is algorithmic and configuration-driven, not an endorsement of a publisher or claim.
- The feed retains publisher attribution and links users to the source.
- The pipeline stores a short RSS-supplied snippet only; it does not scrape or republish article bodies.
- Geography is a derived analytical field and always carries a method/confidence indicator.
- A district/state mention does not imply that every VCM project in that geography is discussed by the story. Geographic relationships are explicitly labelled separately from direct project/developer/methodology matches.
- Third-party headlines/snippets remain subject to the rights and terms of their original publishers; the MIT license applies to this repository's software, not third-party content.
