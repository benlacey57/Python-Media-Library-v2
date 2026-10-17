from core.database import Database
from core.audit import log_audit

class DatabaseSeeder:
    def __init__(self, db: Database):
        self.db = db

    def seed_categories(self):
        """Seeds default media categories."""
        with self.db.get_connection() as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                [("TV Show",), ("Movie",)]
            )
            conn.commit()
        log_audit(self.db, "Seeder", "SEED_CATEGORIES", "SUCCESS", "Seeded default categories.")

    def seed_series(self):
        """Seeds sample TV series data for testing and development."""
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO series 
                (series_id, title, sort_title, imdb_id, release_year, start_date, end_date, genre, age_rating, total_seasons, total_episodes, overview, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    1, 
                    "Breaking Bad", 
                    "Breaking Bad", 
                    "tt0903747", 
                    2008, 
                    "2008-01-20", 
                    "2013-09-29", 
                    "Crime, Drama, Thriller", 
                    "TV-MA", 
                    5, 
                    62, 
                    "A chemistry teacher diagnosed with inoperable lung cancer turns to manufacturing and selling methamphetamine.", 
                    "Ended"
                )
            )
            conn.commit()
        log_audit(self.db, "Seeder", "SEED_SERIES", "SUCCESS", "Seeded sample series: Breaking Bad.")

    def seed_all(self):
        """Runs all database seeders in logical order."""
        self.seed_categories()
        self.seed_series()
              
