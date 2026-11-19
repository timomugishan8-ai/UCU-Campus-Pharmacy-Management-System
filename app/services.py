
from database.connection import Database

from database.repositories.medicine_repository import MedicineRepository
from database.repositories.branch_repository import BranchRepository
from database.repositories.stock_repository import StockRepository
from database.repositories.prescription_repository import PrescriptionRepository
from database.repositories.prescriber_repository import PrescriberRepository

from services.medicine_service import MedicineService
from services.stock_service import StockService
from services.prescription_service import PrescriptionService
from services.report_service import ReportService


class ApplicationServices:
    """Create and connect the application's shared dependencies."""

    def __init__(self, db_path=None):

        # 1. Create one shared database manager.
        self.database = Database(db_path)

        # 2. Create repositories using the shared database manager.
        self.medicine_repository = MedicineRepository(self.database)
        self.branch_repository = BranchRepository(self.database)
        self.stock_repository = StockRepository(self.database)
        self.prescription_repository = PrescriptionRepository(self.database)
        self.prescriber_repository = PrescriberRepository(self.database)

        # 3. Create application services.
        self.medicine_service = MedicineService(
            medicine_repository=self.medicine_repository
        )

        self.stock_service = StockService(
            stock_repository=self.stock_repository,
            medicine_repository=self.medicine_repository,
            branch_repository=self.branch_repository,
            database=self.database
        )

        self.prescription_service = PrescriptionService(
            prescription_repository=self.prescription_repository,
            medicine_repository=self.medicine_repository,
            stock_repository=self.stock_repository,
            prescriber_repository=self.prescriber_repository,
            branch_repository=self.branch_repository
        )

        self.report_service = ReportService(
            stock_repository=self.stock_repository,
            database=self.database
        )
