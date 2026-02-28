"""Unit tests for generator module."""

import pytest

from generator import (
    find_and_replace_section,
    format_duration,
    format_timestamp,
    generate_ascii_bar_chart,
    generate_pipeline_section,
    generate_status_badge,
)
from models import PipelineHistory, PipelineInfo, PipelineTestCounts, TestSummary


class TestGenerateStatusBadge:
    """Tests for generate_status_badge function."""

    def test_generate_status_badge_success(self):
        """Test generating status badge for success."""
        result = generate_status_badge("success")

        assert "status-success.svg" in result

    def test_generate_status_badge_failed(self):
        """Test generating status badge for failed."""
        result = generate_status_badge("failed")

        assert "status-failed.svg" in result

    def test_generate_status_badge_case_insensitive(self):
        """Test that status is lowercased."""
        result = generate_status_badge("SUCCESS")

        assert "status-success.svg" in result


class TestGenerateAsciiBarChart:
    """Tests for generate_ascii_bar_chart function."""

    def test_generate_ascii_bar_chart_empty(self):
        """Test bar chart with empty data."""
        result = generate_ascii_bar_chart([])

        assert result == "No data available"

    def test_generate_ascii_bar_chart_single(self):
        """Test bar chart with single pipeline."""
        pipelines = [
            PipelineHistory(
                id=1, status="success", ref="main",
                test_counts=PipelineTestCounts(total_count=100)
            )
        ]

        result = generate_ascii_bar_chart(pipelines)

        assert "success" in result
        assert "100" in result

    def test_generate_ascii_bar_chart_multiple(self):
        """Test bar chart with multiple pipelines."""
        pipelines = [
            PipelineHistory(
                id=i, status="success", ref="main",
                test_counts=PipelineTestCounts(total_count=100 - i * 10)
            )
            for i in range(5)
        ]

        result = generate_ascii_bar_chart(pipelines)

        lines = result.split("\n")
        assert len(lines) == 5

    def test_generate_ascii_bar_chart_with_failed_status(self):
        """Test bar chart with failed pipelines."""
        pipelines = [
            PipelineHistory(
                id=1, status="failed", ref="main",
                test_counts=PipelineTestCounts(total_count=50)
            ),
            PipelineHistory(
                id=2, status="success", ref="main",
                test_counts=PipelineTestCounts(total_count=100)
            ),
        ]

        result = generate_ascii_bar_chart(pipelines)

        assert "✗" in result
        assert "✓" in result


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_format_duration_none(self):
        """Test formatting None duration."""
        result = format_duration(None)

        assert result == "N/A"

    def test_format_duration_seconds_only(self):
        """Test formatting seconds only."""
        result = format_duration(45)

        assert result == "45s"

    def test_format_duration_minutes_and_seconds(self):
        """Test formatting minutes and seconds."""
        result = format_duration(150)

        assert result == "2m 30s"

    def test_format_duration_large_value(self):
        """Test formatting large duration."""
        result = format_duration(3661)

        assert result == "61m 1s"

    def test_format_duration_zero(self):
        """Test formatting zero duration."""
        result = format_duration(0)

        assert result == "0s"


class TestFormatTimestamp:
    """Tests for format_timestamp function."""

    def test_format_timestamp_valid(self):
        """Test formatting valid timestamp."""
        result = format_timestamp("2024-01-15T10:30:00Z")

        assert result == "2024-01-15 10:30"

    def test_format_timestamp_with_timezone(self):
        """Test formatting timestamp with timezone."""
        result = format_timestamp("2024-01-15T10:30:00+05:00")

        assert "2024-01-15" in result

    def test_format_timestamp_invalid(self):
        """Test formatting invalid timestamp."""
        result = format_timestamp("not-a-timestamp")

        assert result == "not-a-timestamp"

    def test_format_timestamp_empty(self):
        """Test formatting empty timestamp."""
        result = format_timestamp("")

        assert result == "N/A"

    def test_format_timestamp_none(self):
        """Test formatting None timestamp."""
        result = format_timestamp(None)

        assert result == "N/A"


class TestGeneratePipelineSection:
    """Tests for generate_pipeline_section function."""

    def test_generate_pipeline_section(self):
        """Test generating pipeline section."""
        pipeline_info = PipelineInfo(
            id=123,
            name="test-pipeline",
            status="success",
            ref="main",
            sha="abc123",
            web_url="https://gitlab.com/pipelines/123",
        )
        test_summary = TestSummary(
            total_count=100,
            success_count=98,
            failed_count=2,
            skipped_count=0,
            error_count=0,
            total_time=300,
        )
        recent_pipelines = [
            PipelineHistory(
                id=i, status="success", ref="main", version='v1.0.0', url=f'https://gitlab.com/pipelines/{i}',
                test_counts=PipelineTestCounts(total_count=100 - i * 10)
            )
            for i in range(5)
        ]

        result = generate_pipeline_section(
            "test-pipeline", "v1.0.0", pipeline_info, test_summary, recent_pipelines
        )

        assert "<h2>test-pipeline</h2>" in result
        assert "123" in result
        assert "success" in result
        assert "100" in result
        assert "98" in result
        assert "2" in result
        assert "<h3>Test Results</h3>" in result
        assert "<h3>Pipeline History" in result


class TestFindAndReplaceSection:
    """Tests for find_and_replace_section function."""

    def test_find_and_replace_section_exists(self):
        """Test replacing existing section."""
        content = """
<h1>Page Title</h1>
<h2>my-pipeline</h2>
Old content here
<h2>another-pipeline</h2>
More content
"""
        new_section = "<h2>my-pipeline</h2>\nNew content"

        result = find_and_replace_section(content, "my-pipeline", new_section)

        assert "New content" in result
        assert "Old content here" not in result

    def test_find_and_replace_section_not_exists(self):
        """Test appending when section doesn't exist."""
        content = "<h1>Page Title</h1>\n<p>Some content</p>"
        new_section = "<h2>new-pipeline</h2>\nNew content"

        result = find_and_replace_section(content, "new-pipeline", new_section)

        assert result.endswith(new_section)

    def test_find_and_replace_section_first(self):
        """Test replacing first section."""
        content = "<h2>first-pipeline</h2>\nFirst content<h2>second</h2>\nSecond"
        new_section = "<h2>first-pipeline</h2>\nUpdated first"

        result = find_and_replace_section(content, "first-pipeline", new_section)

        assert "Updated first" in result
        assert "First content" not in result
        assert "second" in result

    def test_find_and_replace_case_insensitive(self):
        """Test case insensitive matching."""
        content = "<h2>My-Pipeline</h2>\nOld content"
        new_section = "<h2>My-Pipeline</h2>\nNew content"

        result = find_and_replace_section(content, "my-pipeline", new_section)

        assert "New content" in result
