# DEPLOY GUIDE

## Prerequisites
- SSH key: ~/.ssh/xserver_mof
- Server: aitah@sv16590.xserver.jp:10022

## Deploy Child Theme
```bash
./scripts/deploy.sh
```

## Manual Deploy
```bash
scp -i ~/.ssh/xserver_mof -P 10022 -r \
  theme/cocoon-child-master/* \
  aitah@sv16590.xserver.jp:~/xn--28jvbe3m5a.tokyo/public_html/wp-content/themes/cocoon-child-master/
```

## Clear Cache
```bash
ssh -i ~/.ssh/xserver_mof -p 10022 aitah@sv16590.xserver.jp \
  "cd ~/xn--28jvbe3m5a.tokyo/public_html && wp cache flush"
```

## Verify
1. curl -sI https://xn--28jvbe3m5a.tokyo/
2. Check footer/changes in browser
