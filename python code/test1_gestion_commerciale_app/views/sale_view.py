import sys
import datetime
from PyQt6.QtWidgets import (
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
    QGridLayout,
    QGroupBox,
    QDialog,
    QDialogButtonBox,
    QTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from database.database import (
    add_sale,
    get_sales_history,
    get_sale_items,
    get_all_products,
    get_all_customers,
    get_product_by_id,
    get_db_connection,
    add_product,
    add_customer,
)


class SaleView(QWidget):

    sale_recorded = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.products_cache = {}
        self.customers_cache = {}
        self.current_sale_items = []
        self.selected_sale_id_for_details = None
        self.init_ui()
        self.load_initial_data()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        new_sale_group = QGroupBox("Nouvelle Vente")
        new_sale_layout = QVBoxLayout()

        customer_layout = QHBoxLayout()
        customer_layout.addWidget(QLabel("Client:"))
        self.customer_combo = QComboBox()
        customer_layout.addWidget(self.customer_combo)
        new_sale_layout.addLayout(customer_layout)

        add_item_layout = QGridLayout()
        add_item_layout.addWidget(QLabel("Produit:"), 0, 0)
        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(
            self.update_price_and_stock_display
        )
        add_item_layout.addWidget(self.product_combo, 0, 1)

        add_item_layout.addWidget(QLabel("Qté:"), 0, 2)
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 1)
        add_item_layout.addWidget(self.quantity_spinbox, 0, 3)

        self.price_display_label = QLabel("Prix Unit.: --.-- €")
        add_item_layout.addWidget(self.price_display_label, 1, 1)
        self.stock_display_label = QLabel("Stock: --")
        add_item_layout.addWidget(self.stock_display_label, 1, 3)

        self.add_item_button = QPushButton("Ajouter au Panier")
        self.add_item_button.clicked.connect(self.add_item_to_sale)
        add_item_layout.addWidget(self.add_item_button, 2, 0, 1, 4)
        new_sale_layout.addLayout(add_item_layout)

        new_sale_layout.addWidget(QLabel("Panier Actuel:"))
        self.current_sale_table = QTableWidget()
        self.current_sale_table.setColumnCount(5)
        self.current_sale_table.setHorizontalHeaderLabels(
            ["Produit", "Qté", "Prix Unit.", "Sous-Total", "Retirer"]
        )
        self.current_sale_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.current_sale_table.verticalHeader().setVisible(False)
        self.current_sale_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.current_sale_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        new_sale_layout.addWidget(self.current_sale_table)

        finalize_layout = QHBoxLayout()
        self.total_label = QLabel("Total Vente: 0.00 €")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        self.finalize_button = QPushButton("Finaliser la Vente")
        self.finalize_button.clicked.connect(self.finalize_current_sale)
        self.clear_sale_button = QPushButton("Annuler Vente")
        self.clear_sale_button.clicked.connect(self.clear_current_sale)

        finalize_layout.addWidget(self.total_label)
        finalize_layout.addStretch()
        finalize_layout.addWidget(self.clear_sale_button)
        finalize_layout.addWidget(self.finalize_button)
        new_sale_layout.addLayout(finalize_layout)

        new_sale_group.setLayout(new_sale_layout)
        main_layout.addWidget(new_sale_group, 1)

        history_group = QGroupBox("Historique des Ventes")
        history_layout = QVBoxLayout()

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(
            ["ID Vente", "Date", "Client", "Montant Total"]
        )
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.history_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.history_table.itemSelectionChanged.connect(self.on_history_row_selected)
        self.history_table.doubleClicked.connect(self.show_sale_details_dialog)

        history_layout.addWidget(self.history_table)

        history_button_layout = QHBoxLayout()
        self.view_details_button = QPushButton("Voir Détails Vente")
        self.view_details_button.setEnabled(False)
        self.view_details_button.clicked.connect(self.show_sale_details_dialog)
        self.generate_receipt_button = QPushButton("Générer Ticket")
        self.generate_receipt_button.setEnabled(False)
        self.generate_receipt_button.clicked.connect(self.show_receipt_dialog)
        self.refresh_history_button = QPushButton("Rafraîchir Historique")
        self.refresh_history_button.clicked.connect(self.load_sales_history)

        history_button_layout.addStretch()
        history_button_layout.addWidget(self.view_details_button)
        history_button_layout.addWidget(self.generate_receipt_button)
        history_button_layout.addWidget(self.refresh_history_button)
        history_layout.addLayout(history_button_layout)

        history_group.setLayout(history_layout)
        main_layout.addWidget(history_group, 1)

        self.setLayout(main_layout)

    def load_initial_data(self):

        self.load_products_for_sale()
        self.load_customers_for_sale()
        self.load_sales_history()

    def load_products_for_sale(self):

        self.product_combo.clear()
        self.products_cache.clear()
        self.product_combo.addItem("Sélectionner un produit...", -1)
        try:
            products = get_all_products()
            if products:
                for product in products:
                    if product["quantity_in_stock"] > 0:
                        self.product_combo.addItem(product["name"], product["id"])
                        self.products_cache[product["id"]] = {
                            "name": product["name"],
                            "price": product["selling_price"],
                            "stock": product["quantity_in_stock"],
                        }
            self.update_price_and_stock_display()
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur Produits", f"Impossible de charger les produits: {e}"
            )

    def load_customers_for_sale(self):

        self.customer_combo.clear()
        self.customers_cache.clear()
        self.customer_combo.addItem("select client", -1)
        try:
            customers = get_all_customers()
            if customers:
                for customer in customers:
                    self.customer_combo.addItem(customer["name"], customer["id"])
                    self.customers_cache[customer["id"]] = customer["name"]
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur Clients", f"Impossible de charger les clients: {e}"
            )

    def update_price_and_stock_display(self):

        selected_index = self.product_combo.currentIndex()
        if selected_index > 0:
            product_id = self.product_combo.itemData(selected_index)
            if product_id in self.products_cache:
                product_info = self.products_cache[product_id]
                self.price_display_label.setText(
                    f"Prix Unit.: {product_info['price']:.2f} €"
                )
                self.stock_display_label.setText(f"Stock: {product_info['stock']}")
                self.quantity_spinbox.setRange(1, product_info["stock"])
                self.quantity_spinbox.setEnabled(True)
                self.add_item_button.setEnabled(True)
            else:

                self.price_display_label.setText("Prix Unit.: --.-- €")
                self.stock_display_label.setText("Stock: --")
                self.quantity_spinbox.setRange(1, 1)
                self.quantity_spinbox.setEnabled(False)
                self.add_item_button.setEnabled(False)
        else:
            self.price_display_label.setText("Prix Unit.: --.-- €")
            self.stock_display_label.setText("Stock: --")
            self.quantity_spinbox.setRange(1, 1)
            self.quantity_spinbox.setEnabled(False)
            self.add_item_button.setEnabled(False)

    def add_item_to_sale(self):

        selected_product_index = self.product_combo.currentIndex()
        if selected_product_index <= 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un produit.")
            return

        product_id = self.product_combo.itemData(selected_product_index)
        quantity = self.quantity_spinbox.value()

        if product_id in self.products_cache:
            product_info = self.products_cache[product_id]

            current_cart_qty = sum(
                item["quantity"]
                for item in self.current_sale_items
                if item["product_id"] == product_id
            )
            if quantity + current_cart_qty > product_info["stock"]:
                QMessageBox.warning(
                    self,
                    "Stock Insuffisant",
                    f"Stock disponible pour '{product_info['name']}': {product_info['stock']}. "
                    f"Quantité demandée ({quantity}) + déjà au panier ({current_cart_qty}) dépasse le stock.",
                )
                return

            existing_item_index = -1
            for i, item in enumerate(self.current_sale_items):
                if item["product_id"] == product_id:
                    existing_item_index = i
                    break

            if existing_item_index != -1:

                self.current_sale_items[existing_item_index]["quantity"] += quantity
                self.current_sale_items[existing_item_index]["subtotal"] = (
                    self.current_sale_items[existing_item_index]["quantity"]
                    * product_info["price"]
                )
            else:

                sale_item = {
                    "product_id": product_id,
                    "name": product_info["name"],
                    "quantity": quantity,
                    "price_at_sale": product_info["price"],
                    "subtotal": quantity * product_info["price"],
                }
                self.current_sale_items.append(sale_item)

            self.refresh_current_sale_table()
            self.update_total()

            self.product_combo.setCurrentIndex(0)
            self.quantity_spinbox.setValue(1)

        else:
            QMessageBox.critical(
                self, "Erreur", "Produit sélectionné non trouvé dans le cache."
            )

    def refresh_current_sale_table(self):

        self.current_sale_table.setRowCount(0)
        self.current_sale_table.setRowCount(len(self.current_sale_items))

        for row_idx, item in enumerate(self.current_sale_items):
            self.current_sale_table.setItem(row_idx, 0, QTableWidgetItem(item["name"]))
            self.current_sale_table.setItem(
                row_idx, 1, QTableWidgetItem(str(item["quantity"]))
            )
            self.current_sale_table.setItem(
                row_idx, 2, QTableWidgetItem(f"{item['price_at_sale']:.2f} €")
            )
            self.current_sale_table.setItem(
                row_idx, 3, QTableWidgetItem(f"{item['subtotal']:.2f} €")
            )

            remove_button = QPushButton("X")
            remove_button.setFixedSize(25, 25)
            remove_button.setStyleSheet("color: red; font-weight: bold;")

            remove_button.clicked.connect(
                lambda checked, r=row_idx: self.remove_item_from_sale(r)
            )
            self.current_sale_table.setCellWidget(row_idx, 4, remove_button)

    def remove_item_from_sale(self, row_index):

        if 0 <= row_index < len(self.current_sale_items):
            del self.current_sale_items[row_index]
            self.refresh_current_sale_table()
            self.update_total()

    def update_total(self):

        total = sum(item["subtotal"] for item in self.current_sale_items)
        self.total_label.setText(f"Total Vente: {total:.2f} €")

    def clear_current_sale(self):

        self.current_sale_items = []
        self.refresh_current_sale_table()
        self.update_total()
        self.customer_combo.setCurrentIndex(0)
        self.product_combo.setCurrentIndex(0)
        self.quantity_spinbox.setValue(1)

    def finalize_current_sale(self):

        if not self.current_sale_items:
            QMessageBox.warning(
                self,
                "Vente Vide",
                "Le panier est vide. Ajoutez des produits avant de finaliser.",
            )
            return

        selected_customer_index = self.customer_combo.currentIndex()
        customer_id = None
        if selected_customer_index > 0:
            customer_id = self.customer_combo.itemData(selected_customer_index)

        items_for_db = [
            {
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "price_at_sale": item["price_at_sale"],
            }
            for item in self.current_sale_items
        ]

        total = sum(item["subtotal"] for item in self.current_sale_items)
        customer_name = self.customer_combo.currentText()
        item_count = len(self.current_sale_items)
        confirm_msg = f"Confirmer la vente ?\n\nClient: {customer_name}\nNombre d'articles: {item_count}\nMontant Total: {total:.2f} €"

        reply = QMessageBox.question(
            self,
            "Confirmation Vente",
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Yes:
            sale_id = add_sale(items_for_db, customer_id)
            if sale_id:
                QMessageBox.information(
                    self, "Succès", f"Vente ID {sale_id} enregistrée avec succès."
                )
                self.clear_current_sale()
                self.load_sales_history()
                self.load_products_for_sale()
                self.sale_recorded.emit()

            else:
                QMessageBox.critical(
                    self,
                    "Erreur Base de Données",
                    "Erreur lors de l'enregistrement de la vente. Vérifiez les logs ou le stock.",
                )

    def load_sales_history(self):

        self.history_table.setRowCount(0)
        self.selected_sale_id_for_details = None
        self.view_details_button.setEnabled(False)
        try:
            history = get_sales_history()
            if history:
                self.history_table.setRowCount(len(history))
                for row_idx, sale in enumerate(history):
                    self.history_table.setItem(
                        row_idx, 0, QTableWidgetItem(str(sale["id"]))
                    )
                    date_str = sale["sale_date"]
                    try:
                        dt_obj = datetime.datetime.fromisoformat(date_str)
                        display_date = dt_obj.strftime("%Y-%m-%d %H:%M")
                    except ValueError:
                        display_date = date_str
                    self.history_table.setItem(
                        row_idx, 1, QTableWidgetItem(display_date)
                    )
                    self.history_table.setItem(
                        row_idx, 2, QTableWidgetItem(sale["customer_name"] or "Anonyme")
                    )
                    self.history_table.setItem(
                        row_idx, 3, QTableWidgetItem(f"{sale['total_amount']:.2f} €")
                    )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur Historique",
                f"Impossible de charger l'historique des ventes: {e}",
            )

    def on_history_row_selected(self):

        selected_items = self.history_table.selectedItems()
        if selected_items:
            selected_row = self.history_table.currentRow()
            self.selected_sale_id_for_details = int(
                self.history_table.item(selected_row, 0).text()
            )
            self.view_details_button.setEnabled(True)
            self.generate_receipt_button.setEnabled(True)
        else:
            self.selected_sale_id_for_details = None
            self.view_details_button.setEnabled(False)
            self.generate_receipt_button.setEnabled(False)

    def show_sale_details_dialog(self):

        if self.selected_sale_id_for_details is None:

            selected_items = self.history_table.selectedItems()
            if not selected_items:
                return
            selected_row = self.history_table.currentRow()
            self.selected_sale_id_for_details = int(
                self.history_table.item(selected_row, 0).text()
            )

        if self.selected_sale_id_for_details is not None:
            try:
                items = get_sale_items(self.selected_sale_id_for_details)
                dialog = SaleDetailsDialog(
                    self.selected_sale_id_for_details, items, self
                )
                dialog.exec()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur Détails",
                    f"Impossible de charger les détails de la vente: {e}",
                )

    def show_receipt_dialog(self):

        if self.selected_sale_id_for_details is None:
            selected_items = self.history_table.selectedItems()
            if not selected_items:
                return
            selected_row = self.history_table.currentRow()
            self.selected_sale_id_for_details = int(
                self.history_table.item(selected_row, 0).text()
            )

        if self.selected_sale_id_for_details is not None:
            try:
                receipt_text = self.generate_receipt_text(
                    self.selected_sale_id_for_details
                )
                if receipt_text:
                    dialog = ReceiptDialog(
                        self.selected_sale_id_for_details, receipt_text, self
                    )
                    dialog.exec()
                else:
                    QMessageBox.warning(
                        self,
                        "Erreur Ticket",
                        "Impossible de générer les données du ticket.",
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur Ticket",
                    f"Erreur lors de la génération du ticket: {e}",
                )

    def generate_receipt_text(self, sale_id):

        try:

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sale_date, customer_id, total_amount FROM Sales WHERE id = ?",
                (sale_id,),
            )
            sale_header = cursor.fetchone()
            conn.close()

            if not sale_header:
                return None

            customer_info = "Client: Anonyme"
            if sale_header["customer_id"]:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name, address, phone FROM Customers WHERE id = ?",
                    (sale_header["customer_id"],),
                )
                cust = cursor.fetchone()
                conn.close()
                if cust:
                    customer_info = f"Client: {cust['name']}\n"
                    if cust["address"]:
                        customer_info += f"Adresse: {cust['address']}\n"
                    if cust["phone"]:
                        customer_info += f"Tél: {cust['phone']}"

            items = get_sale_items(sale_id)
            if not items:
                return None

            receipt = f"--- TICKET DE VENTE ---\n\n"
            receipt += f"Vente ID: {sale_id}\n"
            try:
                dt_obj = datetime.datetime.fromisoformat(sale_header["sale_date"])
                receipt += f"Date: {dt_obj.strftime('%Y-%m-%d %H:%M:%S')}\n"
            except ValueError:
                receipt += f"Date: {sale_header['sale_date']}\n"
            receipt += f"{customer_info}\n"
            receipt += f"{'-'*40}\n"
            receipt += f"{'Produit':<20} {'Qté':>3} {'Prix U.':>8} {'Total':>8}\n"
            receipt += f"{'-'*40}\n"

            for item in items:
                name = item["product_name"][:20]
                qty = str(item["quantity"])
                price = f"{item['price_at_sale']:.2f}"
                subtotal = f"{item['quantity'] * item['price_at_sale']:.2f}"
                receipt += f"{name:<20} {qty:>3} {price:>8} {subtotal:>8}\n"

            receipt += f"{'-'*40}\n"
            receipt += f"{'MONTANT TOTAL:':>32} {sale_header['total_amount']:.2f} €\n"
            receipt += f"\n--- Merci de votre visite ! ---\n"

            return receipt

        except Exception as e:
            print(f"Error generating receipt text for sale {sale_id}: {e}")
            return None


