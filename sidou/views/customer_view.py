import datetime
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
    QDialog,
    QDialogButtonBox,
    QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal


from database.database import (
    get_all_customers,
    add_customer,
    update_customer,
    delete_customer,
    get_sales_by_customer,
    get_sale_items,
)


class CustomerView(QWidget):
    # Signal for customer updates
    customer_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_customer_id = None
        self.init_ui()
        self.load_customers()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("Gestion des Clients")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            "font-size: 16pt; font-weight: bold; margin-bottom: 10px;"
        )
        main_layout.addWidget(title_label)

        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nom du client*")
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Adresse")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Téléphone")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")

        form_layout.addWidget(QLabel("Nom:"))
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(QLabel("Adresse:"))
        form_layout.addWidget(self.address_input)
        form_layout.addWidget(QLabel("Tél:"))
        form_layout.addWidget(self.phone_input)
        form_layout.addWidget(QLabel("Email:"))
        form_layout.addWidget(self.email_input)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Ajouter")
        self.add_button.clicked.connect(self.add_new_customer)
        self.update_button = QPushButton("Modifier")
        self.update_button.clicked.connect(self.update_selected_customer)
        self.update_button.setEnabled(False)
        self.delete_button = QPushButton("Supprimer")
        self.delete_button.clicked.connect(self.delete_selected_customer)
        self.delete_button.setEnabled(False)
        self.history_button = QPushButton("Voir Historique Achats")
        self.history_button.clicked.connect(self.show_customer_history)
        self.history_button.setEnabled(False)
        self.clear_button = QPushButton("Effacer Formulaire")
        self.clear_button.clicked.connect(self.clear_form)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.history_button)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)

        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(5)
        self.customer_table.setHorizontalHeaderLabels(
            ["ID", "Nom", "Adresse", "Téléphone", "Email"]
        )
        self.customer_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.customer_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.customer_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.customer_table.verticalHeader().setVisible(False)
        self.customer_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.customer_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.customer_table.itemSelectionChanged.connect(self.on_row_selected)

        main_layout.addWidget(self.customer_table)

        self.setLayout(main_layout)

    def load_customers(self):
        """Loads customer data from the database into the table."""
        self.customer_table.setRowCount(0)
        try:
            customers = get_all_customers()
            if customers:
                self.customer_table.setRowCount(len(customers))
                for row_idx, customer in enumerate(customers):
                    self.customer_table.setItem(
                        row_idx, 0, QTableWidgetItem(str(customer["id"]))
                    )
                    self.customer_table.setItem(
                        row_idx, 1, QTableWidgetItem(customer["name"])
                    )
                    self.customer_table.setItem(
                        row_idx, 2, QTableWidgetItem(customer["address"] or "")
                    )
                    self.customer_table.setItem(
                        row_idx, 3, QTableWidgetItem(customer["phone"] or "")
                    )
                    self.customer_table.setItem(
                        row_idx, 4, QTableWidgetItem(customer["email"] or "")
                    )
            self.clear_form()
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur", f"Erreur lors du chargement des clients: {e}"
            )

    def on_row_selected(self):
        """Handles actions when a table row is selected."""
        selected_items = self.customer_table.selectedItems()
        if selected_items:
            selected_row = self.customer_table.currentRow()
            self.current_customer_id = int(
                self.customer_table.item(selected_row, 0).text()
            )
            self.name_input.setText(self.customer_table.item(selected_row, 1).text())
            self.address_input.setText(self.customer_table.item(selected_row, 2).text())
            self.phone_input.setText(self.customer_table.item(selected_row, 3).text())
            self.email_input.setText(self.customer_table.item(selected_row, 4).text())
            self.update_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.history_button.setEnabled(True)
            self.add_button.setEnabled(False)
        else:
            self.clear_form()

    def clear_form(self):
        """Clears the input fields and resets selection state."""
        self.current_customer_id = None
        self.name_input.clear()
        self.address_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        self.customer_table.clearSelection()
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.history_button.setEnabled(False)
        self.add_button.setEnabled(True)

    def add_new_customer(self):
        """Adds a new customer to the database."""
        name = self.name_input.text().strip()
        address = self.address_input.text().strip() or None
        phone = self.phone_input.text().strip() or None
        email = self.email_input.text().strip() or None

        if not name:
            QMessageBox.warning(self, "Attention", "Le nom du client est obligatoire.")
            return

        try:
            add_customer(name, address, phone, email)
            self.clear_form()
            self.load_customers()
            self.customer_updated.emit()  # Emit signal when customer is added
            QMessageBox.information(
                self, "Succès", "Le client a été ajouté avec succès."
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur", f"Erreur lors de l'ajout du client: {e}"
            )

    def update_selected_customer(self):
        """Updates the selected customer in the database."""
        if not self.current_customer_id:
            QMessageBox.warning(
                self, "Attention", "Veuillez sélectionner un client à modifier."
            )
            return

        name = self.name_input.text().strip()
        address = self.address_input.text().strip() or None
        phone = self.phone_input.text().strip() or None
        email = self.email_input.text().strip() or None

        if not name:
            QMessageBox.warning(self, "Attention", "Le nom du client est obligatoire.")
            return

        try:
            update_customer(self.current_customer_id, name, address, phone, email)
            self.load_customers()
            self.customer_updated.emit()  # Emit signal when customer is updated
            QMessageBox.information(
                self, "Succès", "Le client a été modifié avec succès."
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur", f"Erreur lors de la modification du client: {e}"
            )

    def delete_selected_customer(self):
        """Deletes the selected customer from the database."""
        if not self.current_customer_id:
            QMessageBox.warning(
                self, "Attention", "Veuillez sélectionner un client à supprimer."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir supprimer ce client ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_customer(self.current_customer_id)
                self.clear_form()
                self.load_customers()
                self.customer_updated.emit()  # Emit signal when customer is deleted
                QMessageBox.information(
                    self, "Succès", "Le client a été supprimé avec succès."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Erreur", f"Erreur lors de la suppression du client: {e}"
                )

    def show_customer_history(self):
        """Shows a dialog with the purchase history for the selected customer."""
        if self.current_customer_id is None:
            QMessageBox.warning(
                self,
                "Aucun Client Sélectionné",
                "Veuillez sélectionner un client dans la table.",
            )
            return

        customer_name = self.name_input.text()
        try:
            sales_history = get_sales_by_customer(self.current_customer_id)
            dialog = CustomerHistoryDialog(
                self.current_customer_id, customer_name, sales_history, self
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur Historique Client",
                f"Impossible de charger l'historique: {e}",
            )


class CustomerHistoryDialog(QDialog):
    def __init__(self, customer_id, customer_name, sales_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(
            f"Historique des Achats - {customer_name} (ID: {customer_id})"
        )
        self.setMinimumWidth(600)
        self.selected_sale_id = None

        layout = QVBoxLayout(self)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(
            ["ID Vente", "Date", "Montant Total"]
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
        self.history_table.doubleClicked.connect(self.show_sale_details)
        self.history_table.itemSelectionChanged.connect(self.on_row_selected)

        layout.addWidget(QLabel(f"Historique pour {customer_name}:"))
        layout.addWidget(self.history_table)

        self.populate_table(sales_data)

        self.details_button = QPushButton("Voir Détails Vente Sélectionnée")
        self.details_button.setEnabled(False)
        self.details_button.clicked.connect(self.show_sale_details)

        button_box = QDialogButtonBox()
        button_box.addButton(
            self.details_button, QDialogButtonBox.ButtonRole.ActionRole
        )
        button_box.addButton(QDialogButtonBox.StandardButton.Ok)

        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def populate_table(self, sales_data):
        self.history_table.setRowCount(0)
        if sales_data:
            self.history_table.setRowCount(len(sales_data))
            for row_idx, sale in enumerate(sales_data):
                self.history_table.setItem(
                    row_idx, 0, QTableWidgetItem(str(sale["id"]))
                )

                date_str = sale["sale_date"]
                try:
                    dt_obj = datetime.datetime.fromisoformat(date_str)
                    display_date = dt_obj.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    display_date = date_str
                self.history_table.setItem(row_idx, 1, QTableWidgetItem(display_date))
                self.history_table.setItem(
                    row_idx, 2, QTableWidgetItem(f"{sale['total_amount']:.2f} €")
                )

    def on_row_selected(self):
        selected_items = self.history_table.selectedItems()
        if selected_items:
            selected_row = self.history_table.currentRow()
            self.selected_sale_id = int(self.history_table.item(selected_row, 0).text())
            self.details_button.setEnabled(True)
        else:
            self.selected_sale_id = None
            self.details_button.setEnabled(False)

    def show_sale_details(self):
        """Shows the details of the selected sale."""
        if self.selected_sale_id is None:

            selected_items = self.history_table.selectedItems()
            if not selected_items:
                return
            selected_row = self.history_table.currentRow()
            self.selected_sale_id = int(self.history_table.item(selected_row, 0).text())

        if self.selected_sale_id is not None:
            try:

                items = get_sale_items(self.selected_sale_id)

                from views.sale_view import SaleDetailsDialog

                details_dialog = SaleDetailsDialog(self.selected_sale_id, items, self)
                details_dialog.exec()
            except ImportError:
                QMessageBox.critical(
                    self, "Erreur Import", "Impossible d'importer SaleDetailsDialog."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur Détails Vente",
                    f"Impossible de charger les détails: {e}",
                )


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    from database.database import initialize_database

    initialize_database()

    app = QApplication(sys.argv)
    customer_widget = CustomerView()
    customer_widget.show()
    sys.exit(app.exec())
