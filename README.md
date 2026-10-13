# Ki web site

Static site for **Ki** (calisthenics for beginners), served by GitHub Pages from `main` (root):
<https://ekinuzunyayla.github.io/ki-website/>

| Page | Used for |
|---|---|
| `index.html` | Landing page: what Ki does, app screenshots, free core and Pro |
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
Images come from the approved store creatives in `~/Desktop/kip-aso/kreatif/` (app repo decision D124), fonts from the app repo (`../ki`):

| On the site | Source |
|---|---|
| Favicon, touch icon, the icon in the hero | `logo/final/app-store-1024.png` (the "k." app icon) |
| "A look inside" strip | `v2/app-store/iphone-6.9/01…08.png` (store screenshots, round 2) |
| Hero photo and social card, equipment and rest photos | `v2/foto/*.jpg` |
| Phone screenshots in "How it works" | `ham/_prep/android-phone/*.png` (raw app captures) |

The photos are AI images made in Google Flow for the store listing; the licence line is in the app repo's `content-pipeline/LICENSES.md` (2026-10-13). They show a setting, not a result: no before/after, no body claims.

The script needs Pillow, fontTools and brotli:

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
- **Name**: the app is called "Ki" (owner's decision, 2026-10-13). The raw captures were taken while the app still showed the old "kip." wordmark, so the full Today screen (`06-home`) is not used as a phone screenshot; store frame 07 shows only its streak card. Re-capture after the rename if the Today screen is wanted.
- **Contact**: publisher and email are the same as on the Memory site. Swap in a dedicated support address if one is created.
- **Not on the site on purpose**: prices, a session length in minutes (the store sentence is still open), and screen-reader or large-text support (not yet checked on devices).
- The App Store frames are still built from Android captures and will be re-rendered with iOS ones before upload (D124); rebuild the assets after that.
- When the app is live, replace the "Coming soon" note on the home page with the official store badges (follow Apple's and Google's badge guidelines), and refresh the screenshots from the final store set.
- Update the "Last updated" date on `privacy.html` / `terms.html` and `lastmod` in `sitemap.xml` whenever they change.
- With a custom domain later: add a `CNAME`, point DNS at GitHub Pages, and update the absolute `/ki-website/` links (`404.html`, `sitemap.xml`, `robots.txt`, `og:image`, `BASE_PATH` in the build script).
