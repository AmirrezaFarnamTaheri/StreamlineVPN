# Advanced Protocol Mergers

This folder contains standalone tools for protocols that are not covered by
`vpn_merger.py`. Each script downloads sources, performs a quick connectivity
check and saves the working entries in its own output folder. If you do not pass
the `--sources` option, the default URLs are read from the project-wide
`sources.json` file. Edit that JSON file to point the tools at your own lists.

## ⚠️ Security & Privacy Warning

- These scripts fetch configurations from public sources run by unknown parties.
- **Do not use them for logins, banking or other sensitive tasks.**
- You are using the results entirely at your own risk.

## Requirements
1. Install Python 3.8 or newer.
2. Install dependencies with:
   ```bash
   pip install -r requirements.txt
   ```
   This installs `aiohttp`, `aiodns`, `nest-asyncio`, `PyYAML` and `tqdm`.
3. All scripts accept the common options `--proxy` to route requests through a
   proxy, `--test-timeout` to adjust connection checks, and `--output-dir` to
   choose where files are written.

### Zero to Hero Quick Guide

1. Pick the script matching your protocol (`http_injector_merger.py`,
   `argo_merger.py` or `tunnel_bridge_merger.py`).
2. Supply one or more source URLs with `--sources` or edit `sources.json`.
3. Run the script. Add `--proxy` if your network blocks access to the sources.
4. Import the generated files in your client:
   - **HTTP Injector** – use **Import Config** on Android or the PC edition.
   - **ArgoVPN/Hiddify Next** – load the `argo_domains.txt` file via the Argo
     domain list option.
   - **Tunnel bridges** – import `tunnel_endpoints.txt` into NekoRay or open it
     with SocksDroid.


## Output Overview

| Script | Output File | How to Import |
| ------ | ----------- | ------------- |
| `http_injector_merger.py` | `http_injector_raw.txt` | Use **Import Config** in the HTTP Injector app or PC edition. |
| `argo_merger.py` | `argo_domains.txt` | Load as an Argo domain list in ArgoVPN or Hiddify Next. |
| `tunnel_bridge_merger.py` | `tunnel_endpoints.txt` | Add endpoints from this file in NekoRay or SocksDroid. |

## `http_injector_merger.py`
1. **Gather sources** – collect one or more `.ehi` links or text files and pass them with `--sources`.
2. **Run the merger**
   ```bash
   python -m advanced_methods.http_injector_merger --sources URL1 file.txt \
       --output-dir output_http_injector --proxy socks5://127.0.0.1:9050 \
       --test-timeout 5
   ```
3. **Check the output** – the file `output_http_injector/http_injector_raw.txt` will contain lines such as:
   ```
   CONNECT example.com:80
   CONNECT anotherhost:80
   ```
4. **Import into clients**
   - **Windows** – HTTP Injector PC edition: choose **`Config`** → **`Import`** and select the file.
   - **Android** – HTTP Injector app: open the menu, tap **`Import Config`** and pick `http_injector_raw.txt`.

## `argo_merger.py`
1. **Prepare lists** – supply Falcon/CDN domain lists with `--sources`.
2. **Run the merger**
   ```bash
   python -m advanced_methods.argo_merger --sources URL1 URL2 \
       --output-dir output_argo --proxy http://127.0.0.1:8080 \
       --test-timeout 5
   ```
3. **Check the output** – the resulting file `output_argo/argo_domains.txt` may contain lines like:
   ```
   example.cloudflare.com
   another.workers.dev
   ```
4. **Import into clients**
   - **Hiddify Next (Windows/macOS/iOS)** – click the **`+`** button, choose **`Add Argo domain list`** and load the file.
   - **Android** – ArgoVPN: go to **`Falcon`**, tap **`Import from file`** and select `argo_domains.txt`.

## `tunnel_bridge_merger.py`
1. **Prepare endpoints** – create text files with `ssh://`, `socks5://` or similar URLs and pass them via `--sources`.
2. **Run the merger**
   ```bash
   python -m advanced_methods.tunnel_bridge_merger --sources bridges1.txt bridges2.txt \
       --output-dir output_tunnel --proxy socks5://127.0.0.1:9050 \
       --test-timeout 5
   ```
3. **Check the output** – `output_tunnel/tunnel_endpoints.txt` will contain lines such as:
   ```
   ssh://user@1.2.3.4:22
   socks5://5.6.7.8:1080
   ```
4. **Import into clients**
   - **Windows/Linux/macOS** – NekoRay (or Qv2ray) via **`Program`** → **`Add profile from file`**.
   - **Android** – SocksDroid or similar tools can open the file and connect to a selected endpoint.

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
