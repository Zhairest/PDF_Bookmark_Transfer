# Releasing

This file documents the recommended release workflow for `PDF Bookmark Transfer`.

## 1. Update project metadata

- review `CHANGELOG.md`
- review `README.md` and `README_EN.md`
- update version strings if you introduce formal version bumps in code or packaging metadata

## 2. Prepare the build environment

```bash
python3 -m venv .venv-build
./.venv-build/bin/python -m pip install -r requirements-build.txt
```

## 3. Build the macOS application

```bash
./build_macos_app.sh
```

Expected artifacts:

- `dist/PDF Bookmark Transfer.app`
- `dist/PDF Bookmark Transfer-macOS.zip`

## 4. Verify the build

Recommended checks:

- run the GUI locally
- verify the generated app bundle structure
- verify PDF conversion with a known sample pair
- run:

```bash
codesign --verify --deep --strict "dist/PDF Bookmark Transfer.app"
```

## 5. Publish the release

Recommended GitHub release asset:

- `PDF Bookmark Transfer-macOS.zip`

Suggested release notes should mention:

- new features
- bug fixes
- compatibility changes
- any known limitations

## 6. Future hardening

For a more polished public macOS distribution, consider adding:

- Developer ID signing
- notarization
- checksum files
- Windows release artifacts
