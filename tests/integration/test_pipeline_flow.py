"""Integration tests for GitLab pipeline flow."""

import pytest
import responses

from gitlab_client import GitLabClient
from models import (
    PipelineHistory,
    PipelineInfo,
    PipelineTestCounts,
    TestSummary,
    add_test_summary_to_pipeline,
    add_version_and_url_to_pipeline,
    parse_pipelines,
    parse_pipeline_info,
    parse_ref_with_regex,
    parse_test_summary,
)


# GitLab API Response Examples from documentation

GITLAB_PIPELINE_RESPONSE = {
    "id": 287,
    "iid": 144,
    "project_id": 21,
    "name": "Build pipeline",
    "sha": "50f0acb76a40e34a4ff304f7347dcc6587da8a14",
    "ref": "my-app - v1.2.3",
    "status": "success",
    "source": "push",
    "web_url": "https://gitlab.example.com/mygroup/myproject/-/pipelines/287",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "duration": 300,
}

GITLAB_PIPELINES_LIST_RESPONSE = [
    {
        "id": 287,
        "status": "success",
        "ref": "my-app - v1.2.3",
        "name": "Build pipeline",
        "web_url": "https://gitlab.example.com/mygroup/myproject/-/pipelines/287",
        "created_at": "2024-01-15T10:00:00Z",
        "duration": 300,
    },
    {
        "id": 286,
        "status": "failed",
        "ref": "my-app - v1.2.2",
        "name": "Build pipeline",
        "web_url": "https://gitlab.example.com/mygroup/myproject/-/pipelines/286",
        "created_at": "2024-01-14T10:00:00Z",
        "duration": 280,
    },
    {
        "id": 285,
        "status": "success",
        "ref": "other-app - v2.0.0",
        "name": "Build pipeline",
        "web_url": "https://gitlab.example.com/mygroup/myproject/-/pipelines/285",
        "created_at": "2024-01-13T10:00:00Z",
        "duration": 250,
    },
    {
        "id": 284,
        "status": "success",
        "ref": "my-app - v1.2.1",
        "name": "Build pipeline",
        "web_url": "https://gitlab.example.com/mygroup/myproject/-/pipelines/284",
        "created_at": "2024-01-12T10:00:00Z",
        "duration": 270,
    },
]

GITLAB_TEST_REPORT_SUMMARY_RESPONSE = {
    "total": {
        "count": 150,
        "success": 148,
        "failed": 2,
        "skipped": 0,
        "error": 0,
        "time": 320,
    }
}

DEFAULT_REGEX = r"^(?P<name>[^ ]+) - (?P<version>.*)$"


class TestGitLabPipelineResponses:
    """Test parsing GitLab API responses with realistic data."""

    def test_parse_pipeline_info_from_api_response(self):
        """Test parsing pipeline info from GitLab API response."""
        result = parse_pipeline_info(GITLAB_PIPELINE_RESPONSE)

        assert isinstance(result, PipelineInfo)
        assert result.id == 287
        assert result.name == "Build pipeline"
        assert result.ref == "my-app - v1.2.3"
        assert result.status == "success"
        assert result.sha == "50f0acb76a40e34a4ff304f7347dcc6587da8a14"
        assert result.web_url == "https://gitlab.example.com/mygroup/myproject/-/pipelines/287"
        assert result.duration == 300
        assert result.created_at == "2024-01-15T10:00:00Z"
        assert result.updated_at == "2024-01-15T10:30:00Z"

    def test_parse_pipelines_list_from_api_response(self):
        """Test parsing pipelines list from GitLab API response."""
        result = parse_pipelines(GITLAB_PIPELINES_LIST_RESPONSE)

        assert len(result) == 4
        assert all(isinstance(p, PipelineHistory) for p in result)

        assert result[0].id == 287
        assert result[0].status == "success"
        assert result[0].ref == "my-app - v1.2.3"
        assert result[0].web_url == "https://gitlab.example.com/mygroup/myproject/-/pipelines/287"

        assert result[1].id == 286
        assert result[1].status == "failed"

        assert result[2].id == 285
        assert result[2].ref == "other-app - v2.0.0"

    def test_parse_test_summary_from_api_response(self):
        """Test parsing test summary from GitLab API response."""
        result = parse_test_summary(GITLAB_TEST_REPORT_SUMMARY_RESPONSE)

        assert isinstance(result, TestSummary)
        assert result.total_count == 150
        assert result.success_count == 148
        assert result.failed_count == 2
        assert result.skipped_count == 0
        assert result.error_count == 0
        assert result.total_time == 320


