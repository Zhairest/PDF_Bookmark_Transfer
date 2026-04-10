# Contributing

Thanks for your interest in improving `PDF Bookmark Transfer`.

## Development Setup

### Runtime dependencies

```bash
python3 -m pip install -r requirements.txt
```

### Build dependencies

```bash
python3 -m pip install -r requirements-build.txt
```

## Local Development

Run the desktop app:

```bash
python3 pdf_bookmark_transfer_app.py
```

Run the CLI:

```bash
python3 merge_pdf_bookmarks.py --help
```

Build the macOS app bundle:

```bash
python3 -m venv .venv-build
./.venv-build/bin/python -m pip install -r requirements-build.txt
./build_macos_app.sh
```

## Contribution Guidelines

- Keep the terminology consistent: `Content PDF` and `Bookmark source PDF`
- Prefer cross-platform changes unless the improvement is intentionally platform-specific
- When updating the GUI, keep macOS and Windows behavior in mind
- If you change the workflow or packaging process, update both `README.md` and `README_EN.md`
- If you add or change release steps, update `CHANGELOG.md`

## Pull Requests

- Keep pull requests focused and easy to review
- Include a short description of user-facing impact
- Mention any manual verification you performed
- Add screenshots only when they reflect the real application state

## Reporting Issues

Useful details include:

- operating system and version
- Python version
- whether you used the GUI or CLI
- whether the two PDFs have identical pagination
- a minimal reproduction description