class SaleDetailsDialog(QDialog):
    def __init__(self, sale_id, items_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Détails de la Vente ID: {sale_id}")
        self.setMinimumWidth(500)
        self.sale_id = sale_id

        layout = QVBoxLayout(self)

        self.details_table = QTableWidget()
        self.details_table.setColumnCount(4)
        self.details_table.setHorizontalHeaderLabels(
            ["Produit", "Quantité", "Prix Unit.", "Sous-Total"]
        )
        self.details_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.details_table.verticalHeader().setVisible(False)
        self.details_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        layout.addWidget(self.details_table)

        self.populate_table(items_data)

        button_box = QDialogButtonBox()

        button_box.addButton(QDialogButtonBox.StandardButton.Ok)

        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def populate_table(self, items_data):
        self.details_table.setRowCount(0)
        if items_data:
            self.details_table.setRowCount(len(items_data))
            total = 0.0
            for row_idx, item in enumerate(items_data):
                subtotal = item["quantity"] * item["price_at_sale"]
                total += subtotal
                self.details_table.setItem(
                    row_idx, 0, QTableWidgetItem(item["product_name"])
                )
                self.details_table.setItem(
                    row_idx, 1, QTableWidgetItem(str(item["quantity"]))
                )
                self.details_table.setItem(
                    row_idx, 2, QTableWidgetItem(f"{item['price_at_sale']:.2f} €")
                )
                self.details_table.setItem(
                    row_idx, 3, QTableWidgetItem(f"{subtotal:.2f} €")
                )


class ReceiptDialog(QDialog):
    def __init__(self, sale_id, receipt_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Ticket de Vente - ID: {sale_id}")
        self.setMinimumSize(450, 500)

        layout = QVBoxLayout(self)

        self.receipt_display = QTextEdit()
        self.receipt_display.setReadOnly(True)
        self.receipt_display.setFont(QFont("Courier New", 10))
        self.receipt_display.setText(receipt_text)
        layout.addWidget(self.receipt_display)

        button_box = QDialogButtonBox()

        close_button = button_box.addButton(QDialogButtonBox.StandardButton.Close)

        close_button.clicked.connect(self.accept)

        layout.addWidget(button_box)
        self.setLayout(layout)


if __name__ == "__main__":
    from database.database import initialize_database
    from PyQt6.QtWidgets import QApplication

    initialize_database()

    if not get_all_products():
        add_product("Produit A", "Desc A", "Cat 1", 5.0, 10.0, 20)
        add_product("Produit B", "Desc B", "Cat 2", 12.5, 25.0, 15)
    if not get_all_customers():
        add_customer("Client Test", "123 Rue Test", "0102030405", "test@example.com")

    app = QApplication(sys.argv)
    sale_widget = SaleView()
    sale_widget.show()
    sys.exit(app.exec())
