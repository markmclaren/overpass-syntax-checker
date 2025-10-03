# Deployment Guide

This project uses GitHub Actions for automated deployment to PyPI repositories.

## Manual Deployment Workflow

The deployment workflow is designed to be triggered manually and can deploy to either:

- **Test PyPI** (<https://test.pypi.org/>) - for testing releases
- **Production PyPI** (<https://pypi.org/>) - for official releases

### Prerequisites

Before using the deployment workflow, you need to set up the following GitHub repository secrets:

1. **TEST_PYPI_API_TOKEN** - API token for test.pypi.org
2. **PYPI_API_TOKEN** - API token for pypi.org (for production releases)

#### Setting up PyPI API Tokens

1. **For Test PyPI:**

   - Go to <https://test.pypi.org/manage/account/>
   - Navigate to "API tokens" section
   - Generate a new token with scope for the entire account or specific project
   - Copy the token (starts with `pypi-`)

2. **For Production PyPI:**

   - Go to <https://pypi.org/manage/account/>
   - Navigate to "API tokens" section
   - Generate a new token with scope for the entire account or specific project
   - Copy the token (starts with `pypi-`)

3. **Add secrets to GitHub:**
   - Go to your repository on GitHub
   - Navigate to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add `TEST_PYPI_API_TOKEN` with your test PyPI token
   - Add `PYPI_API_TOKEN` with your production PyPI token

### Running the Deployment

1. **Navigate to Actions tab** in your GitHub repository
2. **Select "Deploy to PyPI"** workflow from the left sidebar
3. **Click "Run workflow"** button
4. **Choose parameters:**
   - **Environment**: Select `test` for Test PyPI or `production` for Production PyPI
   - **Version bump**: Select version bump type if needed (currently not implemented, for future use)
5. **Click "Run workflow"** to start the deployment

### What the Workflow Does

The deployment workflow performs the following steps:

1. **Environment Setup**

   - Checks out the code
   - Sets up Python 3.10
   - Installs build dependencies (`build`, `twine`)

2. **Quality Assurance**

   - Installs package in development mode
   - Runs full test suite
   - Performs code quality checks (Black, isort, flake8)

3. **Package Building**

   - Builds source distribution and wheel
   - Validates the built packages with `twine check`

4. **Deployment**

   - Deploys to Test PyPI if `test` environment selected
   - Deploys to Production PyPI if `production` environment selected

5. **Release Management** (Production only)

   - Creates a GitHub release with version tag
   - Attaches built distribution files to the release

6. **Artifact Storage**
   - Uploads build artifacts for 30 days

### Testing a Release

After deploying to Test PyPI, you can test the installation:

```bash
# Install from Test PyPI
pip install -i https://test.pypi.org/simple/ overpass-ql-checker

# Test the installation
overpass-ql-check "node[amenity=restaurant];out;"
```

### Version Management

The current version is specified in `pyproject.toml`. Before deploying:

1. Update the version in `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Commit and push changes
4. Run the deployment workflow

### Troubleshooting

**Common Issues:**

1. **"Token not found" error**

   - Ensure the appropriate secret (`TEST_PYPI_API_TOKEN` or `PYPI_API_TOKEN`) is set in repository settings

2. **"Package already exists" error**

   - The version already exists on PyPI
   - Update the version in `pyproject.toml` and try again

3. **Test failures during deployment**

   - The workflow runs tests before deployment
   - Fix any failing tests and try again

4. **Quality check failures**
   - Run local quality checks: `./quality.sh`
   - Fix formatting/linting issues and try again

### Security Notes

- API tokens are stored securely as GitHub secrets
- Tokens are only accessible to the deployment workflow
- Test PyPI and Production PyPI use separate tokens for security isolation
- The workflow uses trusted GitHub Actions from verified publishers

### Environment Configuration

The workflow uses GitHub Environments to provide additional security:

- `test` environment for Test PyPI deployments
- `production` environment for Production PyPI deployments

You can configure environment protection rules in repository settings to require manual approval for production deployments.

