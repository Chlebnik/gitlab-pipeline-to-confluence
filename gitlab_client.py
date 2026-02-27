"""GitLab API client for fetching pipeline and test data."""

from typing import Any, Optional

import requests

import config


class GitLabClient:
    """Client for interacting with GitLab REST API.

    This class provides methods to fetch pipeline information and test reports
    from a GitLab instance using the private token authentication.

    Attributes:
        url: Base URL of the GitLab instance
        token: Private token for authentication
    """

    def __init__(self, url: Optional[str] = None, token: Optional[str] = None):
        """Initialize the GitLab client.

        Args:
            url: Base URL of the GitLab instance (defaults to config value)
            token: Private token for authentication (defaults to config value)
        """
        self.url = url or config.GITLAB_URL
        self.token = token or config.GITLAB_TOKEN
        self.session = requests.Session()
        self.session.headers.update({"PRIVATE-TOKEN": self.token})

    def get_pipeline(self, project_id: str, pipeline_id: int) -> dict[str, Any]:
        """Get a single pipeline by ID.

        Args:
            project_id: The ID or URL-encoded path of the project
            pipeline_id: The ID of the pipeline

        Returns:
            Raw JSON response from GitLab API

        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{self.url}/api/v4/projects/{project_id}/pipelines/{pipeline_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_pipeline_test_report_summary(
        self, project_id: str, pipeline_id: int
    ) -> dict[str, Any]:
        """Get test report summary for a pipeline.

        Args:
            project_id: The ID or URL-encoded path of the project
            pipeline_id: The ID of the pipeline

        Returns:
            Raw JSON response containing test summary (total, success, failed, etc.)

        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{self.url}/api/v4/projects/{project_id}/pipelines/{pipeline_id}/test_report_summary"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_pipelines(
        self, project_id: str, per_page: int = 10, status: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Get list of pipelines for a project.

        Args:
            project_id: The ID or URL-encoded path of the project
            per_page: Number of pipelines to return per page (default: 10)
            status: Filter pipelines by status (e.g., 'success', 'failed')

        Returns:
            Raw JSON response containing list of pipelines

        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{self.url}/api/v4/projects/{project_id}/pipelines"
        params: dict[str, Any] = {"per_page": per_page}
        if status:
            params["status"] = status
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
