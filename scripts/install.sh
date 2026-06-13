#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install git+https://github.com/<owner>/xmosaic.git

echo "Installed xMosaic. Restart your shell, then run: xmosaic doctor"

