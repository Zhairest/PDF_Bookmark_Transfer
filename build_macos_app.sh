#!/bin/zsh

set -euo pipefail

SCRIPT_DIR=${0:a:h}
cd "$SCRIPT_DIR"

VENV_PYTHON="$SCRIPT_DIR/.venv-build/bin/python"
export PYINSTALLER_CONFIG_DIR="$SCRIPT_DIR/.pyinstaller"
APP_PATH="$SCRIPT_DIR/dist/PDF Bookmark Transfer.app"
ZIP_PATH="$SCRIPT_DIR/dist/PDF.Bookmark.Transfer-macOS.zip"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Missing build environment: $VENV_PYTHON" >&2
  echo "Create it first with: python3 -m venv .venv-build" >&2
  exit 1
fi

"$VENV_PYTHON" -m PyInstaller \
  --clean \
  --noconfirm \
  --distpath "$SCRIPT_DIR/dist" \
  --workpath "$SCRIPT_DIR/build" \
  pdf_bookmark_transfer_app.spec

rm -f "$ZIP_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"

echo
echo "Build complete:"
echo "  $APP_PATH"
echo "  $ZIP_PATH"
