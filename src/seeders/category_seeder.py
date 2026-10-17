from core.database import Database
from core.audit import Audit

class CategorySeeder:
    def __init__(self, db: Database, audit: Audit = None):
        self.db = db
        self.audit = audit

    def seed(self) -> dict:
        """Seeds default categories."""
        categories = [("TV Show",), ("Movie",)]
        with self.db.get_connection() as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                categories
            )
            conn.commit()
        
        if self.audit:
            self.audit.log("Seeder", "SEED_CATEGORIES", "SUCCESS", "Populated categories table.")
        return {"categories_seeded": len(categories)}
      
