# Cloudflare WS+TLS Fallback Pack — Xray + Nginx + Cloudflare

**Goal:** Hide your VLESS service behind Cloudflare with WebSocket + TLS, keep the site looking normal, and route `/ws` to Xray. Production‑ready, Docker‑based, minimal moving parts.

---

## Quickstart

1. **DNS** → In Cloudflare, create an **A** record for your domain (e.g., `vpn.example.com`) to your server IP and turn the orange cloud **ON** (proxied).
2. **TLS mode** → Cloudflare **SSL/TLS** → set to **Full (strict)**.
3. **Origin cert** → Cloudflare **Origin Server** → create an **Origin Certificate** for your hostname; download the **certificate (PEM)** and **private key (PEM)**. Place as `./certs/origin.crt` and `./certs/origin.key` on the server.
4. **Env** → Edit `.env` below (set your domain and UUID).
5. **Run** → `docker compose up -d` → visit `https://vpn.example.com/` (you'll see a normal site), and your client uses `wss://vpn.example.com/ws` via VLESS.

> ℹ️ This pack terminates TLS at **Nginx** using Cloudflare Origin Certs. The **Xray** WebSocket listener runs **without TLS** behind Nginx on the Docker network.

---

## Files & Structure

```
cloudflare-ws-pack/
├─ .env                      # your domain + UUID
├─ .gitignore               # excludes sensitive files
├─ docker-compose.yml       # Docker services configuration
├─ setup.sh                 # Linux/macOS setup script
├─ setup.bat                # Windows setup script
├─ env.example              # environment template
├─ nginx/
│  ├─ conf.d/
│  │  └─ vpn.conf           # nginx reverse proxy + static site + /ws → xray
│  └─ html/
│     └─ index.html         # placeholder legit site
├─ xray/
│  └─ config.json           # VLESS over WebSocket inbound
└─ certs/
   ├─ README.md             # certificate setup instructions
   ├─ origin.crt            # Cloudflare origin certificate (PEM)
   └─ origin.key            # Cloudflare origin private key (PEM)
```

---

## Setup Instructions

### 1. Environment Configuration

Copy the example environment file and configure it:

```bash
cp env.example .env
# Edit .env with your domain and UUID
```

### 2. Cloudflare Configuration

1. **DNS Setup**: Create an A record for your domain pointing to your server IP with Cloudflare proxy enabled (orange cloud)
2. **SSL/TLS**: Set to "Full (strict)" mode
3. **Origin Certificate**: Create and download the certificate files to `./certs/`

### 3. Certificate Setup

Place your Cloudflare Origin Certificate files:
- `./certs/origin.crt` - Certificate (PEM format)
- `./certs/origin.key` - Private key (PEM format)

### 4. Deploy

#### Quick Setup (Recommended)

**Linux/macOS:**
```bash
# Make setup script executable and run
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
# Run the setup script
setup.bat
```

#### Manual Setup

```bash
# Start the services
docker compose up -d

# Check logs
docker compose logs -f nginx
```

---

## Client Configuration

### VLESS (WS + TLS via Cloudflare)

```
vless://<UUID>@$DOMAIN:443?encryption=none&security=tls&type=ws&path=%2Fws&sni=$DOMAIN#CF-WS
```

### sing-box outbound

```json
{
  "type": "vless",
  "tag": "cf-ws",
  "server": "$DOMAIN",
  "server_port": 443,
  "uuid": "<UUID>",
  "tls": { "enabled": true, "server_name": "$DOMAIN" },
  "transport": { "type": "ws", "path": "/ws" }
}
```

---

## Cloudflare Settings (Recommended)

* **DNS**: A/AAAA for `$DOMAIN` with **proxied** turned on (orange cloud)
* **SSL/TLS → Overview**: **Full (strict)**
* **Edge Certificates**:
  * Always Use HTTPS: **On**
  * HTTP/2: **On**
  * WebSockets: **On**
  * (Optional) 0‑RTT: On
* **Origin Server**: Use **Origin Certificate** (placed in `./certs/`)
* **Caching**: No special rule needed; `/ws` is proxied as WebSocket

> If you use a CDN "Under Attack Mode", WebSocket still works, but some enterprise WAF rules can interfere. Verify `/ws` is allowed.

---

## Security (Optional)

### Restrict to Cloudflare IPs

If you expose 443 to the internet, restrict it to Cloudflare's egress ranges:

```bash
# iptables example (IPv4), make sure to persist with your distro's method
# Fetch Cloudflare IPv4 ranges
curl -s https://www.cloudflare.com/ips-v4 | while read range; do
  iptables -I INPUT -p tcp --dport 443 -s "$range" -j ACCEPT
  iptables -I INPUT -p tcp --dport 80  -s "$range" -j ACCEPT
done
# Default drop (ensure SSH is still allowed!)
iptables -A INPUT -p tcp --dport 443 -j DROP
iptables -A INPUT -p tcp --dport 80  -j DROP
```

> Alternatively, use **UFW** with an **ipset** or your cloud firewall (AWS SG/GCP FW/DO FW) to allow only Cloudflare IPs. Remember to allow SSH from your IP range first.

---

## Troubleshooting

* **521/522/525 from Cloudflare** → Check `docker compose logs -f nginx`; ensure cert paths are correct and Cloudflare mode is **Full (strict)**
* **400/502 on `/ws`** → Verify Nginx `proxy_set_header Upgrade/Connection` and `proxy_pass http://xray:10000;`
* **Client stuck** → Confirm client uses **TLS + WS** with `sni=$DOMAIN` and `path=/ws`
* **Real IP in logs** → Add Cloudflare real‑IP restore (optional):

  ```nginx
  # /etc/nginx/conf.d/realip.conf (include in server or http block)
  set_real_ip_from 103.21.244.0/22;  # repeat for all CF ranges
  real_ip_header CF-Connecting-IP;
  ```

  (List: [https://www.cloudflare.com/ips/](https://www.cloudflare.com/ips/))

---

## Health Checks

```bash
curl -I http://$DOMAIN/health
curl -I https://$DOMAIN/health
```

---

## Integration with VPN Merger

This deployment pack integrates seamlessly with the VPN Merger project:

1. **Node Generation**: Use the Xray REALITY installer script (`scripts/install-reality.sh`) to generate server configurations
2. **Node Aggregation**: The Free Nodes Aggregator can collect and validate nodes from this deployment
3. **Client Management**: Use the Universal Client & QR tool to manage and distribute client configurations
4. **Analytics**: Monitor deployment health and performance through the integrated analytics dashboard

---

## Extensions

### Add REALITY Fallback (Advanced)

You can add a second inbound on **Xray** for REALITY on a high port and route it via port‑forwarding or a different hostname (not proxied). Keep it separate from this CF WS stack to reduce blast radius.

### Auto-renew with DNS-01

For automatic certificate renewal, consider integrating with lego/ACME for Cloudflare DNS-01 challenges.

---

### That's it

This pack pairs perfectly with your **Universal Client & QR** helper. Import the VLESS link, generate QR, and ship. The deployment is production-ready and integrates seamlessly with the broader VPN Merger ecosystem.
