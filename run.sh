#!/usr/bin/env bash
set -euo pipefail

mkdir -p output config logs

if [ ! -f config/vpn-merger.yaml ]; then
  cat > config/vpn-merger.yaml << 'EOF'
network:
  concurrent_limit: 50
  request_timeout: 30
testing:
  enable_url_testing: true
  test_timeout: 5.0
processing:
  batch_size: 1000
output:
  output_dir: "./output"
  output_formats: ["raw", "base64"]
monitoring:
  enable_dashboard: true
  enable_metrics: true
  dashboard_port: 8000
  metrics_port: 8001
EOF
fi

python vpn_merger.py --config config/vpn-merger.yaml || python vpn_merger.py


