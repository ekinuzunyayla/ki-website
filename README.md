# Kip web site

Static site for **Kip** (calisthenics for beginners; the name is provisional), meant for GitHub Pages from `main` (root):
<https://ekinuzunyayla.github.io/ki-website/>

| Page | Used for |
|---|---|
| `index.html` | Landing page: what Kip does, app screenshots, free core and Pro |
| `privacy.html` | Privacy Policy URL (App Store Connect, Play Console, paywall, store description) |
| `terms.html` | Terms of Use URL (paywall, store description) |
| `support.html` | Support URL (App Store Connect) and FAQ |
| `404.html` | Served by GitHub Pages for any missing path |

Plain HTML and CSS, no build step, no cookies, no scripts, no third-party requests. Dark only, like v1 of the app. Colors, type and radii follow the app's token set (`docs/design/tokens.md`, Theme A). Fonts are self-hosted Bricolage Grotesque and Manrope (OFL, `assets/fonts/OFL-*.txt`).

Copy follows the app repo's rules: the approved store text, no health or body claims, no prices (they come from the store), US English. Lint it with the app repo's `claims-and-copy` script:

```bash
python3 ../ki/.claude/skills/claims-and-copy/scripts/copy_lint.py *.html
```

## Rebuilding assets
Screenshots come from the raw captures behind the store set (`~/Desktop/kip-aso/kreatif/ham/`), fonts from the app repo (`../ki`). The app has no icon yet, so the favicon and social card are drawn from the "kip." wordmark. The script needs Pillow, fontTools and brotli:

```bash
python3 -m venv .venv && .venv/bin/pip install pillow fonttools brotli
.venv/bin/python scripts/build_assets.py            # rebuild assets/, then check
.venv/bin/python scripts/build_assets.py --check    # glyph coverage + broken links only
```

## Before launch
The legal pages describe the app as it is meant to ship in v1. Each line below must be true on launch day, or the page changes first.

- **Lawyer review** of `privacy.html` and `terms.html` (app repo: product doc 05, D70, 11 §3): Washington My Health My Data Act and similar state laws, FTC Health Breach Notification Rule, the age wording, the exercise-risk and liability sections, governing law.
- **Usage data** (`privacy.html` §4): PostHog and Sentry are named as providers and the eight events are listed from ADR-031. Today the app sends nothing. When the SDKs are bound, check the event list, what the SDK adds by itself (ID, device details, IP handling), the hosting region and the retention period, and whether the "Share anonymous usage data" switch also covers crash reports. If v1 ships without them, say so in §4 instead.
- **Delete my data** (`privacy.html` §11): the text says the app asks our server to delete the RevenueCat customer (D83). That needs the Supabase function to exist and stay reachable (open question A18).
- **Name and identity**: "Kip" is provisional (D79). If the name changes, the pages, `og.png` and the icons change with it.
- **Contact**: publisher and email are the same as on the Memory site. Swap in a dedicated support address if one is created.
- **Not on the site on purpose**: prices, a session length in minutes (the store sentence is still open), and screen-reader or large-text support (not yet checked on devices).
- When the app is live, replace the "Coming soon" note on the home page with the official store badges (follow Apple's and Google's badge guidelines), and refresh the screenshots from the final store set.
- Update the "Last updated" date on `privacy.html` / `terms.html` and `lastmod` in `sitemap.xml` whenever they change.
- With a custom domain later: add a `CNAME`, point DNS at GitHub Pages, and update the absolute `/ki-website/` links (`404.html`, `sitemap.xml`, `robots.txt`, `og:image`, `BASE_PATH` in the build script).
