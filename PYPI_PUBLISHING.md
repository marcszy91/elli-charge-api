# Publishing to PyPI

This guide explains how to publish the `elli-api-client` package to PyPI.

## Package Structure

```
elli-charge-api/
├── src/elli_api_client/     ← This becomes the PyPI package
│   ├── __init__.py
│   ├── client.py
│   ├── models.py
│   ├── config.py
│   ├── README.md            ← Package README (shown on PyPI)
│   └── CHANGELOG.md         ← Client-specific changelog
├── setup.py                 ← Package configuration
├── MANIFEST.in              ← Include additional files
└── .github/workflows/
    ├── pypi-publish.yml     ← Auto-publish on release
    └── release-client.yml   ← Client-specific releases
```

## Two Release Strategies

### Strategy 1: Automatic (Recommended)

**When client code changes:**
1. Make changes to `src/elli_api_client/`
2. Commit with conventional commits:
   ```bash
   git commit -m "feat(client): add refresh token support"
   ```
3. Push to `main`
4. Release Please creates a PR with version bump
5. Merge PR → GitHub Release created
6. GitHub Action publishes to PyPI automatically

### Strategy 2: Manual

**Publish specific version:**
1. Go to Actions → "Publish to PyPI"
2. Click "Run workflow"
3. Enter version (e.g., `0.2.0`)
4. Publishes to TestPyPI first (for testing)
5. If OK, create GitHub Release to publish to PyPI

## Version Management

### Two Independent Versions

**Client Package** (`elli-api-client`):
- Version: `0.1.0` → Only bumped when client changes
- Changelog: `src/elli_api_client/CHANGELOG.md`
- Tags: `client-v0.1.0`

**API Server** (full repo):
- Version: `0.1.0` → Bumped for any changes
- Changelog: `CHANGELOG.md`
- Tags: `v0.1.0`

### When to Bump Client Version

**MAJOR** (1.0.0):
- Breaking API changes
- Changed authentication method
- Removed public methods

**MINOR** (0.2.0):
- New features (e.g., new API endpoints)
- New optional parameters
- New models

**PATCH** (0.1.1):
- Bug fixes
- Documentation updates
- Internal refactoring

## Setup Requirements

### 1. PyPI Account
1. Create account at https://pypi.org
2. Enable 2FA
3. Create API token: Account Settings → API tokens
4. Save as GitHub Secret: `PYPI_API_TOKEN`

### 2. TestPyPI (Optional, for testing)
1. Create account at https://test.pypi.org
2. Create API token
3. Save as GitHub Secret: `TEST_PYPI_API_TOKEN`

### 3. GitHub Secrets
Add in repo settings → Secrets and variables → Actions:
- `PYPI_API_TOKEN` - For production releases
- `TEST_PYPI_API_TOKEN` - For testing (optional)

## Local Testing

### Build the package
```bash
pip install build twine
python -m build
```

This creates:
- `dist/elli_api_client-0.1.0-py3-none-any.whl`
- `dist/elli-api-client-0.1.0.tar.gz`

### Check the package
```bash
twine check dist/*
```

### Test install locally
```bash
pip install dist/elli_api_client-0.1.0-py3-none-any.whl
```

### Upload to TestPyPI
```bash
twine upload --repository testpypi dist/*
```

### Test install from TestPyPI
```bash
pip install --index-url https://test.pypi.org/simple/ elli-api-client
```

## Usage in Other Projects

After publishing to PyPI, use in any Python project:

```python
# Install
pip install elli-api-client

# Use
from elli_api_client import ElliAPIClient

client = ElliAPIClient()
token = client.login("email@example.com", "password")
stations = client.get_stations()
```

## Benefits

✅ **Single source of truth** - One codebase for all integrations
✅ **Version pinning** - Projects can specify exact versions
✅ **Easy updates** - `pip install --upgrade elli-api-client`
✅ **Dependency management** - PyPI handles httpx, pydantic versions
✅ **Professional** - Proper Python package on PyPI
✅ **Testable** - Can test in isolation
✅ **Reusable** - Anyone can use the client

## Package URLs

After publishing:
- **PyPI**: https://pypi.org/project/elli-api-client/
- **TestPyPI**: https://test.pypi.org/project/elli-api-client/
- **Docs**: https://github.com/yourusername/elli-charge-api

## Troubleshooting

### "Package already exists"
- Increase version number in `setup.py` and `__init__.py`
- Can't replace existing versions on PyPI

### "Invalid credentials"
- Check GitHub secrets are set correctly
- Regenerate API token if needed

### "Import fails in HA"
- Check `requirements` in manifest.json
- Verify package name: `elli-api-client` (with dash)
- Import name: `elli_api_client` (with underscore)

## Example Workflow

1. **Change client code**
   ```bash
   git checkout -b feat/add-refresh-token
   # Make changes to src/elli_api_client/
   git commit -m "feat(client): add automatic token refresh"
   git push origin feat/add-refresh-token
   ```

2. **Create PR to main**
   - CI runs (linting, formatting)
   - Merge to main

3. **Release Please creates release PR**
   - Updates version to 0.2.0
   - Updates CHANGELOG
   - Merge this PR

4. **GitHub creates release**
   - Tag: `client-v0.2.0`
   - GitHub Action publishes to PyPI

5. **Users update their projects**
   ```bash
   pip install --upgrade elli-api-client
   ```

Done! 🎉
