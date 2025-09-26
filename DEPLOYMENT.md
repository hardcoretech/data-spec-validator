# Deployment Guide

This document describes the process for deploying a new version of `data-spec-validator` to PyPI.

## Deployment Methods

There are two ways to deploy to PyPI:

1. **Automated via GitHub Actions** (Recommended) - Automatically publishes when you create a GitHub release
2. **Manual deployment** - Using `twine` directly from your local machine

## Method 1: Automated Deployment via GitHub Actions (Recommended)

### Initial Setup

#### 1. Generate PyPI API Tokens

**For Production PyPI:**

1. Go to <https://pypi.org/manage/account/token/>
2. Click "Add API token"
3. Token name: `data-spec-validator-github-actions` (or any name you prefer)
4. Scope: Select "Project: data-spec-validator" (recommended) or "Entire account"
5. Click "Add token"
6. **Copy the token** (starts with `pypi-`) - you won't see it again!

**For Test PyPI (optional, for manual testing):**

1. Go to <https://test.pypi.org/manage/account/token/>
2. Follow the same steps as above
3. Copy the token

#### 2. Add Tokens to GitHub Secrets

1. Go to repository settings: <https://github.com/hardcoretech/data-spec-validator/settings/secrets/actions>
2. Click **"New repository secret"**
3. For production PyPI:
   - Name: `PYPI_API_TOKEN`
   - Secret: Paste your PyPI token (the `pypi-...` string)
   - Click "Add secret"
4. For Test PyPI (if you want manual testing):
   - Click "New repository secret" again
   - Name: `TEST_PYPI_API_TOKEN`
   - Secret: Paste your Test PyPI token
   - Click "Add secret"

### Deployment Process

#### Option A: Automatic on Release (Production)

1. **Prepare the release** (see "Prepare the Release" section below)
2. **Create a GitHub Release:**
   - Go to <https://github.com/hardcoretech/data-spec-validator/releases/new>
   - Create a new tag: `vX.Y.Z` (e.g., `v3.5.1`)
   - Set release title: `vX.Y.Z`
   - Copy the changelog entry for this version into the description
   - Click "Publish release"
3. **GitHub Actions will automatically:**
   - Build the package
   - Upload to production PyPI
   - You can monitor progress at <https://github.com/hardcoretech/data-spec-validator/actions>

#### Option B: Manual Trigger (Test or Production)

You can manually trigger the workflow to test deployment or deploy to production:

1. **Go to Actions tab:**
   - Visit <https://github.com/hardcoretech/data-spec-validator/actions/workflows/publish.yml>
2. **Click "Run workflow"**
3. **Select target:**
   - Choose `testpypi` to test deployment (requires `TEST_PYPI_API_TOKEN` secret)
   - Choose `pypi` to deploy to production PyPI
4. **Click "Run workflow"**
5. Monitor the workflow execution in the Actions tab

## Method 2: Manual Deployment

### Prerequisites

- Python 3.8 or higher
- `twine` installed (`pip install twine`)
- PyPI account with maintainer permissions for `data-spec-validator`
- PyPI API token configured

### Initial Setup

#### 1. Install Required Tools

```bash
pip install build twine
```

#### 2. Configure PyPI Credentials

**Option 1: Environment Variables (Recommended)**

```bash
# Set credentials as environment variables
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=your-pypi-token-here

# Twine will automatically use these
twine upload dist/*
```

**Option 2: Using .pypirc file**

Create `.pypirc` in the project root (for multiple profiles):

```ini
[distutils]
index-servers =
  pypi
  testpypi

[pypi]
  repository = https://upload.pypi.org/legacy/
  username = __token__
  password = <paste-your-token-here>

[testpypi]
  repository = https://test.pypi.org/legacy/
  username = __token__
  password = <paste-your-token-here>
```

