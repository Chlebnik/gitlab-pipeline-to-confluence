"""Data models and parsers for GitLab pipeline and test data."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class PipelineMetadata:
    """Metadata for a GitLab pipeline including timestamps and duration."""

    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    duration: Optional[int] = None


@dataclass(frozen=True)
class PipelineInfo:
    """Information about a GitLab pipeline."""

    id: int
    name: str
    status: str
    ref: str
    sha: str
    web_url: str
    metadata: Optional[PipelineMetadata] = None

    def __post_init__(self):
        if self.metadata is None:
            object.__setattr__(self, 'metadata', PipelineMetadata())

    @property
    def created_at(self) -> Optional[str]:
        """Return the pipeline creation timestamp."""
        return self.metadata.created_at if self.metadata else None

    @property
    def updated_at(self) -> Optional[str]:
        """Return the pipeline last update timestamp."""
        return self.metadata.updated_at if self.metadata else None

    @property
    def duration(self) -> Optional[int]:
        """Return the pipeline duration in seconds."""
        return self.metadata.duration if self.metadata else None


@dataclass(frozen=True)
class TestSummary:
    """Summary of test results for a pipeline."""

    total_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    total_time: int = 0


@dataclass(frozen=True)
class PipelineTestCounts:
    """Test count results for a pipeline run."""

    total_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0


@dataclass(frozen=True)
class PipelineHistory:
    """Historical information about a past pipeline run."""

    id: int
    status: str
    ref: str
    created_at: Optional[str] = None
    duration: Optional[int] = None
    web_url: Optional[str] = None
    test_counts: Optional[PipelineTestCounts] = None

    def __post_init__(self):
        if self.test_counts is None:
            object.__setattr__(self, 'test_counts', PipelineTestCounts())

    @property
    def total_count(self) -> int:
        """Return total test count."""
        return self.test_counts.total_count if self.test_counts else 0

    @property
    def success_count(self) -> int:
        """Return success test count."""
        return self.test_counts.success_count if self.test_counts else 0

    @property
    def failed_count(self) -> int:
        """Return failed test count."""
        return self.test_counts.failed_count if self.test_counts else 0

    @property
    def skipped_count(self) -> int:
        """Return skipped test count."""
        return self.test_counts.skipped_count if self.test_counts else 0


def parse_pipeline_info(pipeline: dict) -> PipelineInfo:
    """Parse raw GitLab pipeline API response into PipelineInfo.

    Args:
        pipeline: Raw dictionary from GitLab API GET /pipelines/:id

    Returns:
        PipelineInfo dataclass with parsed pipeline data
    """
    return PipelineInfo(
        id=pipeline.get("id", 0),
        name=pipeline.get("name", "unknown"),
        status=pipeline.get("status", ""),
        ref=pipeline.get("ref", ""),
        sha=pipeline.get("sha", ""),
        web_url=pipeline.get("web_url", ""),
        metadata=PipelineMetadata(
            created_at=pipeline.get("created_at"),
            updated_at=pipeline.get("updated_at"),
            duration=pipeline.get("duration"),
        ),
    )


def parse_test_summary(test_summary: dict) -> TestSummary:
    """Parse raw GitLab test report summary API response into TestSummary.

    Args:
        test_summary: Raw dictionary from GitLab API GET /pipelines/:id/test_report_summary

    Returns:
        TestSummary dataclass with parsed test result data
    """
    totals = test_summary.get("total", {})
    return TestSummary(
        total_count=totals.get("count", 0),
        success_count=totals.get("success", 0),
        failed_count=totals.get("failed", 0),
        skipped_count=totals.get("skipped", 0),
        error_count=totals.get("error", 0),
        total_time=totals.get("time", 0),
    )


def parse_pipelines(pipelines: List[dict]) -> List[PipelineHistory]:
    """Parse raw GitLab pipelines list API response into list of PipelineHistory.

    Args:
        pipelines: List of raw dictionaries from GitLab API GET /pipelines

    Returns:
        List of PipelineHistory dataclasses with parsed pipeline history data
    """
    return [
        PipelineHistory(
            id=p.get("id", 0),
            status=p.get("status", ""),
            ref=p.get("ref", ""),
            created_at=p.get("created_at"),
            duration=p.get("duration"),
            web_url=p.get("web_url"),
        )
        for p in pipelines
    ]


def add_test_summary_to_pipeline(
    pipeline: PipelineHistory, test_summary: TestSummary
) -> PipelineHistory:
    """Create a new PipelineHistory with test summary data.

    Args:
        pipeline: Existing PipelineHistory object
        test_summary: TestSummary with test counts

    Returns:
        New PipelineHistory instance with test counts added
    """
    return PipelineHistory(
        id=pipeline.id,
        status=pipeline.status,
        ref=pipeline.ref,
        created_at=pipeline.created_at,
        duration=pipeline.duration,
        web_url=pipeline.web_url,
        test_counts=PipelineTestCounts(
            total_count=test_summary.total_count,
            success_count=test_summary.success_count,
            failed_count=test_summary.failed_count,
            skipped_count=test_summary.skipped_count,
        ),
    )
