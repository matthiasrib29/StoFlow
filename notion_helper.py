#!/usr/bin/env python3
"""
Notion Helper - Service pour créer et modifier des tâches Notion

Usage:
    # Créer une tâche
    python notion_helper.py create --title "Ma tâche" --status "En cours"

    # Créer depuis un fichier JSON
    python notion_helper.py create-from-file task_1.json

    # Créer depuis tous les fichiers dans /tmp
    python notion_helper.py create-bulk /tmp/task_*.json

    # Modifier une tâche
    python notion_helper.py update <page_id> --status "Terminé"
"""

import os
import json
import argparse
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error
import sys


class NotionHelper:
    """Helper pour interagir avec l'API Notion"""

    def __init__(self, api_key: Optional[str] = None, database_id: Optional[str] = None):
        """
        Initialize Notion Helper

        Args:
            api_key: Notion API key (or set NOTION_API_KEY env var)
            database_id: Default database ID (or set NOTION_DATABASE_ID env var)
        """
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID", "7469559e-46b6-4431-a344-36e808f8297b")
        self.base_url = "https://api.notion.com/v1"
        self.notion_version = "2025-09-03"

        if not self.api_key:
            raise ValueError("NOTION_API_KEY must be set (env var or parameter)")

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to Notion API

        Args:
            method: HTTP method (GET, POST, PATCH)
            endpoint: API endpoint (e.g., '/pages')
            data: Request body (for POST/PATCH)

        Returns:
            Response JSON
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": self.notion_version,
            "Content-Type": "application/json"
        }

        request_data = json.dumps(data).encode('utf-8') if data else None
        req = urllib.request.Request(
            url,
            data=request_data,
            headers=headers,
            method=method
        )

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"❌ HTTP Error {e.code}: {error_body}", file=sys.stderr)
            raise
        except urllib.error.URLError as e:
            print(f"❌ URL Error: {e.reason}", file=sys.stderr)
            raise

    def create_task(
        self,
        title: str,
        status: str = "📝 À faire",
        sprint: Optional[str] = None,
        mvp: Optional[str] = None,
        priority: Optional[str] = None,
        estimation: Optional[int] = None,
        categories: Optional[List[str]] = None,
        notes: Optional[str] = None,
        database_id: Optional[str] = None
    ) -> Dict:
        """
        Create a new task in Notion

        Args:
            title: Task title (required)
            status: Task status (default: "📝 À faire")
            sprint: Sprint name
            mvp: MVP name
            priority: Priority (🔴 Haute, 🟡 Moyenne, 🟢 Basse)
            estimation: Estimation in hours
            categories: List of categories
            notes: Additional notes
            database_id: Database ID (uses default if not provided)

        Returns:
            Created page object
        """
        db_id = database_id or self.database_id

        properties = {
            "Tâche": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "Statut": {
                "select": {
                    "name": status
                }
            }
        }

        # Add optional fields
        if sprint:
            properties["Sprint"] = {"select": {"name": sprint}}

        if mvp:
            properties["MVP"] = {"select": {"name": mvp}}

        if priority:
            properties["Priorité"] = {"select": {"name": priority}}

        if estimation is not None:
            properties["Estimation (h)"] = {"number": estimation}

        if categories:
            properties["Catégorie"] = {
                "multi_select": [{"name": cat} for cat in categories]
            }

        if notes:
            properties["Notes"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": notes
                        }
                    }
                ]
            }

        data = {
            "parent": {
                "database_id": db_id
            },
            "properties": properties
        }

        return self._make_request("POST", "/pages", data)

    def update_task(
        self,
        page_id: str,
        title: Optional[str] = None,
        status: Optional[str] = None,
        sprint: Optional[str] = None,
        mvp: Optional[str] = None,
        priority: Optional[str] = None,
        estimation: Optional[int] = None,
        categories: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Update an existing task in Notion

        Args:
            page_id: Page ID to update (required)
            title: New title
            status: New status
            sprint: New sprint
            mvp: New MVP
            priority: New priority
            estimation: New estimation
            categories: New categories
            notes: New notes

        Returns:
            Updated page object
        """
        properties = {}

        if title:
            properties["Tâche"] = {
                "title": [{"text": {"content": title}}]
            }

        if status:
            properties["Statut"] = {"select": {"name": status}}

        if sprint:
            properties["Sprint"] = {"select": {"name": sprint}}

        if mvp:
            properties["MVP"] = {"select": {"name": mvp}}

        if priority:
            properties["Priorité"] = {"select": {"name": priority}}

        if estimation is not None:
            properties["Estimation (h)"] = {"number": estimation}

        if categories:
            properties["Catégorie"] = {
                "multi_select": [{"name": cat} for cat in categories]
            }

        if notes:
            properties["Notes"] = {
                "rich_text": [{"text": {"content": notes}}]
            }

        data = {"properties": properties}
        return self._make_request("PATCH", f"/pages/{page_id}", data)

    def create_from_json(self, json_data: Dict) -> Dict:
        """
        Create a task from a JSON structure

        Args:
            json_data: JSON object with parent and properties

        Returns:
            Created page object
        """
        return self._make_request("POST", "/pages", json_data)

    def create_from_file(self, filepath: str) -> Dict:
        """
        Create a task from a JSON file

        Args:
            filepath: Path to JSON file

        Returns:
            Created page object
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"📄 Creating task from {filepath}...")
        result = self.create_from_json(data)

        # Extract title for logging
        title = data.get("properties", {}).get("Tâche", {}).get("title", [{}])[0].get("text", {}).get("content", "Unknown")
        print(f"✅ Created: {title}")

        return result


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Notion Helper - Manage Notion tasks")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new task")
    create_parser.add_argument("--title", required=True, help="Task title")
    create_parser.add_argument("--status", default="📝 À faire", help="Task status")
    create_parser.add_argument("--sprint", help="Sprint name")
    create_parser.add_argument("--mvp", help="MVP name")
    create_parser.add_argument("--priority", help="Priority")
    create_parser.add_argument("--estimation", type=int, help="Estimation (hours)")
    create_parser.add_argument("--categories", nargs="+", help="Categories")
    create_parser.add_argument("--notes", help="Notes")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update an existing task")
    update_parser.add_argument("page_id", help="Page ID to update")
    update_parser.add_argument("--title", help="New title")
    update_parser.add_argument("--status", help="New status")
    update_parser.add_argument("--sprint", help="New sprint")
    update_parser.add_argument("--mvp", help="New MVP")
    update_parser.add_argument("--priority", help="New priority")
    update_parser.add_argument("--estimation", type=int, help="New estimation")
    update_parser.add_argument("--categories", nargs="+", help="New categories")
    update_parser.add_argument("--notes", help="New notes")

    # Create from file command
    file_parser = subparsers.add_parser("create-from-file", help="Create task from JSON file")
    file_parser.add_argument("filepath", help="Path to JSON file")

    # Bulk create command
    bulk_parser = subparsers.add_parser("create-bulk", help="Create multiple tasks from JSON files")
    bulk_parser.add_argument("pattern", help="File pattern (e.g., /tmp/task_*.json)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize helper
    helper = NotionHelper()

    try:
        if args.command == "create":
            result = helper.create_task(
                title=args.title,
                status=args.status,
                sprint=args.sprint,
                mvp=args.mvp,
                priority=args.priority,
                estimation=args.estimation,
                categories=args.categories,
                notes=args.notes
            )
            print(f"✅ Task created: {result.get('id')}")
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "update":
            result = helper.update_task(
                page_id=args.page_id,
                title=args.title,
                status=args.status,
                sprint=args.sprint,
                mvp=args.mvp,
                priority=args.priority,
                estimation=args.estimation,
                categories=args.categories,
                notes=args.notes
            )
            print(f"✅ Task updated: {result.get('id')}")
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "create-from-file":
            result = helper.create_from_file(args.filepath)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "create-bulk":
            import glob
            files = sorted(glob.glob(args.pattern))

            if not files:
                print(f"❌ No files found matching: {args.pattern}")
                return

            print(f"📦 Found {len(files)} files to process")
            print("=" * 80)

            success_count = 0
            error_count = 0

            for filepath in files:
                try:
                    helper.create_from_file(filepath)
                    success_count += 1
                except Exception as e:
                    print(f"❌ Error with {filepath}: {str(e)}")
                    error_count += 1

            print("=" * 80)
            print(f"✅ Successfully created: {success_count} tasks")
            if error_count > 0:
                print(f"❌ Failed: {error_count} tasks")

    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
