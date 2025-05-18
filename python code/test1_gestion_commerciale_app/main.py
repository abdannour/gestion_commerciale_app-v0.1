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

        self.sale_view.sale_recorded.connect(self.refresh_product_data_views)

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
        
        # Refresh data based on the view type
        if index == 0 and hasattr(current_widget, "load_data"):  # Dashboard
            current_widget.load_data()
        elif index == 1 and hasattr(current_widget, "load_customers"):  # Clients
            current_widget.load_customers()
        elif index == 2:  # Produits
            if hasattr(current_widget, "load_products"):
                current_widget.load_products()
            if hasattr(current_widget, "load_categories"):
                current_widget.load_categories()
        elif index == 3:  # Achats
            if hasattr(current_widget, "load_products_for_combo"):
                current_widget.load_products_for_combo()
            if hasattr(current_widget, "load_purchase_history"):
                current_widget.load_purchase_history()
        elif index == 4:  # Ventes
            if hasattr(current_widget, "load_products_for_sale"):
                current_widget.load_products_for_sale()
            if hasattr(current_widget, "load_customers_for_sale"):
                current_widget.load_customers_for_sale()
            if hasattr(current_widget, "load_sales_history"):
                current_widget.load_sales_history()
        elif index == 5:  # Stock
            if hasattr(current_widget, "load_stock_data"):
                current_widget.load_stock_data()
            if hasattr(current_widget, "load_categories_filter"):
                current_widget.load_categories_filter()

    def refresh_product_data_views(self):
        print("Refreshing product data in relevant views...")
        if hasattr(self.product_view, "load_products"):
            self.product_view.load_products()
            self.product_view.load_categories()
        if hasattr(self.purchase_view, "load_products_for_combo"):
            self.purchase_view.load_products_for_combo()
        if hasattr(self.stock_view, "load_stock_data"):
            self.stock_view.load_stock_data()
            self.stock_view.load_categories_filter()


if __name__ == "__main__":
    print("Initializing database...")
    initialize_database()
    print("Database check complete.")

    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
