"""Confluence REST API client for page operations."""

from typing import Optional, Dict, Any

import requests

import config


class ConfluenceClient:
    """Client for interacting with Confluence REST API.

    This class provides methods to fetch and update Confluence pages
    using Basic Authentication (email + API token).

    Attributes:
        url: Base URL of the Confluence instance
        email: Email address for authentication
        token: API token for authentication
    """

    def __init__(
        self,
        url: Optional[str] = None,
        email: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """Initialize the Confluence client.

        Args:
            url: Base URL of the Confluence instance (defaults to config value)
            email: Email address for authentication (defaults to config value)
            token: API token for authentication (defaults to config value)
        """
        self.url = url or config.CONFLUENCE_URL
        self.email = email or config.CONFLUENCE_EMAIL
        self.token = token or config.CONFLUENCE_TOKEN
        self.session = requests.Session()
        self.session.auth = (self.email, self.token)
        self.session.headers.update({"Content-Type": "application/json"})

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get a Confluence page by ID.

        Args:
            page_id: The ID of the page to retrieve

        Returns:
            Raw JSON response containing page data including body content and version

        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{self.url}/rest/api/content/{page_id}"
        params = {"expand": "body.storage,version"}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def update_page(
        self, page_id: str, title: str, content: str, version: int
    ) -> Dict[str, Any]:
        """Update an existing Confluence page.

        Args:
            page_id: The ID of the page to update
            title: The title of the page
            content: The new content in storage format (HTML)
            version: Current version number (will be incremented)

        Returns:
            Raw JSON response confirming the update

        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{self.url}/rest/api/content/{page_id}"
        data = {
            "id": page_id,
            "type": "page",
            "title": title,
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            },
            "version": {
                "number": version + 1,
                "message": "Updated via GitLab pipeline script"
            }
        }
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()
