# Advanced Protocol Mergers

This directory contains standalone tools for merging and testing VPN configurations that do not fit into the standard V2Ray ecosystem. Each script collects sources, performs minimal connectivity tests and generates importable files for their respective clients.

## Modules

### http_injector_merger.py
Collects HTTP Injector payloads from public sources and tests them using a basic HTTP request with the specified headers. Successful payloads are saved to `output_http_injector/http_injector_raw.txt`.

Usage:
```bash
python -m advanced_methods.http_injector_merger --sources URL1 URL2
```

### argo_merger.py
Fetches lists of ArgoVPN Falcon or CDN domains. A TLS handshake is performed to verify each domain. Working domains are saved to `output_argo/argo_domains.txt`.

Usage:
```bash
python -m advanced_methods.argo_merger --sources URL1 URL2
```

### tunnel_bridge_merger.py
Handles generic tunnel or bridge endpoints such as `ssh://` or `socks5://` URLs listed in local files. Each host and port is tested with a TCP connection. Valid entries are written to `output_tunnel/tunnel_endpoints.txt`.

Usage:
```bash
python -m advanced_methods.tunnel_bridge_merger --sources file1.txt file2.txt
```

## Importing in Clients

The output files are plain text lists. For mobile apps simply copy the contents or open the file directly. On desktop clients use the "import from file" feature.

## Troubleshooting

These scripts perform only lightweight checks. If a configuration fails to connect in its client, verify network reachability and try running the script again with a different proxy using `--proxy`.
