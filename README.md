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

## Documentation
- [SITE_BASELINE.md](docs/SITE_BASELINE.md)
- [DEPLOY.md](docs/DEPLOY.md)
- [ROLLBACK.md](docs/ROLLBACK.md)
