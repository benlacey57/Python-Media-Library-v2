from core.database import Database
from core.audit import Audit
from seeders.category_seeder import CategorySeeder
from seeders.series_seeder import SeriesSeeder
from seeders.media_seeder import MediaSeeder

class MasterSeeder:
    def __init__(self, db: Database, audit: Audit = None):
        self.db = db
        self.audit = audit
        self.category_seeder = CategorySeeder(db, audit)
        self.series_seeder = SeriesSeeder(db, audit)
        self.media_seeder = MediaSeeder(db, audit)

    def seed_all(self):
        """Runs all independent seeders sequentially to fully populate the database."""
        self.category_seeder.seed()
        self.series_seeder.seed()
        self.media_seeder.seed()
        
        if self.audit:
            self.audit.log("MasterSeeder", "SEED_ALL", "SUCCESS", "Successfully executed full database seeding.")
          
