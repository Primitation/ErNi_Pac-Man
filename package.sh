#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# package.sh — builds a self-contained Linux folder in dist/, ready to
# upload to itch.io manually (drag-and-drop the folder or a zip of it).
#
# Why this approach: MiniLibX is X11 / Linux-only, so there's no
# meaningful Windows/macOS build to produce. Rather than freezing a
# single binary (PyInstaller can be fragile with native extensions),
# this ships the actual venv (as real files, not symlinks — see
# --copies in the Makefile's `install` target) plus a launcher script.
# `mlx` is imported as a normal Python package (`from mlx import Mlx`),
# and its compiled extension already lives inside the venv's
# site-packages after `pip install`, so copying the venv is sufficient
# — no separate .so handling needed. The result runs on any Linux
# desktop with X11 — no internet access or setup required by the player.
# ---------------------------------------------------------------------------

APP_NAME="pacman-42"
VERSION="${1:-0.1.0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$ROOT_DIR/dist/${APP_NAME}-linux"
VENV_DIR="$ROOT_DIR/.venv"

echo "==> [1/5] Ensuring the venv + MiniLibX are built (make install)"
make -C "$ROOT_DIR" install

echo "==> [2/5] Cleaning previous package output"
rm -rf "$ROOT_DIR/dist"
mkdir -p "$DIST_DIR"

echo "==> [3/5] Copying application source and assets"
cp -r "$ROOT_DIR/pacman.py"   "$DIST_DIR/"
cp -r "$ROOT_DIR/config.json" "$DIST_DIR/"
cp -r "$ROOT_DIR/Engine"      "$DIST_DIR/"
cp -r "$ROOT_DIR/game"        "$DIST_DIR/"
cp -r "$ROOT_DIR/assets"      "$DIST_DIR/"
# Strip bytecode caches picked up from the dev tree.
find "$DIST_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "==> [4/5] Copying self-contained Python venv (includes the mlx extension)"
cp -r "$VENV_DIR" "$DIST_DIR/.venv"

echo "==> [5/5] Writing launcher and copying in-package instructions"
cat > "$DIST_DIR/run.sh" << 'EOF'
#!/usr/bin/env bash
# Launcher used by the itch app (see itch.toml) and by players running
# the game manually from the extracted folder.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
exec "$DIR/.venv/bin/python" "$DIR/pacman.py" "$DIR/config.json" "$@"
EOF
chmod +x "$DIST_DIR/run.sh"

cp "$ROOT_DIR/Controls.md" "$DIST_DIR/Controls.md"
[ -f "$ROOT_DIR/itch.toml" ] && cp "$ROOT_DIR/itch.toml" "$DIST_DIR/itch.toml"

echo "==> Zipping for upload (optional convenience alongside the folder)"
( cd "$ROOT_DIR/dist" && zip -rq "${APP_NAME}-linux-${VERSION}.zip" "${APP_NAME}-linux" )

echo ""
echo "✔ Package folder: dist/${APP_NAME}-linux/"
echo "✔ Zip for upload: dist/${APP_NAME}-linux-${VERSION}.zip"
echo ""
echo "Test it locally first:"
echo "  cd dist/${APP_NAME}-linux && ./run.sh"
echo ""
echo "Then upload dist/${APP_NAME}-linux-${VERSION}.zip (or the folder"
echo "itself) manually on your itch.io project page."