**Important:** Never commit `.pypirc` to version control (it's already in `.gitignore`).

**Option 3: Pass credentials directly**

```bash
twine upload dist/* -u __token__ -p "${PYPI_TOKEN}"
```

### Manual Deployment Steps

#### 1. Prepare the Release

1. **Fetch the latest develop branch:**

   ```bash
   git fetch origin develop
   git checkout develop
   git pull origin develop
   ```

2. **Update the version number:**
   - Edit `data_spec_validator/__version__.py`
   - Update the version following [Semantic Versioning](https://semver.org/):
     - MAJOR version for incompatible API changes
     - MINOR version for backwards-compatible functionality additions
     - PATCH version for backwards-compatible bug fixes

3. **Update the CHANGELOG:**
   - Edit `CHANGELOG.md`
   - Add a new section at the top with the new version number
   - Document all changes since the last release:
     - `[feature]` for new features
     - `[fix]` for bug fixes
     - `[improvement]` for enhancements
     - `[behavior-change]` for breaking changes
     - `[internal]` for internal refactoring

4. **Commit the version bump:**

   ```bash
   git add data_spec_validator/__version__.py CHANGELOG.md
   git commit -m "bump version to X.Y.Z"
   git push origin develop
   ```

#### 2. Build and Deploy

**Install build tools:**

```bash
pip install build twine
```

**Build the package:**

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build source distribution and wheel
python -m build
```

**Upload to Test PyPI (for testing):**

```bash
twine upload --repository testpypi dist/*
# Or use a specific profile from .pypirc:
twine upload --config-file .pypirc -r testdsv dist/*
```

**Upload to Production PyPI:**

```bash
twine upload dist/*
# Or use a specific profile from .pypirc:
twine upload --config-file .pypirc -r pypi dist/*
```

**Verify the upload:**

```bash
# For Test PyPI
pip install --index-url https://test.pypi.org/simple/ --no-deps data-spec-validator

# For Production PyPI
pip install --upgrade data-spec-validator
python -c "from data_spec_validator.__version__ import __version__; print(__version__)"
```

#### 3. Post-Deployment

1. **Create a Git tag:**

   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

2. **Create a GitHub Release:**
   - Go to <https://github.com/hardcoretech/data-spec-validator/releases/new>
   - Select the tag you just created
   - Copy the changelog entry for this version
   - Publish the release

## Configuration Files

- **setup.py**: Package metadata and dependencies
- **pyproject.toml**: Build system requirements (Black configuration)
- **setup.cfg**: Flake8 and isort configuration
- **.pypirc**: PyPI credentials (NOT committed to git)
- **data_spec_validator/__version__.py**: Current version number

## Troubleshooting

### "Package already exists" error

- This means the version number is already uploaded to PyPI
- Increment the version number and try again
- PyPI does not allow re-uploading the same version

### Authentication errors

- Verify `.pypirc` credentials are correct
- Ensure you have maintainer permissions for the package
- Generate a new API token from <https://pypi.org/manage/account/token/>

### Test PyPI 403 Forbidden error

- Test PyPI and production PyPI use separate accounts and API tokens
- The version may already exist on Test PyPI (each version can only be uploaded once)
- If testing is needed, increment to a dev version (e.g., `3.5.2.dev1`) for Test PyPI
- Alternatively, skip Test PyPI and deploy directly to production if you're confident in the release

### Missing twine error

- Install twine: `pip install twine`
- Ensure twine is available in your PATH

### Build errors

- Ensure all dependencies are installed: `pip install -r requirements-dev.txt`
- Check that `setup.py` is valid: `python setup.py check`

## Quick Reference

### Automated Deployment via GitHub Actions (Recommended)

#### Automatic on Release

```bash
# 1. Update version and changelog
git checkout develop
git pull origin develop

# Edit data_spec_validator/__version__.py
# Edit CHANGELOG.md

git add data_spec_validator/__version__.py CHANGELOG.md
git commit -m "bump version to X.Y.Z"
git push origin develop

# 2. Create GitHub release
# Go to: https://github.com/hardcoretech/data-spec-validator/releases/new
# Tag: vX.Y.Z
# Title: vX.Y.Z
# Description: Copy changelog entry
# Click "Publish release"
#
# GitHub Actions will automatically publish to PyPI
```

#### Manual Trigger (Test or Production)

```bash
# 1. Update version and changelog (same as above)
git checkout develop
git pull origin develop

# Edit data_spec_validator/__version__.py
# Edit CHANGELOG.md

git add data_spec_validator/__version__.py CHANGELOG.md
git commit -m "bump version to X.Y.Z"
git push origin develop

# 2. Manually trigger GitHub Action
# Go to: https://github.com/hardcoretech/data-spec-validator/actions/workflows/publish.yml
# Click "Run workflow"
# Select branch: develop
# Select environment: testpypi or pypi
# Click "Run workflow"
#
# Monitor at: https://github.com/hardcoretech/data-spec-validator/actions
```

### Manual Deployment

```bash
# 1. Update version and changelog
git checkout develop
git pull origin develop

# Edit data_spec_validator/__version__.py
# Edit CHANGELOG.md

git add data_spec_validator/__version__.py CHANGELOG.md
git commit -m "bump version to X.Y.Z"
git push origin develop

# 2. Build and deploy
pip install build twine
rm -rf dist/ build/ *.egg-info
python -m build
twine upload dist/*

# 3. Tag the release
git tag vX.Y.Z
git push origin vX.Y.Z

# 4. Create GitHub release at:
# https://github.com/hardcoretech/data-spec-validator/releases/new
```
