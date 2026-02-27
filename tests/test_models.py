"""Unit tests for models module."""

import pytest

from models import (
    PipelineHistory,
    PipelineInfo,
    PipelineMetadata,
    TestSummary,
    parse_pipeline_info,
    parse_pipelines,
    parse_test_summary,
)


class TestPipelineInfo:
    """Tests for PipelineInfo dataclass."""

    def test_parse_pipeline_info_with_valid_data(self):
        """Test parsing pipeline info with all fields."""
        pipeline = {
            "id": 123,
            "name": "main",
            "status": "success",
            "ref": "main",
            "sha": "abc123",
            "web_url": "https://gitlab.com/project/-/pipelines/123",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "duration": 300,
        }

        result = parse_pipeline_info(pipeline)

        assert isinstance(result, PipelineInfo)
        assert result.id == 123
        assert result.name == "main"
        assert result.status == "success"
        assert result.ref == "main"
        assert result.sha == "abc123"
        assert result.web_url == "https://gitlab.com/project/-/pipelines/123"
        assert result.created_at == "2024-01-15T10:00:00Z"
        assert result.updated_at == "2024-01-15T10:30:00Z"
        assert result.duration == 300

    def test_parse_pipeline_info_with_missing_fields(self):
        """Test parsing pipeline info with missing fields."""
        pipeline = {"id": 456, "name": "test-pipeline"}

        result = parse_pipeline_info(pipeline)

        assert result.id == 456
        assert result.name == "test-pipeline"
        assert result.status == ""
        assert result.ref == ""
        assert result.sha == ""
        assert result.web_url == ""
        assert result.created_at is None
        assert result.updated_at is None
        assert result.duration is None

    def test_parse_pipeline_info_with_empty_dict(self):
        """Test parsing pipeline info with empty dict."""
        result = parse_pipeline_info({})

        assert result.id == 0
        assert result.name == "unknown"
        assert result.status == ""

    def test_pipeline_info_properties(self):
        """Test PipelineInfo property access."""
        pipeline = {
            "id": 1,
            "name": "test",
            "status": "running",
            "ref": "develop",
            "sha": "def456",
            "web_url": "https://gitlab.com/pipelines/1",
            "created_at": "2024-01-15T10:00:00Z",
            "duration": 120,
        }

        result = parse_pipeline_info(pipeline)

        assert result.created_at == "2024-01-15T10:00:00Z"
        assert result.duration == 120
        assert result.metadata.created_at == "2024-01-15T10:00:00Z"
        assert result.metadata.duration == 120


class TestSummaryData:
    """Tests for TestSummary dataclass."""

    def test_parse_test_summary_with_valid_data(self):
        """Test parsing test summary with all fields."""
        test_summary = {
            "total": {
                "count": 150,
                "success": 148,
                "failed": 2,
                "skipped": 0,
                "error": 0,
                "time": 300,
            }
        }

        result = parse_test_summary(test_summary)

        assert isinstance(result, TestSummary)
        assert result.total_count == 150
        assert result.success_count == 148
        assert result.failed_count == 2
        assert result.skipped_count == 0
        assert result.error_count == 0
        assert result.total_time == 300

    def test_parse_test_summary_with_empty_data(self):
        """Test parsing test summary with empty data."""
        test_summary = {}

        result = parse_test_summary(test_summary)

        assert result.total_count == 0
        assert result.success_count == 0
        assert result.failed_count == 0
        assert result.skipped_count == 0
        assert result.error_count == 0
        assert result.total_time == 0

    def test_parse_test_summary_with_partial_data(self):
        """Test parsing test summary with partial data."""
        test_summary = {"total": {"count": 100, "success": 95}}

        result = parse_test_summary(test_summary)

        assert result.total_count == 100
        assert result.success_count == 95
        assert result.failed_count == 0
        assert result.skipped_count == 0


class TestPipelineHistory:
    """Tests for PipelineHistory dataclass."""

    def test_parse_pipelines_with_multiple_items(self):
        """Test parsing multiple pipelines."""
        pipelines = [
            {
                "id": 100,
                "status": "success",
                "ref": "main",
                "created_at": "2024-01-15T10:00:00Z",
                "duration": 180,
                "web_url": "https://gitlab.com/pipelines/100",
            },
            {
                "id": 99,
                "status": "failed",
                "ref": "main",
                "created_at": "2024-01-14T10:00:00Z",
                "duration": 200,
                "web_url": "https://gitlab.com/pipelines/99",
            },
            {
                "id": 98,
                "status": "success",
                "ref": "develop",
                "created_at": "2024-01-13T10:00:00Z",
                "duration": 150,
                "web_url": "https://gitlab.com/pipelines/98",
            },
        ]

        result = parse_pipelines(pipelines)

        assert len(result) == 3
        assert all(isinstance(p, PipelineHistory) for p in result)

        assert result[0].id == 100
        assert result[0].status == "success"
        assert result[0].ref == "main"

        assert result[1].id == 99
        assert result[1].status == "failed"

        assert result[2].id == 98
        assert result[2].status == "success"

    def test_parse_pipelines_with_empty_list(self):
        """Test parsing empty pipeline list."""
        result = parse_pipelines([])

        assert result == []

    def test_parse_pipelines_with_missing_fields(self):
        """Test parsing pipelines with missing fields."""
        pipelines = [{"id": 1, "status": "running"}]

        result = parse_pipelines(pipelines)

        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].status == "running"
        assert result[0].ref == ""
        assert result[0].created_at is None
        assert result[0].duration is None
        assert result[0].web_url is None
