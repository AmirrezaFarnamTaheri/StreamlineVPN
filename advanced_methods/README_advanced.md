# Advanced Protocol Mergers

This folder contains standalone tools for protocols that are not covered by
`vpn_merger.py`. Each script downloads sources, performs a quick connectivity
check and saves the working entries in its own output folder. If you do not pass
the `--sources` option, the default URLs are read from the project-wide
`sources.json` file. Edit that JSON file to point the tools at your own lists.

## Requirements
1. Install Python 3.8 or newer.
2. Install dependencies with:
   ```bash
   pip install -r requirements.txt
   ```
3. All scripts accept the common options `--proxy` to route requests through a
   proxy and `--output-dir` to choose where files are written.

## Output Overview

| Script | Output File | How to Import |
| ------ | ----------- | ------------- |
| `http_injector_merger.py` | `http_injector_raw.txt` | Use **Import Config** in the HTTP Injector app or PC edition. |
| `argo_merger.py` | `argo_domains.txt` | Load as an Argo domain list in ArgoVPN or Hiddify Next. |
| `tunnel_bridge_merger.py` | `tunnel_endpoints.txt` | Add endpoints from this file in NekoRay or SocksDroid. |

## `http_injector_merger.py`
1. Gather one or more `.ehi` links or text files and pass them with `--sources`.
2. Run the merger:
   ```bash
   python -m advanced_methods.http_injector_merger --sources URL1 URL2 \
       --output-dir output_http_injector --proxy socks5://127.0.0.1:9050
   ```
3. After it finishes, open `output_http_injector/http_injector_raw.txt`.
4. Import examples:
   - **Windows** – HTTP Injector PC edition: choose **`Config`** → **`Import`** and
     select the file.
   - **Android** – HTTP Injector app: open the menu, tap **`Import Config`** and
     pick `http_injector_raw.txt`.

## `argo_merger.py`
1. Provide Falcon/CDN domain lists via `--sources`.
2. Execute the script:
   ```bash
   python -m advanced_methods.argo_merger --sources URL1 URL2 \
       --output-dir output_argo --proxy http://127.0.0.1:8080
   ```
3. Working domains are written to `output_argo/argo_domains.txt`.
4. Import examples:
   - **Windows** – Hiddify Next: click the **`+`** button, choose **`Add Argo domain list`** and load the file.
   - **Android** – ArgoVPN: go to **`Falcon`**, tap **`Import from file`** and
     select `argo_domains.txt`.

## `tunnel_bridge_merger.py`
1. Create text files containing `ssh://`, `socks5://` and similar URLs.
2. Run the merger:
   ```bash
   python -m advanced_methods.tunnel_bridge_merger --sources bridges1.txt bridges2.txt \
       --output-dir output_tunnel --proxy socks5://127.0.0.1:9050
   ```
3. Results are stored in `output_tunnel/tunnel_endpoints.txt`.
4. Import examples:
   - **Windows** – NekoRay: use **`Program`** → **`Add profile from file`** to
     import the endpoint list.
   - **Android** – SocksDroid or similar tools can open the file and connect to a
     selected endpoint.

## Troubleshooting
- **Empty output file** – The sources may be offline or blocked. Retry with a
  different proxy using `--proxy` or verify the URLs.
- **Permission denied** – Run the command from a writable location or specify a
  different `--output-dir`.
- **Import fails in your client** – Make sure the file is saved in UTF‑8 and that
  your client supports the selected protocol.
- **ModuleNotFoundError** – Install the required packages with
  `pip install -r requirements.txt`.
- **Connection errors or timeouts** – The hosts may be unreachable from your
  network. Try using `--proxy` or lower `--concurrent-limit` to reduce load.
