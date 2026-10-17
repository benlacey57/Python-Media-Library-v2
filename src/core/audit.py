from datetime import datetime
import logging
from pathlib import Path
from core.database import Database


class Audit:
    def __init__(self, db: Database, config: dict = None):
        self.db = db
        self.config = config or {}
        self._setup_file_logger()

    def _setup_file_logger(self):
        """Configures optional application-wide file debugging/audit logging."""
        audit_cfg = self.config.get("audit_logging", {})
        self.log_to_file = audit_cfg.get("log_to_file", False)
        self.log_file_path = Path(audit_cfg.get("log_file_path", "media_manager_debug.log"))
        self.log_level = audit_cfg.get("log_level", "INFO").upper()

        if self.log_to_file:
            self.logger = logging.getLogger("MediaManagerAudit")
            self.logger.setLevel(getattr(logging, self.log_level, logging.INFO))
            if not self.logger.handlers:
                handler = logging.FileHandler(self.log_file_path, encoding="utf-8")
                formatter = logging.Formatter("%(asctime)s - %(levelname)s - [%(name)s] - %(message)s")
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
        else:
            self.logger = None

    def log(self, module_name: str, action: str, status: str, message: str):
        """Records an event in the audit_logs database table and optionally to file."""
        status_upper = status.upper()
        timestamp = datetime.now().isoformat()

        # 1. Save to SQLite database audit_logs table
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO audit_logs (module_name, action, status, message, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (module_name, action, status_upper, message, timestamp)
                )
                conn.commit()
        except Exception as e:
            print(f"Failed to write audit log to database: {e}")

        # 2. Optional file-based logging
        if self.logger and self.log_to_file:
            level_map = {
                "INFO": logging.INFO,
                "SUCCESS": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "DEBUG": logging.DEBUG
            }
            log_level = level_map.get(status_upper, logging.INFO)
            self.logger.log(log_level, f"[{module_name}] {action} ({status_upper}): {message}")

    def get_entries(self, limit: int = 100, offset: int = 0) -> list:
        """Retrieves audit log entries with pagination."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()
            return [dict(row) for row in rows]

    def search_entries(self, query: str) -> list:
        """Searches log entries matching module name, action, status, or message."""
        q = f"%{query}%"
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM audit_logs 
                WHERE module_name LIKE ? OR action LIKE ? OR status LIKE ? OR message LIKE ?
                ORDER BY timestamp DESC
                """,
                (q, q, q, q)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_summary(self) -> dict:
        """Returns log entry counts grouped by status (level) and module."""
        summary = {"levels": {}, "modules": {}}
        with self.db.get_connection() as conn:
            level_rows = conn.execute(
                "SELECT status, COUNT(*) as count FROM audit_logs GROUP BY status"
            ).fetchall()
            for r in level_rows:
                summary["levels"][r["status"]] = r["count"]

            module_rows = conn.execute(
                "SELECT module_name, COUNT(*) as count FROM audit_logs GROUP BY module_name"
            ).fetchall()
            for r in module_rows:
                summary["modules"][r["module_name"]] = r["count"]
        return summary

    def get_timeline_counts(self, interval: str = "date") -> list:
        """Groups audit log entries over time (by date or hour) showing counts."""
        with self.db.get_connection() as conn:
            if interval == "hour":
                sql = """
                    SELECT strftime('%Y-%m-%d %H:00', timestamp) as time_bucket, COUNT(*) as count 
                    FROM audit_logs GROUP BY time_bucket ORDER BY time_bucket DESC
                """
            else:
                sql = """
                    SELECT date(timestamp) as time_bucket, COUNT(*) as count 
                    FROM audit_logs GROUP BY time_bucket ORDER BY time_bucket DESC
                """
            rows = conn.execute(sql).fetchall()
            return [{"time_bucket": r["time_bucket"], "count": r["count"]} for r in rows]
          
