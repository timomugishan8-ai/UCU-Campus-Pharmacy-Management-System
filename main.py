from app.services import ApplicationServices
from gui.main_window import MainWindow
from database.seed_data import seed


def main():
    """Initialize and launch the pharmacy management system."""

    # 1. Create the shared application dependencies.
    services = ApplicationServices()

    # 2. Create the database tables.
    services.database.initialize_schema()

    # 3. Insert fictional sample data.
    seed(services.database)

    # 4. Create the main application window.
    app = MainWindow(services)

    # 5. Start Tkinter's event loop.
    app.mainloop()


if __name__ == "__main__":
    main()