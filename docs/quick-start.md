Quick Start
===========

Prerequisites
-------------

- Python 3.10+
- `pip install -r requirements.txt`

Run
---

1. Optionally edit `config/sources.production.yaml` to add/remove sources.
2. Warm up source health and FSM state:

   `python -m vpn_merger.sources.state_fsm`

3. Merge and export:

   `python vpn_merger.py --full-test --output-clash`

4. Artifacts appear in `output/`:

   - `vpn_subscription_base64.txt`
   - `vpn_subscription_raw.txt`
   - `vpn_singbox.json`

5. Serve metrics (optional):

   `python vpn_merger.py --api --metrics-port 8001`
