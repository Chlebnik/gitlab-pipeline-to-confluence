"""HTML content generation for Confluence pages.

This module provides functions to generate Confluence-compatible HTML content
including pipeline statistics tables, ASCII bar charts, and section management.
"""

import re
from datetime import datetime
from typing import List, Optional

from models import PipelineHistory, PipelineInfo, TestSummary


def generate_status_badge(status: str) -> str:
    """Generate Confluence status badge XML for a pipeline status.

    Args:
        status: The pipeline status (e.g., 'success', 'failed', 'running')

    Returns:
        Confluence XML string for a status icon
    """
    return (
        f'<ac:rich-text-icon>'
        f'<ri:icon ri:filename="status-{status.lower()}.svg" />'
        f'</ac:rich-text-icon>'
    )


def generate_ascii_bar_chart(
    data: List[PipelineHistory], value_attr: str = "total_count"
) -> str:
    """Generate an ASCII bar chart showing pipeline history.

    Args:
        data: List of PipelineHistory objects to visualize
        value_attr: Attribute name to use for bar values (default: 'total_count')

    Returns:
        ASCII art string representing pipeline history as a horizontal bar chart
    """
    if not data:
        return "No data available"

    def get_value(item: PipelineHistory) -> int:
        return getattr(item, value_attr, 0)

    max_val = max(get_value(d) for d in data)
    if max_val == 0:
        max_val = 1

    lines = []
    for d in data:
        status = d.status
        val = get_value(d)
        bar_length = int((val / max_val) * 20)
        bar_str = "█" * bar_length
        status_icon = "✓" if status == "success" else "✗" if status == "failed" else "○"
        lines.append(f"{status_icon} {status:10} |{bar_str}| {val}")

    return "\n".join(lines)


def format_duration(seconds: Optional[int]) -> str:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds, or None

    Returns:
        Formatted duration string (e.g., '2m 30s', '45s', or 'N/A')
    """
    if seconds is None:
        return "N/A"
    try:
        secs = int(seconds)
        mins = secs // 60
        remaining_secs = secs % 60
        if mins > 0:
            return f"{mins}m {remaining_secs}s"
        return f"{secs}s"
    except (ValueError, TypeError):
        return str(seconds)


def format_timestamp(ts: Optional[str]) -> str:
    """Format ISO timestamp to readable date string.

    Args:
        ts: ISO format timestamp string, or None/empty

    Returns:
        Formatted date string (e.g., '2024-01-15 14:30') or 'N/A'
    """
    if not ts:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return ts


def generate_pipeline_section(
    pipeline_name: str,
    pipeline_info: PipelineInfo,
    test_summary: TestSummary,
    recent_pipelines: List[PipelineHistory],
) -> str:
    """Generate Confluence HTML section for a pipeline.

    Creates an HTML section containing pipeline information, test results table,
    and a bar chart visualization of recent pipeline runs.

    Args:
        pipeline_name: Name of the pipeline (used as section header)
        pipeline_info: Current pipeline information
        test_summary: Test results summary
        recent_pipelines: List of recent pipeline runs for history chart

    Returns:
        HTML string suitable for Confluence storage format
    """
    chart = generate_ascii_bar_chart(recent_pipelines[:10])

    return f"""<h2>{pipeline_name}</h2>

<p>
    <strong>Latest Pipeline Run:</strong>
    <a href="{pipeline_info.web_url}">{pipeline_info.id}</a> |
    Status: {pipeline_info.status} |
    Duration: {format_duration(pipeline_info.duration)}
</p>

<h3>Test Results</h3>
<table>
    <tbody>
        <tr>
            <th>Total</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Skipped</th>
            <th>Errors</th>
            <th>Time</th>
        </tr>
        <tr>
            <td>{test_summary.total_count}</td>
            <td style="background-color: #e8f5e9;">{test_summary.success_count}</td>
            <td style="background-color: #ffebee;">{test_summary.failed_count}</td>
            <td style="background-color: #fff3e0;">{test_summary.skipped_count}</td>
            <td>{test_summary.error_count}</td>
            <td>{format_duration(test_summary.total_time)}</td>
        </tr>
    </tbody>
</table>

<h3>Pipeline History (Last 10 Runs)</h3>
<pre>{chart}</pre>

<p><em>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
"""


def find_and_replace_section(
    content: str, pipeline_name: str, new_section: str
) -> str:
    """Find and replace a pipeline section in Confluence page content.

    Searches for an existing section by pipeline name (h2 header) and replaces
    its content. If no section exists, the new section is appended.

    Args:
        content: Current Confluence page content in storage format
        pipeline_name: Name of the pipeline section to find
        new_section: New HTML content to replace the section with

    Returns:
        Updated content with the section replaced or appended
    """
    pattern = rf"(<h2>{re.escape(pipeline_name)}</h2>.*?)(<h2>|$)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

    if match:
        end_pos = match.end()

        if end_pos < len(content):
            return content[: match.start()] + new_section + content[end_pos:]
        return content[: match.start()] + new_section

    return content + new_section
