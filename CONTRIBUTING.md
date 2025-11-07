# Contributing to Elli Charging API

Thank you for considering contributing to this project!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/elli-charging-api.git
cd elli-charging-api
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

4. Install pre-commit hooks:
```bash
pre-commit install --hook-type commit-msg --hook-type pre-commit
```

## Code Quality

This project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **pytest**: Testing

Run all checks before committing:

```bash
# Format code
black .
isort .

# Lint
flake8 .

# Test
pytest
```

## Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/). All commit messages must follow this format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning (white-space, formatting)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvement
- **test**: Adding or updating tests
- **chore**: Changes to build process or auxiliary tools
- **ci**: Changes to CI configuration files and scripts

### Examples

```bash
feat: add endpoint for stopping charging session
fix: resolve authentication token expiration issue
docs: update API usage examples in README
refactor: simplify OAuth2 PKCE flow implementation
```

### Breaking Changes

For breaking changes, add `BREAKING CHANGE:` in the footer or add `!` after the type:

```bash
feat!: change authentication endpoint format

BREAKING CHANGE: The /login endpoint now returns a different response structure
```

## Pull Request Process

1. Create a feature branch from `dev`:
```bash
git checkout -b feat/your-feature-name dev
```

2. Make your changes and commit using conventional commits

3. Push your branch and create a Pull Request to `dev`

4. Ensure all CI checks pass

5. Wait for review and address any feedback

## Branch Strategy

- `main`: Production-ready code, protected branch
- `dev`: Development branch, merge your PRs here
- `feat/*`: Feature branches
- `fix/*`: Bug fix branches
- `docs/*`: Documentation branches

## Release Process

Releases are automated using Release Please:

1. Merge PRs to `dev` branch
2. When ready for release, create a PR from `dev` to `main`
3. Release Please will automatically create a release PR with changelog
4. Merge the release PR to trigger:
   - Version bump
   - Changelog update
   - GitHub release creation
   - Docker image build and push

## Testing

Write tests for all new features:

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.
```

## Questions?

Feel free to open an issue for any questions or discussions.
