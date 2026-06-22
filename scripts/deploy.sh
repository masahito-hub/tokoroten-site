#!/bin/bash
set -e
REMOTE="aitah@sv16590.xserver.jp"
PORT=10022
KEY="$HOME/.ssh/xserver_mof"
DEST="~/xn--28jvbe3m5a.tokyo/public_html/wp-content/themes/cocoon-child-master/"
SRC="$(dirname "$0")/../theme/cocoon-child-master/"

echo "Deploying to $REMOTE..."
scp -i "$KEY" -P $PORT -r "$SRC"* "$REMOTE:$DEST"
ssh -i "$KEY" -p $PORT "$REMOTE" "cd ~/xn--28jvbe3m5a.tokyo/public_html && wp cache flush 2>/dev/null || true"
echo "Deploy complete. Verify: https://xn--28jvbe3m5a.tokyo/"
