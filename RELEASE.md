# Filepilot Release Process


This document describes how to release a new version of Filepilot to PyPI.

## Prerequisites

1. Ensure you have the latest version of build tools:
```bash
python -m pip install --upgrade pip build twine
```

2. Create a PyPI account if you don't have one at https://pypi.org

## Release Steps

1. Update version number in `setup.py`

2. Create distribution packages:
```bash
python -m build
```

3. Upload to PyPI:
```bash
python -m twine upload dist/*
```

4. Create a new git tag:
```bash
git tag v$(python setup.py --version)
git push origin v$(python setup.py --version)
```

## Testing the Release

1. Create a new virtual environment
2. Install the package:
```bash
pip install filepilot
```
3. Verify the installation works:
```bash
filepilot --version
```

## Troubleshooting

If you encounter issues during upload:
- Ensure you have the correct PyPI credentials
- Check that the version number hasn't been used before
- Verify the package builds correctly locally