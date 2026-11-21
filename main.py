from app.services import ApplicationServices
from gui.login import ask_for_login
from gui.main_window import MainWindow
from database.seed_data import seed

import tkinter as tk

def main():
    """Initialize and launch the pharmacy management system."""

    # 1. Create the shared application dependencies.
    services = ApplicationServices()

    # 2. Create the database tables.
    services.database.initialize_schema()

    # 3. Insert fictional sample data.
    seed(services.database)

    # 4. Sign in first: the login gate closes itself on success and
    #    stores the session in services.current_user.
    services.current_user = ask_for_login(services)
    if services.current_user is None:
        return  # the login window was closed without signing in

    # 5. Create the main application window.
    app = MainWindow(services)

    # 6. Start Tkinter's event loop.
    app.mainloop()


if __name__ == "__main__":
    main()