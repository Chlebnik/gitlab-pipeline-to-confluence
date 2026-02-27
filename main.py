"""Main entry point for GitLab Pipeline to Confluence synchronization.

This script fetches pipeline test results from GitLab and updates a Confluence
page with the latest statistics, test results, and pipeline history visualization.

Configuration priority (highest to lowest):
    1. Command line arguments
    2. Config file (YAML)
    3. Environment variables
    4. Default values
"""

import argparse
import sys
from pathlib import Path

import yaml

import config
from confluence_client import ConfluenceClient
from generator import find_and_replace_section, generate_pipeline_section
from gitlab_client import GitLabClient
from models import (
    PipelineHistory,
    PipelineInfo,
    TestSummary,
    parse_pipeline_info,
    parse_pipelines,
    parse_test_summary,
)


DEFAULT_CONFIG_TEMPLATE = {
    "gitlab": {
        "url": "https://gitlab.example.com",
        "token": "changeme",
    },
    "confluence": {
        "url": "https://confluence.example.com",
        "email": "changeme",
        "token": "changeme",
    },
    "options": {
        "history_count": 10,
    },
}


def save_default_config(output_path: str) -> None:
    """Save the default configuration template to a file.

    Args:
        output_path: Path where the config file should be saved
    """
    path = Path(output_path)
    if path.exists():
        print(f"Error: File already exists: {output_path}", file=sys.stderr)
        sys.exit(1)

    with open(path, "w", encoding="utf-8") as file:
        yaml.dump(DEFAULT_CONFIG_TEMPLATE, file, default_flow_style=False, sort_keys=False)

    print(f"Configuration template saved to: {output_path}")
    print("Please update the values in the config file before running the script.")


# pylint: disable=too-many-locals,too-many-statements
def main():
    """Main function to fetch GitLab pipeline data and update Confluence page.

    This function:
    1. Parses command line arguments
    2. Loads configuration from file (if specified)
    3. Fetches pipeline information from GitLab
    4. Fetches test report summary
    5. Fetches recent pipeline history
    6. Generates HTML content for the pipeline section
    7. Updates the Confluence page with the new content

    The script requires GitLab private token and Confluence API token to be
    configured via config file, environment variables, or command line arguments.
    """
    arg_parser = argparse.ArgumentParser(
        description="Parse GitLab pipeline test results and update Confluence page",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration priority (highest to lowest):
  1. Command line arguments
  2. Config file (YAML)
  3. Environment variables
  4. Default values

Examples:
  # Run with config file
  python main.py -p 123 --project-id 456 --confluence-page-id 789 --config config.yaml

  # Generate default config file
  python main.py --save-config config.yaml
        """,
    )

    arg_parser.add_argument(
        "--pipeline-id",
        "-p",
        type=int,
        help="GitLab pipeline ID (required)",
    )
    arg_parser.add_argument(
        "--project-id",
        help="GitLab project ID (numeric or URL-encoded path) (required)",
    )
    arg_parser.add_argument(
        "--confluence-page-id",
        help="Confluence page ID to update (required)",
    )
    arg_parser.add_argument(
        "--config",
        "-c",
        help="Path to YAML configuration file",
    )
    arg_parser.add_argument(
        "--save-config",
        help="Save default configuration template to specified file and exit",
    )
    arg_parser.add_argument(
        "--gitlab-url",
        help="GitLab URL (default: from config or env)",
    )
    arg_parser.add_argument(
        "--confluence-url",
        help="Confluence URL (default: from config or env)",
    )
    arg_parser.add_argument(
        "--gitlab-token",
        help="GitLab private token (default: from config or env)",
    )
    arg_parser.add_argument(
        "--confluence-email",
        help="Confluence email (default: from config or env)",
    )
    arg_parser.add_argument(
        "--confluence-token",
        help="Confluence API token (default: from config or env)",
    )
    arg_parser.add_argument(
        "--history-count",
        type=int,
        help="Number of recent pipelines to show in history (default: from config or 10)",
    )

    args = arg_parser.parse_args()

    if args.save_config:
        save_default_config(args.save_config)
        return

    if not args.pipeline_id:
        arg_parser.error("--pipeline-id is required")
    if not args.project_id:
        arg_parser.error("--project-id is required")
    if not args.confluence_page_id:
        arg_parser.error("--confluence-page-id is required")

    file_config = {}
    if args.config:
        try:
            file_config = config.load_config_file(args.config)
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        except yaml.YAMLError as exc:
            print(f"Error: Invalid YAML in config file: {exc}", file=sys.stderr)
            sys.exit(1)

    gitlab_url = args.gitlab_url or config.get_gitlab_url(file_config)
    gitlab_token = args.gitlab_token or config.get_gitlab_token(file_config)
    confluence_url = args.confluence_url or config.get_confluence_url(file_config)
    confluence_email = args.confluence_email or config.get_confluence_email(file_config)
    confluence_token = args.confluence_token or config.get_confluence_token(file_config)
    history_count = args.history_count or config.get_history_count(file_config)

    gitlab = GitLabClient(url=gitlab_url, token=gitlab_token)
    confluence = ConfluenceClient(
        url=confluence_url,
        email=confluence_email,
        token=confluence_token,
    )

    print(f"Fetching pipeline {args.pipeline_id} from project {args.project_id}...")

    pipeline = gitlab.get_pipeline(args.project_id, args.pipeline_id)
    pipeline_info: PipelineInfo = parse_pipeline_info(pipeline)
    pipeline_name = pipeline_info.name

    print(f"Pipeline name: {pipeline_name}")
    print(f"Status: {pipeline_info.status}")

    try:
        test_report = gitlab.get_pipeline_test_report_summary(
            args.project_id, args.pipeline_id
        )
        test_summary: TestSummary = parse_test_summary(test_report)
        print(
            f"Tests - Total: {test_summary.total_count}, "
            f"Passed: {test_summary.success_count}, "
            f"Failed: {test_summary.failed_count}"
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"Warning: Could not fetch test summary: {exc}")
        test_summary = TestSummary()

    print(f"Fetching recent {history_count} pipelines for history...")
    pipelines_data = gitlab.get_pipelines(
        args.project_id, per_page=history_count
    )
    recent_pipelines: list[PipelineHistory] = parse_pipelines(pipelines_data)

    section_content = generate_pipeline_section(
        pipeline_name, pipeline_info, test_summary, recent_pipelines
    )

    print(f"Fetching Confluence page {args.confluence_page_id}...")
    page = confluence.get_page(args.confluence_page_id)
    current_content = page["body"]["storage"]["value"]
    current_version = page["version"]["number"]
    page_title = page["title"]

    new_content = find_and_replace_section(
        current_content, pipeline_name, section_content
    )

    if new_content == current_content:
        print(f"Warning: Section for '{pipeline_name}' not found in page. Appending...")
        new_content = current_content + section_content

    print("Updating Confluence page...")
    confluence.update_page(
        args.confluence_page_id, page_title, new_content, current_version
    )

    print("Successfully updated Confluence page!")


if __name__ == "__main__":
    main()
