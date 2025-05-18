import sys
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
    QComboBox,
    QSpinBox,
    QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


from database.database import search_products, get_all_categories

LOW_STOCK_THRESHOLD = 5


class StockView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_categories_filter()
        self.load_stock_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("Consultation du Stock Actuel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            "font-size: 16pt; font-weight: bold; margin-bottom: 10px;"
        )
        main_layout.addWidget(title_label)

        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par nom/description...")
        self.search_input.textChanged.connect(self.filter_stock_data)

        self.category_filter_combo = QComboBox()
        self.category_filter_combo.addItem("Toutes les catégories")
        self.category_filter_combo.currentIndexChanged.connect(self.filter_stock_data)

        self.stock_level_filter_combo = QComboBox()
        self.stock_level_filter_combo.addItem("Tous les niveaux")
        self.stock_level_filter_combo.addItem(
            f"Stock Faible (<= {LOW_STOCK_THRESHOLD})"
        )
        self.stock_level_filter_combo.addItem("En Stock (> 0)")
        self.stock_level_filter_combo.addItem("Hors Stock (0)")
        self.stock_level_filter_combo.currentIndexChanged.connect(
            self.filter_stock_data
        )

        filter_layout.addWidget(QLabel("Rechercher:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Catégorie:"))
        filter_layout.addWidget(self.category_filter_combo)
        filter_layout.addWidget(QLabel("Niveau Stock:"))
        filter_layout.addWidget(self.stock_level_filter_combo)

        main_layout.addLayout(filter_layout)

        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(4)
        self.stock_table.setHorizontalHeaderLabels(
            ["ID Produit", "Nom", "Catégorie", "Quantité en Stock"]
        )
        self.stock_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.stock_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.stock_table.verticalHeader().setVisible(False)
        self.stock_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.stock_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.stock_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )

        main_layout.addWidget(self.stock_table)

        refresh_button = QPushButton("Rafraîchir")
        refresh_button.clicked.connect(self.load_stock_data)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(refresh_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def load_categories_filter(self):
        """Loads categories into the filter combobox."""

        current_category = self.category_filter_combo.currentText()
        self.category_filter_combo.blockSignals(True)
        self.category_filter_combo.clear()
        self.category_filter_combo.addItem("Toutes les catégories")
        try:
            categories = get_all_categories()
            self.category_filter_combo.addItems(categories)
            index = self.category_filter_combo.findText(current_category)
            if index != -1:
                self.category_filter_combo.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.warning(
                self, "Erreur Catégories", f"Impossible de charger les catégories: {e}"
            )
        finally:
            self.category_filter_combo.blockSignals(False)

    def load_stock_data(self):
        """Loads and displays stock data based on current filters."""
        search_query = self.search_input.text().strip()
        category = self.category_filter_combo.currentText()
        if category == "Toutes les catégories":
            category = None

        stock_level_filter = self.stock_level_filter_combo.currentText()

        self.stock_table.setRowCount(0)
        try:
            products = search_products(search_query, category)
            filtered_products = []

            if stock_level_filter == f"Stock Faible (<= {LOW_STOCK_THRESHOLD})":
                filtered_products = [
                    p for p in products if p["quantity_in_stock"] <= LOW_STOCK_THRESHOLD
                ]
            elif stock_level_filter == "En Stock (> 0)":
                filtered_products = [p for p in products if p["quantity_in_stock"] > 0]
            elif stock_level_filter == "Hors Stock (0)":
                filtered_products = [p for p in products if p["quantity_in_stock"] == 0]
            else:
                filtered_products = products

            if filtered_products:
                self.stock_table.setRowCount(len(filtered_products))
                for row_idx, product in enumerate(filtered_products):
                    stock_qty = product["quantity_in_stock"]
                    item_id = QTableWidgetItem(str(product["id"]))
                    item_name = QTableWidgetItem(product["name"])
                    item_category = QTableWidgetItem(product["category"] or "")
                    item_stock = QTableWidgetItem(str(stock_qty))
                    item_stock.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    if stock_qty <= 0:
                        color = QColor("transparent")
                    elif stock_qty <= LOW_STOCK_THRESHOLD:
                        color = QColor("#f25252")
                    else:
                        color = QColor("#000000")

                    item_id.setBackground(color)
                    item_name.setBackground(color)
                    item_category.setBackground(color)
                    item_stock.setBackground(color)

                    self.stock_table.setItem(row_idx, 0, item_id)
                    self.stock_table.setItem(row_idx, 1, item_name)
                    self.stock_table.setItem(row_idx, 2, item_category)
                    self.stock_table.setItem(row_idx, 3, item_stock)

        except Exception as e:
            QMessageBox.critical(
                self, "Erreur Stock", f"Impossible de charger les données de stock: {e}"
            )

    def filter_stock_data(self):
        """Triggered when search or filter controls change."""
        self.load_stock_data()


if __name__ == "__main__":
    from database.database import initialize_database, add_product, get_all_products

    initialize_database()

    if not get_all_products():
        add_product("Produit Faible Stock", "Desc", "Cat A", 1, 2, 3)
        add_product("Produit OK Stock", "Desc", "Cat B", 10, 20, 15)
        add_product("Produit Hors Stock", "Desc", "Cat A", 5, 10, 0)

    app = QApplication(sys.argv)
    stock_widget = StockView()
    stock_widget.show()
    sys.exit(app.exec())
