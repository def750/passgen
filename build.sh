#!/bin/sh
set -eu

cd "$(dirname "$0")"

uvx --from pyinstaller pyinstaller --onefile --name passgen generator.py
install -Dm755 dist/passgen "$HOME/.local/bin/passgen"

echo "Installed passgen to $HOME/.local/bin/passgen"

