# GitLab Pipeline to Confluence

Python application that parses GitLab pipeline test results and updates a Confluence page with stats, graphs, and pipeline links.

## Overview

This script is typically run as part of a GitLab CI/CD pipeline or triggered via webhook after a pipeline completes. It fetches test results from GitLab and publishes them to a Confluence page for team visibility.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GitLab CI/CD Pipeline                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐               │
│   │  Build  │───▶│  Test   │───▶│ Deploy  │───▶│ Notify  │               │
│   └─────────┘    └─────────┘    └─────────┘    └────┬────┘               │
│                                                     │                     │
│                                                     ▼                     │
│                                            ┌────────────────┐             │
│                                            │  GitLab API    │             │
│                                            │  (Get Results) │             │
│                                            └────────┬───────┘             │
│                                                     │                     │
└─────────────────────────────────────────────────────┼─────────────────────┘
                                                      │
                                                      ▼
┌─────────────────────────────────────────────────────┼─────────────────────┐
│                    Run Pipeline to Confluence       │                     │
├─────────────────────────────────────────────────────┼─────────────────────┤
│                                                     │                     │
│   python main.py                                    │                     │
│     --pipeline-id $CI_PIPELINE_ID                   │                     │
│     --project-id $CI_PROJECT_ID                     │                     │
│     --confluence-page-id 12345                      │                     │
│                                                     │                     │
│   ┌────────────────┐    ┌────────────────┐         │                     │
│   │  GitLab API    │    │  Fetch Pipeline │         │                     │
│   │  Fetch Test    │◀───│  Info & History │         │                     │
│   │  Report Summary│    └────────┬────────┘         │                     │
│   └────────┬───────┘             │                  │                     │
│            │                     ▼                  │                     │
│            │            ┌────────────────┐          │                     │
│            └───────────▶│  Generate HTML │          │                     │
│                         │  (Table + Chart)│          │                     │
│                         └────────┬───────┘          │                     │
│                                  │                  │                     │
│                                  ▼                  │                     │
│                         ┌────────────────┐          │                     │
│                         │  Confluence API│          │                     │
│                         │  Update Page   │──────────┘                     │
│                         └────────────────┘                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Confluence Page Output                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Pipeline Results                                                     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                       │   │
│  │ my-pipeline                                                          │   │
│  │                                                                       │   │
│  │ Latest Pipeline Run: #12345 | Status: success | Duration: 2m 30s   │   │
│  │                                                                       │   │
│  │ Test Results                                                         │   │
│  │ ┌───────┬───────┬───────┬────────┬────────┬────────┐                │   │
│  │ │ Total │ Passed│ Failed│ Skipped│ Errors │  Time  │                │   │
│  │ ├───────┼───────┼───────┼────────┼────────┼────────┤                │   │
│  │ │  150  │  148  │   0   │   2    │   0    │ 5m 23s │                │   │
│  │ └───────┴───────┴───────┴────────┴────────┴────────┘                │   │
│  │                                                                       │   │
│  │ Pipeline History (Last 10 Runs)                                     │   │
│  │ ✓ success   │████████████████│ 148                                  │   │
│  │ ✓ success   │███████████████  │ 145                                  │   │
│  │ ✗ failed    │████████████     │ 142                                  │   │
│  │ ✓ success   │███████████████  │ 150                                  │   │
│  │ ...                                                            │   │
│  │                                                                       │   │
│  │ Last updated: 2024-01-15 14:30:45                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Features

- Fetches pipeline information from GitLab API
- Retrieves test report summary (total, passed, failed, skipped, errors)
- Shows recent pipeline history with ASCII bar chart
- Updates Confluence page by finding pipeline name section
- Configurable via environment variables or CLI arguments

## Requirements

- Python 3.10+
- GitLab account with API token
- Confluence account with API token

## Installation

```bash
cd gitlab-pipeline-to-confluence
pip install -r requirements.txt
```

## CI/CD Integration

This script is designed to be run at the end of a GitLab CI/CD pipeline or triggered via webhook after a pipeline completes.

### Option 1: Add as Final Pipeline Job

Add this job to your `.gitlab-ci.yml`:

```yaml
publish-to-confluence:
  stage: .post
  image: python:3.10-slim
  needs:
    - build
    - test
  script:
    - pip install -r requirements.txt
    - python main.py
      --pipeline-id $CI_PIPELINE_ID
      --project-id $CI_PROJECT_ID
      --confluence-page-id $CONFLUENCE_PAGE_ID
  only:
    - main
    - master
  when: on_success
```

### Option 2: Webhook Trigger

Configure a webhook in GitLab to trigger this script when a pipeline finishes:

```bash
# Example webhook handler (using GitLab webhook)
curl -X POST https://your-server.com/script \
  -d "payload=$(cat pipeline_event.json)"
```

### Required Environment Variables in CI

Set these as CI/CD variables in GitLab project settings, or use a config file:

