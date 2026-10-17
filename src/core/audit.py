from datetime import datetime
import functools
import logging
from pathlib import Path
from core.database import Database


class Audit:
    def __init__(self, db: Database, config: dict = None):
        self.db = db
        self.config = config or {}
        self._setup_file_logger()

    def _setup_file_logger(self):
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

        if self.logger and self.log_to_file:
            level_map = {
                "INFO": logging.INFO,
                "SUCCESS": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "DEBUG": logging.DEBUG
            }
            self.logger.log(level_map.get(status_upper, logging.INFO), f"[{module_name}] {action} ({status_upper}): {message}")

    def log_action(self, action_name: str = None):
        """
        A decorator that automatically audits method execution, 
        catching successes, arguments, and unhandled exceptions.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(instance, *args, **kwargs):
                module_name = instance.__class__.__name__
                action = action_name or func.__name__.upper()
                
                try:
                    # Execute the core method logic
                    result = func(instance, *args, **kwargs)
                    
                    # Log successful execution
                    self.log(
                        module_name=module_name,
                        action=action,
                        status="SUCCESS",
                        message=f"Successfully executed {func.__name__}."
                    )
                    return result
                
                except Exception as e:
                    # Log failure and re-raise exception
                    self.log(
                        module_name=module_name,
                        action=action,
                        status="ERROR",
                        message=f"Failed executing {func.__name__}: {str(e)}"
                    )
                    raise
            return wrapper
        return decorator
        
