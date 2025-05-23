import sys
import datetime
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal


from database.database import (
    add_purchase,
    get_purchase_history,
    get_all_products,
    add_product,
    get_product_by_id,
)


class PurchaseView(QWidget):
    # Signal for purchase updates
    purchase_recorded = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.products_data = {}
        self.init_ui()
        self.load_products_for_combo()
        self.load_purchase_history()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("Enregistrer un Achat Fournisseur")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            "font-size: 16pt; font-weight: bold; margin-bottom: 10px;"
        )
        main_layout.addWidget(title_label)

        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)

        form_layout.addWidget(QLabel("Produit*:"), 0, 0)
        self.product_combo = QComboBox()
        form_layout.addWidget(self.product_combo, 0, 1)

        form_layout.addWidget(QLabel("Quantité*:"), 0, 2)
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 99999)
        form_layout.addWidget(self.quantity_spinbox, 0, 3)

        form_layout.addWidget(QLabel("Coût Unitaire*:"), 1, 0)
        self.cost_spinbox = QDoubleSpinBox()
        self.cost_spinbox.setRange(0.0, 999999.99)
        self.cost_spinbox.setDecimals(2)
        self.cost_spinbox.setSuffix(" DA")
        form_layout.addWidget(self.cost_spinbox, 1, 1)

        form_layout.addWidget(QLabel("Fournisseur:"), 1, 2)
        self.supplier_input = QLineEdit()
        self.supplier_input.setPlaceholderText("(Optionnel)")
        form_layout.addWidget(self.supplier_input, 1, 3)

        self.add_purchase_button = QPushButton("Enregistrer l'Achat")
        self.add_purchase_button.clicked.connect(self.add_new_purchase)
        form_layout.addWidget(self.add_purchase_button, 2, 0, 1, 4)

        main_layout.addWidget(form_widget)

        main_layout.addSpacerItem(
            QSpacerItem(
                20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )

        history_title = QLabel("Historique des Achats Récents")
        history_title.setStyleSheet(
            "font-size: 14pt; font-weight: bold; margin-top: 15px;"
        )
        main_layout.addWidget(history_title)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            ["ID Achat", "Date", "Produit", "Quantité", "Coût Unit.", "Fournisseur"]
        )
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )

        main_layout.addWidget(self.history_table)

        self.refresh_button = QPushButton("Rafraîchir l'Historique")
        self.refresh_button.clicked.connect(self.load_purchase_history)
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        refresh_layout.addWidget(self.refresh_button)
        main_layout.addLayout(refresh_layout)

        self.setLayout(main_layout)

    def load_products_for_combo(self):
        """Loads product names and IDs into the product combobox."""
        self.product_combo.clear()
        self.products_data.clear()
        self.product_combo.addItem("Sélectionner un produit...", -1)
        try:
            products = get_all_products()
            if products:
                for product in products:
                    display_text = (
                        f"{product['name']} (Stock: {product['quantity_in_stock']})"
                    )
                    self.product_combo.addItem(display_text, product["id"])
                    self.products_data[display_text] = product["id"]
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur Produits",
                f"Impossible de charger la liste des produits: {e}",
            )

    def load_purchase_history(self):

        self.history_table.setRowCount(0)
        try:
            history = get_purchase_history()
            if history:
                self.history_table.setRowCount(len(history))
                for row_idx, purchase in enumerate(history):
                    self.history_table.setItem(
                        row_idx, 0, QTableWidgetItem(str(purchase["id"]))
                    )

                    date_str = purchase["purchase_date"]
                    try:

                        dt_obj = datetime.datetime.fromisoformat(date_str)
                        display_date = dt_obj.strftime("%Y-%m-%d %H:%M")
                    except ValueError:
                        display_date = date_str
                    self.history_table.setItem(
                        row_idx, 1, QTableWidgetItem(display_date)
                    )
                    self.history_table.setItem(
                        row_idx, 2, QTableWidgetItem(purchase["product_name"])
                    )
                    self.history_table.setItem(
                        row_idx, 3, QTableWidgetItem(str(purchase["quantity"]))
                    )
                    self.history_table.setItem(
                        row_idx,
                        4,
                        QTableWidgetItem(f"{purchase['cost_per_unit']:.2f} DA"),
                    )
                    self.history_table.setItem(
                        row_idx, 5, QTableWidgetItem(purchase["supplier"] or "")
                    )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur Historique",
                f"Impossible de charger l'historique des achats: {e}",
            )

    def add_new_purchase(self):

        selected_index = self.product_combo.currentIndex()
        if selected_index <= 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un produit.")
            return

        product_id = self.product_combo.itemData(selected_index)
        quantity = self.quantity_spinbox.value()
        cost = self.cost_spinbox.value()
        supplier = self.supplier_input.text().strip() or None

        if quantity <= 0 or cost < 0:
            QMessageBox.warning(
                self,
                "Attention",
                "La quantité doit être positive et le coût doit être positif ou nul.",
            )
            return

        new_purchase_id = add_purchase(product_id, quantity, cost, supplier)

        if new_purchase_id:
            QMessageBox.information(
                self, "Succès", f"Achat pour le produit ID {product_id} enregistré."
            )

            self.load_purchase_history()
            self.load_products_for_combo()

            self.product_combo.setCurrentIndex(0)
            self.quantity_spinbox.setValue(1)
            self.cost_spinbox.setValue(0.0)
            self.supplier_input.clear()

            self.purchase_recorded.emit()

        else:
            QMessageBox.critical(self, "Erreur", "Impossible d'enregistrer l'achat.")


if __name__ == "__main__":
    from database.database import initialize_database

    initialize_database()

    if not get_all_products():
        add_product("Produit Test", "Description Test", "Cat Test", 10.0, 20.0, 5)

    app = QApplication(sys.argv)
    purchase_widget = PurchaseView()
    purchase_widget.show()
    sys.exit(app.exec())
