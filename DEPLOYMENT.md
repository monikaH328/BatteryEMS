# BatteryEMS deployment

## Local
```bash
source .venv/bin/activate
python3 app.py
```
Open `http://127.0.0.1:5000`.

## Public web app
A localhost app cannot appear in Google Search. Deploy the web app to a public HTTPS domain first. The application already exposes `robots.txt`, `sitemap.xml`, crawlable title/description metadata, and a health endpoint.

For a first deployment, use a Python web host that can run:
```bash
python app.py
```
with environment variable `HOST=0.0.0.0` and the host-provided `PORT`.

After deployment:
1. Open the public HTTPS URL.
2. Verify `/health`, `/robots.txt`, and `/sitemap.xml`.
3. Add the domain to Google Search Console.
4. Submit `/sitemap.xml` and inspect the home page URL.
5. Keep a public landing page with descriptive text; do not make the initial HTML only an empty JavaScript shell.

Google can render JavaScript, but crawlability and indexability still depend on a successful public HTTP response and accessible rendered content.
