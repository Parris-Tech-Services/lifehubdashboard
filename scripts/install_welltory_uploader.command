#!/bin/bash
# Double-click this file in Finder to install and start the Welltory uploader via launchd.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$DIR/install_welltory_uploader.sh"
if [ ! -x "$SCRIPT" ]; then
  # ensure script is executable
  chmod +x "$SCRIPT" 2>/dev/null || true
fi
"$SCRIPT"
echo
echo "Installer finished. Press any key to close this terminal window."
read -n1 -s -r
