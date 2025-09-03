# Cloudflare Origin Certificates

This directory should contain your Cloudflare Origin Certificates:

- `origin.crt` - Cloudflare Origin Certificate (PEM format)
- `origin.key` - Cloudflare Origin Private Key (PEM format)

## How to obtain these certificates:

1. Go to your Cloudflare dashboard
2. Navigate to **SSL/TLS** → **Origin Server**
3. Click **Create Certificate**
4. Configure the certificate:
   - **Hostnames**: Your domain (e.g., `vpn.example.com`)
   - **Certificate Validity**: 15 years (recommended)
   - **Key type**: RSA (2048)
5. Download the certificate and private key
6. Save them as `origin.crt` and `origin.key` in this directory

## Security Note

- Keep these files secure and never commit them to version control
- The `.gitignore` file should already exclude this directory
- These certificates are only valid for your specific domain

## File Permissions

Make sure the files have appropriate permissions:

```bash
chmod 600 origin.key
chmod 644 origin.crt
```
