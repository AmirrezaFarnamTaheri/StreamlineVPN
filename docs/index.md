CleanConfigs SubMerger
======================

A trustworthy, fast, maintainable public VPN subscription aggregator. Auto-discovers sources, verifies endpoints by real connectivity and QoS, dedups and ranks nodes with transparent scoring, and exports client-valid artifacts with enterprise-grade security and observability.

Highlights
----------

- ML-powered quality scoring (41 features) with drift detection
- Zero-trust validation pipeline + warm-up FSM (new → probation → trusted → suspended)
- K8s-ready deployment with metrics and tracing
- Multi-tier caching and adaptive processing

Quick Links
-----------

- Production sources: `config/sources.production.yaml`
- Advanced sources (legacy toolchain): `sources.json`
- FSM state: `config/source_states.json`
- Main runner: `vpn_merger.py`
