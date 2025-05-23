import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QStackedWidget,
    QListWidgetItem,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from database.database import initialize_database, get_db_connection

from views.customer_view import CustomerView
from views.product_view import ProductView
from views.purchase_view import PurchaseView
from views.sale_view import SaleView
from views.stock_view import StockView
from views.dashboard_view import DashboardView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestion Commerciale et de Stock")
        self.setGeometry(100, 100, 1000, 700)

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(180)
        self.nav_list.currentRowChanged.connect(self.change_page)
        main_layout.addWidget(self.nav_list)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.dashboard_view = DashboardView()
        self.customer_view = CustomerView()
        self.product_view = ProductView()
        self.purchase_view = PurchaseView()
        self.sale_view = SaleView()
        self.stock_view = StockView()

        # Connect signals for real-time updates
        self.sale_view.sale_recorded.connect(self.refresh_all_views)
        self.product_view.product_updated.connect(self.refresh_all_views)
        self.purchase_view.purchase_recorded.connect(self.refresh_all_views)
        self.customer_view.customer_updated.connect(self.refresh_customer_views)

        self.add_page("Dashboard", self.dashboard_view)
        self.add_page("Clients", self.customer_view)
        self.add_page("Produits", self.product_view)
        self.add_page("Achats", self.purchase_view)
        self.add_page("Ventes", self.sale_view)
        self.add_page("Stock", self.stock_view)

        self.nav_list.setCurrentRow(0)

    def add_page(self, name, widget):
        item = QListWidgetItem(name)
        item.setSizeHint(QSize(0, 40))
        self.nav_list.addItem(item)
        self.stacked_widget.addWidget(widget)

    def change_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        current_widget = self.stacked_widget.widget(index)
        # Refresh data when changing pages
        self.refresh_all_views()

    def refresh_all_views(self):
        """Refresh all views that contain dynamic data"""
        print("Refreshing all views...")
        if hasattr(self.dashboard_view, "load_data"):
            self.dashboard_view.load_data()
        if hasattr(self.product_view, "load_products"):
            self.product_view.load_products()
            self.product_view.load_categories()
        if hasattr(self.purchase_view, "load_products_for_combo"):
            self.purchase_view.load_products_for_combo()
        if hasattr(self.stock_view, "load_stock_data"):
            self.stock_view.load_stock_data()
            self.stock_view.load_categories_filter()
        if hasattr(self.sale_view, "load_products_for_sale"):
            self.sale_view.load_products_for_sale()
            self.sale_view.load_sales_history()

    def refresh_customer_views(self):
        """Refresh views that contain customer data"""
        print("Refreshing customer-related views...")
        if hasattr(self.customer_view, "load_customers"):
            self.customer_view.load_customers()
        if hasattr(self.sale_view, "load_customers_for_sale"):
            self.sale_view.load_customers_for_sale()


if __name__ == "__main__":
    print("Initializing database...")
    initialize_database()
    print("Database check complete.")

    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
