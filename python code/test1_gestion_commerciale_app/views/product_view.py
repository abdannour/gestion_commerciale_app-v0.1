from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
    QDoubleSpinBox,
    QComboBox,
    QGridLayout,
)
from PyQt6.QtCore import Qt


from database.database import (
    get_all_products,
    add_product,
    update_product,
    delete_product,
    search_products,
    get_all_categories,
)


class ProductView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_product_id = None
        self.init_ui()
        self.load_products()
        self.load_categories()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("Gestion des Produits")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            "font-size: 16pt; font-weight: bold; margin-bottom: 10px;"
        )
        main_layout.addWidget(title_label)

        search_filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par nom/description...")
        self.search_input.textChanged.connect(self.filter_products)
        self.category_filter_combo = QComboBox()
        self.category_filter_combo.addItem("Toutes les catégories")
        self.category_filter_combo.currentIndexChanged.connect(self.filter_products)

        search_filter_layout.addWidget(QLabel("Rechercher:"))
        search_filter_layout.addWidget(self.search_input)
        search_filter_layout.addWidget(QLabel("Catégorie:"))
        search_filter_layout.addWidget(self.category_filter_combo)
        main_layout.addLayout(search_filter_layout)

        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)

        form_layout.addWidget(QLabel("Nom*:"), 0, 0)
        self.name_input = QLineEdit()
        form_layout.addWidget(self.name_input, 0, 1)

        form_layout.addWidget(QLabel("Catégorie:"), 0, 2)
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Nouvelle ou existante")
        form_layout.addWidget(self.category_input, 0, 3)

        form_layout.addWidget(QLabel("Description:"), 1, 0)
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(60)
        form_layout.addWidget(self.description_input, 1, 1, 1, 3)

        form_layout.addWidget(QLabel("Prix d'achat*:"), 2, 0)
        self.purchase_price_input = QDoubleSpinBox()
        self.purchase_price_input.setRange(0.0, 999999.99)
        self.purchase_price_input.setDecimals(2)
        self.purchase_price_input.setSuffix(" €")
        form_layout.addWidget(self.purchase_price_input, 2, 1)

        form_layout.addWidget(QLabel("Prix de vente*:"), 2, 2)
        self.selling_price_input = QDoubleSpinBox()
        self.selling_price_input.setRange(0.0, 999999.99)
        self.selling_price_input.setDecimals(2)
        self.selling_price_input.setSuffix(" €")
        form_layout.addWidget(self.selling_price_input, 2, 3)

        main_layout.addWidget(form_widget)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Ajouter Produit")
        self.add_button.clicked.connect(self.add_new_product)
        self.update_button = QPushButton("Modifier Produit")
        self.update_button.clicked.connect(self.update_selected_product)
        self.update_button.setEnabled(False)
        self.delete_button = QPushButton("Supprimer Produit")
        self.delete_button.clicked.connect(self.delete_selected_product)
        self.delete_button.setEnabled(False)
        self.clear_button = QPushButton("Effacer Formulaire")
        self.clear_button.clicked.connect(self.clear_form)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)

        self.product_table = QTableWidget()
        self.product_table.setColumnCount(7)
        self.product_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Nom",
                "Catégorie",
                "Description",
                "Prix Achat",
                "Prix Vente",
                "Stock",
            ]
        )
        self.product_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.product_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.product_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.product_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.product_table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.ResizeToContents
        )
        self.product_table.setColumnHidden(3, True)
        self.product_table.itemSelectionChanged.connect(self.on_row_selected)

        main_layout.addWidget(self.product_table)
        self.setLayout(main_layout)

    def load_categories(self):
        """Loads unique categories into the filter dropdown."""
        current_filter = self.category_filter_combo.currentText()
        self.category_filter_combo.blockSignals(True)
        self.category_filter_combo.clear()
        self.category_filter_combo.addItem("Toutes les catégories")
        try:
            categories = get_all_categories()
            self.category_filter_combo.addItems(categories)

            index = self.category_filter_combo.findText(current_filter)
            if index != -1:
                self.category_filter_combo.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.warning(
                self, "Erreur Catégories", f"Impossible de charger les catégories: {e}"
            )
        finally:
            self.category_filter_combo.blockSignals(False)

    def load_products(self, products_data=None):
        """Loads product data into the table. If data is provided, uses it; otherwise, fetches all."""
        self.product_table.setRowCount(0)
        try:
            if products_data is None:
                products_data = get_all_products()

            if products_data:
                self.product_table.setRowCount(len(products_data))
                for row_idx, product in enumerate(products_data):
                    self.product_table.setItem(
                        row_idx, 0, QTableWidgetItem(str(product["id"]))
                    )
                    self.product_table.setItem(
                        row_idx, 1, QTableWidgetItem(product["name"])
                    )
                    self.product_table.setItem(
                        row_idx, 2, QTableWidgetItem(product["category"] or "")
                    )
                    self.product_table.setItem(
                        row_idx, 3, QTableWidgetItem(product["description"] or "")
                    )
                    self.product_table.setItem(
                        row_idx,
                        4,
                        QTableWidgetItem(f"{product['purchase_price']:.2f} €"),
                    )
                    self.product_table.setItem(
                        row_idx,
                        5,
                        QTableWidgetItem(f"{product['selling_price']:.2f} €"),
                    )
                    self.product_table.setItem(
                        row_idx, 6, QTableWidgetItem(str(product["quantity_in_stock"]))
                    )

                    if product["quantity_in_stock"] <= 5:
                        for col in range(7):
                            item = self.product_table.item(row_idx, col)
                            if item:
                                item.setBackground(Qt.GlobalColor.transparent)

        except Exception as e:
            QMessageBox.critical(
                self, "Erreur", f"Erreur lors du chargement des produits: {e}"
            )

    def filter_products(self):
        """Filters products based on search query and category selection."""
        search_query = self.search_input.text().strip()
        category_filter = self.category_filter_combo.currentText()
        if category_filter == "Toutes les catégories":
            category_filter = None

        try:
            filtered_data = search_products(search_query, category_filter)
            self.load_products(filtered_data)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur Recherche",
                f"Erreur lors de la recherche de produits: {e}",
            )

    def on_row_selected(self):
        """Populates the form when a table row is selected."""
        selected_items = self.product_table.selectedItems()
        if selected_items:
            selected_row = self.product_table.currentRow()
            self.current_product_id = int(
                self.product_table.item(selected_row, 0).text()
            )

            self.name_input.setText(self.product_table.item(selected_row, 1).text())
            self.category_input.setText(self.product_table.item(selected_row, 2).text())
            self.description_input.setText(
                self.product_table.item(selected_row, 3).text()
            )

            try:
                purchase_price_str = (
                    self.product_table.item(selected_row, 4)
                    .text()
                    .replace(" €", "")
                    .replace(",", ".")
                )
                selling_price_str = (
                    self.product_table.item(selected_row, 5)
                    .text()
                    .replace(" €", "")
                    .replace(",", ".")
                )
                self.purchase_price_input.setValue(float(purchase_price_str))
                self.selling_price_input.setValue(float(selling_price_str))
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Erreur Format Prix",
                    "Impossible de lire les prix du produit sélectionné.",
                )
                self.purchase_price_input.setValue(0.0)
                self.selling_price_input.setValue(0.0)

            self.update_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.add_button.setEnabled(False)
        else:
            self.clear_form()

    def clear_form(self):
        """Clears the input fields and resets selection state."""
        self.current_product_id = None
        self.name_input.clear()
        self.description_input.clear()
        self.category_input.clear()
        self.purchase_price_input.setValue(0.0)
        self.selling_price_input.setValue(0.0)
        self.product_table.clearSelection()
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.add_button.setEnabled(True)

    def add_new_product(self):
        """Adds a product using data from the form."""
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip() or None
        category = self.category_input.text().strip() or None
        purchase_price = self.purchase_price_input.value()
        selling_price = self.selling_price_input.value()

        if not name or purchase_price < 0 or selling_price < 0:
            QMessageBox.warning(
                self,
                "Attention",
                "Le nom, prix d'achat et prix de vente sont obligatoires et doivent être positifs.",
            )
            return

        new_id = add_product(name, description, category, purchase_price, selling_price)
        if new_id:
            QMessageBox.information(
                self, "Succès", f"Produit '{name}' ajouté avec succès."
            )
            self.load_products()
            self.load_categories()
            self.clear_form()
        else:
            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible d'ajouter le produit (vérifiez si le nom existe déjà).",
            )

    def update_selected_product(self):
        """Updates the selected product using data from the form."""
        if self.current_product_id is None:
            return

        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip() or None
        category = self.category_input.text().strip() or None
        purchase_price = self.purchase_price_input.value()
        selling_price = self.selling_price_input.value()

        if not name or purchase_price < 0 or selling_price < 0:
            QMessageBox.warning(
                self,
                "Attention",
                "Le nom, prix d'achat et prix de vente sont obligatoires et doivent être positifs.",
            )
            return

        success = update_product(
            self.current_product_id,
            name,
            description,
            category,
            purchase_price,
            selling_price,
        )
        if success:
            QMessageBox.information(
                self, "Succès", f"Produit ID {self.current_product_id} mis à jour."
            )
            self.load_products()
            self.load_categories()
            self.clear_form()
        else:
            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible de mettre à jour le produit (vérifiez si le nom existe déjà pour un autre produit).",
            )

    def delete_selected_product(self):
        """Deletes the product selected in the table."""
        if self.current_product_id is None:
            return

        product_name = self.name_input.text()
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer le produit '{product_name}' (ID: {self.current_product_id})?\n"
            f"Attention: La suppression échouera si des ventes sont associées à ce produit.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = delete_product(self.current_product_id)
            if success:
                QMessageBox.information(
                    self, "Succès", f"Produit '{product_name}' supprimé."
                )
                self.load_products()
                self.load_categories()
                self.clear_form()
            else:

                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Impossible de supprimer le produit '{product_name}'.\nIl est probable qu'il soit utilisé dans des enregistrements de ventes.",
                )


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    from database.database import initialize_database

    initialize_database()
    app = QApplication(sys.argv)
    product_widget = ProductView()
    product_widget.show()
    sys.exit(app.exec())