class TestParseRefWithRegex:
    """Test regex parsing for pipeline refs."""

    def test_parse_ref_with_default_regex(self):
        """Test parsing ref with default regex pattern."""
        ref = "my-app - v1.2.3"
        name, version, matched = parse_ref_with_regex(ref, DEFAULT_REGEX)

        assert matched is True
        assert name == "my-app"
        assert version == "v1.2.3"

    def test_parse_ref_with_different_version(self):
        """Test parsing ref with different version format."""
        ref = "my-app - v2.0.0-beta"
        name, version, matched = parse_ref_with_regex(ref, DEFAULT_REGEX)

        assert matched is True
        assert name == "my-app"
        assert version == "v2.0.0-beta"

    def test_parse_ref_no_version(self):
        """Test parsing ref with hyphen but no version."""
        ref = "main-branch - "  # Matches pattern but version is empty
        name, version, matched = parse_ref_with_regex(ref, DEFAULT_REGEX)

        assert matched is True
        assert name == "main-branch"
        assert version == "N/A"

    def test_parse_ref_no_match(self):
        """Test parsing ref that doesn't match regex."""
        ref = "some-other-ref"
        name, version, matched = parse_ref_with_regex(ref, DEFAULT_REGEX)

        assert matched is False
        assert name == ""
        assert version == "N/A"

    def test_parse_ref_custom_regex(self):
        """Test parsing with custom regex pattern."""
        ref = "v1.2.3-my-app"
        regex = r"^(?P<version>v[\d.]+)-(?P<name>.*)$"

        name, version, matched = parse_ref_with_regex(ref, regex)

        assert matched is True
        assert name == "my-app"
        assert version == "v1.2.3"

    def test_parse_ref_regex_without_version_group(self):
        """Test regex without version group uses N/A."""
        ref = "my-app"  # No hyphen, just name
        regex = r"^(?P<name>[^ ]+)$"

        name, version, matched = parse_ref_with_regex(ref, regex)

        assert matched is True
        assert name == "my-app"
        assert version == "N/A"


class TestPipelineEnrichment:
    """Test pipeline enrichment with test counts and version."""

    def test_add_test_summary_to_pipeline(self):
        """Test adding test summary to pipeline history."""
        pipeline = PipelineHistory(
            id=287,
            status="success",
            ref="my-app - v1.2.3",
        )
        test_summary = TestSummary(
            total_count=150,
            success_count=148,
            failed_count=2,
            skipped_count=0,
        )

        result = add_test_summary_to_pipeline(pipeline, test_summary)

        assert result.id == 287
        assert result.status == "success"
        assert result.total_count == 150
        assert result.success_count == 148
        assert result.failed_count == 2

    def test_add_version_and_url_to_pipeline(self):
        """Test adding version and URL to pipeline."""
        pipeline = PipelineHistory(
            id=287,
            status="success",
            ref="my-app - v1.2.3",
            test_counts=PipelineTestCounts(total_count=150),
        )

        result = add_version_and_url_to_pipeline(
            pipeline, "v1.2.3", "https://gitlab.com/pipelines/287"
        )

        assert result.version == "v1.2.3"
        assert result.url == "https://gitlab.com/pipelines/287"
        assert result.total_count == 150


