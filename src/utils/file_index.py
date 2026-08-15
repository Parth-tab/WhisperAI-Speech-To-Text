import difflib
import logging
import os
import time

import psutil

logger = logging.getLogger("whisperai")


class FileIndexer:
    def __init__(self):
        self.workspace_cache: dict[str, list[str]] = {}
        self.last_scanned: dict[str, float] = {}

    def get_workspace_for_pid(self, pid: int) -> str:
        try:
            process = psutil.Process(pid)
            cwd = process.cwd()
            return cwd
        except Exception as e:
            logger.warning(f"[FileIndexer] Error getting cwd for pid {pid}: {e}")
            return ""

    def scan_workspace(self, workspace_path: str) -> list[str]:
        if not workspace_path or not os.path.exists(workspace_path):
            return []

        # Only scan if not scanned in the last 60 seconds
        now = time.time()
        if (
            workspace_path in self.workspace_cache
            and now - self.last_scanned.get(workspace_path, 0) < 60
        ):
            return self.workspace_cache[workspace_path]

        logger.info(f"[FileIndexer] Scanning workspace: {workspace_path}")
        files = []

        # Avoid traversing deep/irrelevant directories
        ignore_dirs = {
            ".git",
            "node_modules",
            "venv",
            "env",
            "__pycache__",
            ".idea",
            "build",
            "dist",
        }

        try:
            for root, dirs, filenames in os.walk(workspace_path):
                # Don't go deeper than 4 levels
                depth = root[len(workspace_path) :].count(os.sep)
                if depth >= 4:
                    dirs[:] = []

                # Modify dirs in-place to skip ignored directories
                dirs[:] = [d for d in dirs if d not in ignore_dirs]

                for f in filenames:
                    files.append(f)
                    if len(files) >= 10000:
                        break

                if len(files) >= 10000:
                    logger.warning(
                        f"[FileIndexer] Warning: Max file limit (10000) reached for {workspace_path}. Aborting deep scan."
                    )
                    break
        except Exception as e:
            logger.error(f"[FileIndexer] Error scanning workspace: {e}")

        # Evict oldest cache entries if limit reached (>20 workspaces)
        if len(self.workspace_cache) > 20:
            oldest_ws = min(self.last_scanned, key=self.last_scanned.get, default=None)
            if oldest_ws and oldest_ws in self.workspace_cache:
                del self.workspace_cache[oldest_ws]
                del self.last_scanned[oldest_ws]

        self.workspace_cache[workspace_path] = list(set(files))
        self.last_scanned[workspace_path] = now
        logger.info(f"[FileIndexer] Found {len(files)} files.")
        return self.workspace_cache[workspace_path]

    def fuzzy_find_file(self, workspace_path: str, query: str) -> str:
        files = self.scan_workspace(workspace_path)
        if not files:
            return ""

        # Clean query, e.g., "pipeline" or "pipeline dot p y"
        clean_query = query.lower().replace(" ", "").replace("dot", ".")

        matches = difflib.get_close_matches(clean_query, files, n=1, cutoff=0.6)
        if matches:
            return matches[0]

        # Try substring match if fuzzy match fails
        for f in files:
            if clean_query in f.lower():
                return f

        return ""


file_indexer = FileIndexer()
