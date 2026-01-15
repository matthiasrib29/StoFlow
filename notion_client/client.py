"""
Simple Notion API Client (réutilise notion_helper.py)
"""

import sys
import os

# Add parent directory to path to import notion_helper
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notion_helper import NotionHelper as _NotionHelper
from .models import Task


class NotionClient:
    """Simple wrapper around NotionHelper"""

    def __init__(self, api_key: str = None, database_id: str = None):
        self._client = _NotionHelper(api_key=api_key, database_id=database_id)

    def create(self, task: Task) -> Task:
        """Create a task"""
        result = self._client.create_task(
            title=task.title,
            status=task.status,
            sprint=task.sprint,
            mvp=task.mvp,
            priority=task.priority,
            estimation=task.estimation,
            categories=task.categories,
            notes=task.notes
        )
        return self._parse(result)

    def get(self, task_id: str) -> Task:
        """Get a task by ID"""
        import urllib.request
        import json

        url = f"{self._client.base_url}/pages/{task_id}"
        headers = {
            "Authorization": f"Bearer {self._client.api_key}",
            "Notion-Version": self._client.notion_version,
            "Content-Type": "application/json"
        }

        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
        return self._parse(result)

    def update(self, task_id: str, **kwargs) -> Task:
        """Update a task"""
        result = self._client.update_task(task_id, **kwargs)
        return self._parse(result)

    def delete(self, task_id: str):
        """Delete (archive) a task"""
        import urllib.request
        import json

        url = f"{self._client.base_url}/pages/{task_id}"
        headers = {
            "Authorization": f"Bearer {self._client.api_key}",
            "Notion-Version": self._client.notion_version,
            "Content-Type": "application/json"
        }

        data = json.dumps({"archived": True}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method="PATCH")
        urllib.request.urlopen(req)

    def list(self, status: str = None, sprint: str = None, limit: int = 100):
        """List tasks"""
        import urllib.request
        import json

        # Use search endpoint (works better for data_sources)
        url = f"{self._client.base_url}/search"
        headers = {
            "Authorization": f"Bearer {self._client.api_key}",
            "Notion-Version": self._client.notion_version,
            "Content-Type": "application/json"
        }

        query_data = {
            "filter": {"property": "object", "value": "page"},
            "page_size": limit
        }

        data = json.dumps(query_data).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))

        # Parse and filter results (only pages with "Tâche" property)
        tasks = []
        for page in result.get("results", []):
            if "Tâche" in page.get("properties", {}):
                try:
                    tasks.append(self._parse(page))
                except Exception:
                    continue  # Skip pages that can't be parsed

        # Client-side filtering (Notion search doesn't support property filters)
        if status:
            tasks = [t for t in tasks if t.status == status]
        if sprint:
            tasks = [t for t in tasks if t.sprint == sprint]

        return tasks

    def _parse(self, page: dict) -> Task:
        """Parse Notion page to Task"""
        props = page.get("properties", {})

        # Helper to safely get select value
        def get_select(key):
            prop = props.get(key, {})
            if not prop:
                return None
            select = prop.get("select")
            return select.get("name") if select else None

        # Get title
        title_prop = props.get("Tâche", {}).get("title", [])
        title = title_prop[0].get("text", {}).get("content", "") if title_prop else ""

        # Get select fields
        status = get_select("Statut") or ""
        sprint = get_select("Sprint")
        mvp = get_select("MVP")
        priority = get_select("Priorité")

        # Get number
        estimation_prop = props.get("Estimation (h)", {})
        estimation = estimation_prop.get("number") if estimation_prop else None

        # Get multi-select
        categories_prop = props.get("Catégorie", {}).get("multi_select", [])
        categories = [c.get("name") for c in categories_prop] if categories_prop else []

        # Get rich text
        notes_prop = props.get("Notes", {}).get("rich_text", [])
        notes = notes_prop[0].get("text", {}).get("content") if notes_prop else None

        return Task(
            id=page.get("id"),
            title=title,
            status=status,
            sprint=sprint,
            mvp=mvp,
            priority=priority,
            estimation=estimation,
            categories=categories,
            notes=notes,
            url=page.get("url")
        )
