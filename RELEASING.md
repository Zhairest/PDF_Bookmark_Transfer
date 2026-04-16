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

## 3. Build the desktop packages locally

### macOS

```bash
./build_macos_app.sh
```

Expected macOS artifacts:

- `dist/PDF Bookmark Transfer.app`
- `dist/PDF.Bookmark.Transfer-macOS.zip`

### Windows

```powershell
.\build_windows_app.ps1
```

Expected Windows artifact:

- `dist/PDF.Bookmark.Transfer-windows.zip`

## 4. Automated GitHub release flow

The repository includes `.github/workflows/release.yml`.

When a tag matching `v*` is pushed:

- GitHub Actions builds the macOS package on `macos-14`
- GitHub Actions builds the Windows package on `windows-latest`
- both `.zip` files are attached to the GitHub Release
- `SHA256SUMS.txt` is generated and uploaded with the release assets

## 5. Verify the build

Recommended checks:

- run the GUI locally
- verify the generated app bundle structure
- verify PDF conversion with a known sample pair when available
- run:

```bash
codesign --verify --deep --strict "dist/PDF Bookmark Transfer.app"
```

## 6. Publish the release

Recommended release sequence:

1. Commit the release-ready changes.
2. Push the commit to `main`.
3. Create and push a version tag such as `v0.2.0`.
4. Wait for the `release` workflow to finish.
5. Confirm that the release contains:

- `PDF.Bookmark.Transfer-macOS.zip`
- `PDF.Bookmark.Transfer-windows.zip`
- `SHA256SUMS.txt`

Release notes should summarize:

- new features
- bug fixes
- compatibility changes
- any known limitations

## 7. Future hardening

For a more polished public macOS distribution, consider adding:

- Developer ID signing
- notarization
- Windows code signing
