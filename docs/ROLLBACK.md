# ROLLBACK GUIDE

## Quick Rollback (Git tag)
```bash
git checkout baseline-2026-06
./scripts/deploy.sh
```

## Emergency Rollback (Backup)
```bash
ssh -i ~/.ssh/xserver_mof -p 10022 aitah@sv16590.xserver.jp \
  "cd ~/xn--28jvbe3m5a.tokyo/public_html/wp-content/themes && \
   tar -xzf ~/backups/tokoroten/20260621/themes_cocoon.tar.gz"
```

## Full Site Restore
See: /home/aitah/backups/tokoroten/20260621/RUNBOOK.md

## Estimated Recovery Time
- Git rollback: ~2 min
- Backup restore: ~5 min
- Full restore: ~10 min