| Variable | Description |
|----------|-------------|
| `GITLAB_TOKEN` | GitLab private token with `read_api` scope |
| `CONFLUENCE_EMAIL` | Confluence account email |
| `CONFLUENCE_TOKEN` | Confluence API token |
| `CONFLUENCE_PAGE_ID` | Target Confluence page ID |
| `GITLAB_URL` | Your GitLab instance URL |

**Tip**: For CI/CD, consider using a config file and passing it via `artifacts:expose_as` or storing it as a CI/CD variable.

## Configuration

The application supports multiple configuration methods with the following priority order:

1. **Command line arguments** (highest priority)
2. **Config file** (YAML)
3. **Environment variables**
4. **Default values** (lowest priority)

### Config File (Recommended)

Using a config file is recommended for production use as it keeps credentials separate from command line arguments.

#### Generate Default Config

```bash
python main.py --save-config config.yaml
```

This will create a template file. Edit it with your values:

```yaml
gitlab:
  url: https://gitlab.example.com
  token: your_gitlab_private_token

confluence:
  url: https://confluence.example.com
  email: your_email@example.com
  token: your_confluence_api_token

options:
  history_count: 10
```

#### Run with Config File

```bash
python main.py \
  --pipeline-id 123 \
  --project-id 456 \
  --confluence-page-id 789 \
  --config config.yaml
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env`:

```
GITLAB_TOKEN=your_gitlab_private_token
CONFLUENCE_EMAIL=your_email@example.com
CONFLUENCE_TOKEN=your_confluence_api_token
GITLAB_URL=https://gitlab.example.com
CONFLUENCE_URL=https://confluence.example.com
CONFLUENCE_PAGE_ID=12345
PROJECT_ID=your_project_id
```

### Getting GitLab Token

1. Go to GitLab → User Settings → Access Tokens
2. Create new token with `read_api` scope

### Getting Confluence Token

1. Go to Confluence → Profile → Atlassian account settings
2. Create API token under Security → API tokens

### Getting IDs

- **Project ID**: Found in GitLab project settings or use URL-encoded path (e.g., `mygroup/myproject`)
- **Pipeline ID**: Found in pipeline URL or CI/CD variables
- **Confluence Page ID**: Found in page URL (last part of `/spaces/.../pages/12345`)

## Usage

```bash
python main.py \
  --pipeline-id 123 \
  --project-id 456 \
  --confluence-page-id 789
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--pipeline-id`, `-p` | GitLab pipeline ID (required) | - |
| `--project-id` | GitLab project ID (required) | From env |
| `--confluence-page-id` | Confluence page ID (required) | From env |
| `--gitlab-url` | GitLab URL | From config |
| `--confluence-url` | Confluence URL | From config |
| `--gitlab-token` | GitLab private token | From env |
| `--confluence-email` | Confluence email | From env |
| `--confluence-token` | Confluence API token | From env |
| `--history-count` | Number of recent pipelines | 10 |

### Examples

```bash
# Basic usage
python main.py --pipeline-id 12345 --project-id 100 --confluence-page-id 500

# With custom URLs
python main.py -p 12345 --project-id 100 --confluence-page-id 500 \
  --gitlab-url https://gitlab.company.com \
  --confluence-url https://company.atlassian.net/wiki

# Override tokens via CLI
python main.py -p 12345 --project-id 100 --confluence-page-id 500 \
  --gitlab-token xxxx --confluence-email me@company.com --confluence-token xxxx
```

## Confluence Page Format

The script expects a Confluence page with sections marked by `<h2>` headers matching pipeline names:

```html
<h2>my-pipeline-name</h2>
... content to be updated ...
<h2>another-pipeline</h2>
```

If the pipeline section doesn't exist, it will be appended to the page.

## Output Example

The updated section contains:

- **Latest Pipeline Run**: Link to pipeline, status, duration
- **Test Results Table**: Total, Passed, Failed, Skipped, Errors, Time
- **Pipeline History**: ASCII bar chart showing last 10 runs
- **Last Updated**: Timestamp

## Project Structure

```
gitlab-pipeline-to-confluence/
├── config.py              # Configuration
├── gitlab_client.py      # GitLab API client
├── confluence_client.py  # Confluence API client
├── models.py             # Data models and parsers
├── generator.py          # HTML content generation
├── main.py               # CLI entry point
├── requirements.txt      # Dependencies
├── pytest.ini            # Pytest configuration
├── .env.example          # Environment template
└── tests/                # Unit tests
    ├── __init__.py
    ├── test_config.py
    ├── test_generator.py
    ├── test_gitlab_client.py
    ├── test_confluence_client.py
    └── test_models.py
```

## Testing

The project includes comprehensive unit tests using pytest.

### Run Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_models.py

# Run with coverage (if pytest-cov installed)
pytest --cov=. --cov-report=html
```

### Test Coverage

- **models.py**: Tests for parsing pipeline info, test summaries, and pipeline history
- **generator.py**: Tests for HTML generation, formatting, and section replacement
- **config.py**: Tests for config file loading and priority resolution
- **gitlab_client.py**: Tests for GitLab API client (with mocked HTTP)
- **confluence_client.py**: Tests for Confluence API client (with mocked HTTP)

## License

MIT
