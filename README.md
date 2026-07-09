# tokoroten-site

ところてん.tokyo WordPress Lab

## Structure
- theme/cocoon-child-master/ - Child theme
- plugins/a-court-ad-slots/ - Ad slots plugin (future)
- docs/ - Documentation
- scripts/ - Deploy/rollback scripts
- content-samples/ - Sample content
- tools/ - Content/CI validation scripts

## Quick Start
```bash
./scripts/deploy.sh      # Deploy to Xserver
./scripts/rollback.sh    # Rollback to baseline
```

## Content Package Validation

Every `content-samples/*/` article package (`post.md`, `metadata.json`,
`source-notes.md`, `README.md`, and referenced images) is checked by
`tools/validate_content_package.py`, using only the Python 3 standard
library. It runs automatically on pull requests that touch
`content-samples/**` (see `.github/workflows/content-package-validation.yml`).

```bash
# Validate a single package
python3 tools/validate_content_package.py content-samples/golden-article-001

# Validate every package under content-samples/
python3 tools/validate_content_package.py content-samples

# Run the test suite
python3 -m unittest discover -s tests -v
```

## Auto-blog Package Adapter

`tools/build_autoblog_package.py` converts a validated `content-samples/*/`
package into an `Auto-blog`-compatible input ZIP (`post.md` with YAML
frontmatter + `images/`). It only converts a package that already passes
`validate_content_package.py`, always forces `status: draft` in the output,
and never writes a partial ZIP. See
[docs/AUTOBLOG_PACKAGE.md](docs/AUTOBLOG_PACKAGE.md) for the full contract.
Generated ZIPs are a local intermediate artifact only — never push one
manually to WordPress or a VPS.

```bash
python3 tools/build_autoblog_package.py content-samples/golden-article-001 --output dist/
```

## Documentation
- [SITE_BASELINE.md](docs/SITE_BASELINE.md)
- [DEPLOY.md](docs/DEPLOY.md)
- [ROLLBACK.md](docs/ROLLBACK.md)
- [AUTOBLOG_PACKAGE.md](docs/AUTOBLOG_PACKAGE.md)
