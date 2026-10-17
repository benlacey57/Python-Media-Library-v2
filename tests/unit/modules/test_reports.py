from core.database import Database


class ReportingModule:

    def __init__(self, db: Database):
        self.db = db

    def get_library_summary(self) -> dict:
        """Computes aggregate library statistics directly from the database."""
        with self.db.get_connection() as conn:
            total_files = conn.execute("SELECT COUNT(*) FROM media_items").fetchone()[0]
            total_size = conn.execute("SELECT SUM(file_size_bytes) FROM media_items").fetchone()[0] or 0
            
            cat_rows = conn.execute("""
                SELECT c.name as category_name, COUNT(m.media_id) as count, SUM(m.file_size_bytes) as size
                FROM media_items m
                JOIN categories c ON m.category_id = c.category_id
                GROUP BY c.name
            """).fetchall()

            categories = {}
            for row in cat_rows:
                categories[row["category_name"]] = {
                    "count": row["count"],
                    "size_bytes": row["size"]
                }

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "categories": categories,
        }

    def get_missing_episodes_report(self) -> list:
        """Retrieves all tracked missing episodes across series."""
        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT m.*, s.title as series_title 
                FROM missing_episodes m
                JOIN series s ON m.series_id = s.series_id
            """).fetchall()
            return [dict(row) for row in rows]
            