class TestPipelineFiltering:
    """Test pipeline filtering by name."""

    def test_filter_pipelines_by_name(self):
        """Test filtering pipelines to match same name."""
        pipelines_data = GITLAB_PIPELINES_LIST_RESPONSE
        pipelines = parse_pipelines(pipelines_data)
        target_name = "my-app"

        filtered = [p for p in pipelines if parse_ref_with_regex(p.ref, DEFAULT_REGEX)[0] == target_name]

        assert len(filtered) == 3
        assert all(parse_ref_with_regex(p.ref, DEFAULT_REGEX)[0] == target_name for p in filtered)

    def test_filter_excludes_non_matching_names(self):
        """Test that non-matching pipeline names are excluded."""
        pipelines_data = GITLAB_PIPELINES_LIST_RESPONSE
        pipelines = parse_pipelines(pipelines_data)
        target_name = "my-app"

        filtered = [p for p in pipelines if parse_ref_with_regex(p.ref, DEFAULT_REGEX)[0] == target_name]

        ref_names = [parse_ref_with_regex(p.ref, DEFAULT_REGEX)[0] for p in filtered]
        assert "other-app" not in ref_names


@responses.activate
class TestGitLabAPIMocking:
    """Integration tests with mocked GitLab API responses."""

    def test_get_pipeline_from_api(self):
        """Test fetching pipeline from mocked GitLab API."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects/21/pipelines/287",
            json=GITLAB_PIPELINE_RESPONSE,
            status=200,
        )

        client = GitLabClient(url="https://gitlab.example.com", token="test_token")
        result = client.get_pipeline("21", 287)

        assert result["id"] == 287
        assert result["ref"] == "my-app - v1.2.3"
        assert result["status"] == "success"

    def test_get_pipelines_list_from_api(self):
        """Test fetching pipelines list from mocked GitLab API."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects/21/pipelines",
            json=GITLAB_PIPELINES_LIST_RESPONSE,
            status=200,
        )

        client = GitLabClient(url="https://gitlab.example.com", token="test_token")
        result = client.get_pipelines("21", per_page=10)

        assert len(result) == 4
        assert result[0]["id"] == 287

    def test_get_test_report_summary_from_api(self):
        """Test fetching test report summary from mocked GitLab API."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects/21/pipelines/287/test_report_summary",
            json=GITLAB_TEST_REPORT_SUMMARY_RESPONSE,
            status=200,
        )

        client = GitLabClient(url="https://gitlab.example.com", token="test_token")
        result = client.get_pipeline_test_report_summary("21", 287)

        assert result["total"]["count"] == 150
        assert result["total"]["success"] == 148
        assert result["total"]["failed"] == 2

    def test_full_pipeline_flow_with_mocks(self):
        """Test complete pipeline flow with mocked API responses."""
        # Mock pipeline details
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects/21/pipelines/287",
            json=GITLAB_PIPELINE_RESPONSE,
            status=200,
        )

        # Mock pipelines list
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects/21/pipelines",
            json=GITLAB_PIPELINES_LIST_RESPONSE,
            status=200,
        )

        # Mock test report summary
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects/21/pipelines/287/test_report_summary",
            json=GITLAB_TEST_REPORT_SUMMARY_RESPONSE,
            status=200,
        )

        client = GitLabClient(url="https://gitlab.example.com", token="test_token")

        # Fetch pipeline
        pipeline = client.get_pipeline("21", 287)
        pipeline_info = parse_pipeline_info(pipeline)

        # Parse ref with regex
        name, version, matched = parse_ref_with_regex(pipeline.ref, DEFAULT_REGEX)
        assert matched is True
        assert name == "my-app"
        assert version == "v1.2.3"

        # Fetch pipelines list
        pipelines_data = client.get_pipelines("21", per_page=10)
        pipelines = parse_pipelines(pipelines_data)

        # Filter by name
        filtered = [p for p in pipelines if parse_ref_with_regex(p.ref, DEFAULT_REGEX)[0] == name]
        assert len(filtered) == 3

        # Fetch test summary for main pipeline
        test_report = client.get_pipeline_test_report_summary("21", 287)
        test_summary = parse_test_summary(test_report)

        assert test_summary.total_count == 150
        assert test_summary.success_count == 148
        assert test_summary.failed_count == 2
