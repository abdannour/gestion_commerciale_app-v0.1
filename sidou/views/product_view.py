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
from PyQt6.QtCore import Qt, pyqtSignal


from database.database import (
    get_all_products,
    add_product,
    update_product,
    delete_product,
    search_products,
    get_all_categories,
)


class ProductView(QWidget):
    # Signal for product updates
    product_updated = pyqtSignal()

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
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.setInsertPolicy(QComboBox.InsertPolicy.InsertAtBottom)
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
        self.purchase_price_input.setSuffix(" DA")
        form_layout.addWidget(self.purchase_price_input, 2, 1)

        form_layout.addWidget(QLabel("Prix de vente*:"), 2, 2)
        self.selling_price_input = QDoubleSpinBox()
        self.selling_price_input.setRange(0.0, 999999.99)
        self.selling_price_input.setDecimals(2)
        self.selling_price_input.setSuffix(" DA")
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
        """Loads unique categories into the filter dropdown and category input."""
        current_filter = self.category_filter_combo.currentText()
        current_input = self.category_input.currentText() if self.category_input.currentText() else ""
        
        # Block signals to prevent unnecessary updates
        self.category_filter_combo.blockSignals(True)
        self.category_input.blockSignals(True)
        
        # Clear both combo boxes
        self.category_filter_combo.clear()
        self.category_input.clear()
        
        # Add default item to filter combo
        self.category_filter_combo.addItem("Toutes les catégories")
        
        try:
            categories = get_all_categories()
            # Add categories to both combo boxes
            self.category_filter_combo.addItems(categories)
            self.category_input.addItems(categories)
            
            # Restore previous selections if they exist
            filter_index = self.category_filter_combo.findText(current_filter)
            if filter_index != -1:
                self.category_filter_combo.setCurrentIndex(filter_index)
                
            input_index = self.category_input.findText(current_input)
            if input_index != -1:
                self.category_input.setCurrentIndex(input_index)
            elif current_input:
                self.category_input.setCurrentText(current_input)
                
        except Exception as e:
            QMessageBox.warning(
                self, "Erreur Catégories", f"Impossible de charger les catégories: {e}"
            )
        finally:
            self.category_filter_combo.blockSignals(False)
            self.category_input.blockSignals(False)

    def load_products(self, products_data=None):
        """Loads product data into the table. If data is provided, uses it; otherwise, fetches all."""
        self.product_table.setRowCount(0)
        try:
            if products_data is None:
                products_data = get_all_products()

            if products_data:
                self.product_table.setRowCount(len(products_data))
                for row_idx, product in enumerate(products_data):
                    # ID
                    self.product_table.setItem(
                        row_idx, 0, QTableWidgetItem(str(product["id"]))
                    )
                    # Nom
                    self.product_table.setItem(
                        row_idx, 1, QTableWidgetItem(product["name"])
                    )
                    # Catégorie
                    self.product_table.setItem(
                        row_idx, 2, QTableWidgetItem(product["category"] or "")
                    )
                    # Description
                    self.product_table.setItem(
                        row_idx, 3, QTableWidgetItem(product["description"] or "")
                    )
                    # Prix d'achat
                    self.product_table.setItem(
                        row_idx,
                        4,
                        QTableWidgetItem(f"{product['purchase_price']:.2f} DA"),
                    )
                    # Prix de vente
                    self.product_table.setItem(
                        row_idx,
                        5,
                        QTableWidgetItem(f"{product['selling_price']:.2f} DA"),
                    )
                    # Stock
                    stock_item = QTableWidgetItem(str(product["quantity_in_stock"]))
                    self.product_table.setItem(row_idx, 6, stock_item)

                    # Coloration des lignes selon le stock
                    if product["quantity_in_stock"] == 0:
                        color = Qt.GlobalColor.red
                    elif product["quantity_in_stock"] <= 5:
                        color = Qt.GlobalColor.yellow
                    else:
                        color = Qt.GlobalColor.white

                    for col in range(7):
                        item = self.product_table.item(row_idx, col)
                        if item:
                            item.setBackground(color)

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
            
            try:
                # Get values from the table
                product_id = self.product_table.item(selected_row, 0).text()  # ID
                name = self.product_table.item(selected_row, 1).text()  # Name
                category = self.product_table.item(selected_row, 2).text()  # Category
                description = self.product_table.item(selected_row, 3).text()  # Description
                purchase_price = self.product_table.item(selected_row, 4).text()  # Purchase Price
                selling_price = self.product_table.item(selected_row, 5).text()  # Selling Price

                # Set the values in the form
                self.current_product_id = int(product_id)
                self.name_input.setText(name)
                self.category_input.setCurrentText(category)
                self.description_input.setText(description)

                # Process the prices
                purchase_price_str = purchase_price.replace(" DA", "").replace(",", ".")
                selling_price_str = selling_price.replace(" DA", "").replace(",", ".")
                self.purchase_price_input.setValue(float(purchase_price_str))
                self.selling_price_input.setValue(float(selling_price_str))

                self.update_button.setEnabled(True)
                self.delete_button.setEnabled(True)
                self.add_button.setEnabled(False)
            except (ValueError, AttributeError) as e:
                QMessageBox.warning(
                    self,
                    "Erreur de Données",
                    "Impossible de lire les données du produit sélectionné."
                )
                self.clear_form()
        else:
            self.clear_form()

    def clear_form(self):
        """Clears the input fields and resets selection state."""
        self.current_product_id = None
        self.name_input.clear()
        self.description_input.clear()
        self.category_input.setCurrentText("")
        self.purchase_price_input.setValue(0.0)
        self.selling_price_input.setValue(0.0)
        self.product_table.clearSelection()
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.add_button.setEnabled(True)

    def add_new_product(self):
        """Adds a new product to the database."""
        # Récupération des valeurs
        name = self.name_input.text().strip()
        category = self.category_input.currentText().strip()
        description = self.description_input.toPlainText().strip()
        purchase_price = self.purchase_price_input.value()
        selling_price = self.selling_price_input.value()

        # Validation des données
        if not name:
            QMessageBox.warning(self, "Attention", "Le nom du produit est obligatoire.")
            self.name_input.setFocus()
            return

        if selling_price < purchase_price:
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "Le prix de vente est inférieur au prix d'achat. Voulez-vous continuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        try:
            # Ajout du produit
            product_id = add_product(
                name=name,
                category=category,
                description=description,
                purchase_price=purchase_price,
                selling_price=selling_price,
                initial_stock=0
            )

            if product_id:
                self.clear_form()
                self.load_products()
                self.load_categories()
                self.product_updated.emit()
                QMessageBox.information(
                    self, "Succès", "Le produit a été ajouté avec succès."
                )
            else:
                QMessageBox.critical(
                    self, "Erreur", "Impossible d'ajouter le produit. Vérifiez que le nom n'existe pas déjà."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur", f"Erreur lors de l'ajout du produit: {e}"
            )

    def update_selected_product(self):
        """Updates the selected product in the database."""
        if not self.current_product_id:
            QMessageBox.warning(
                self, "Attention", "Veuillez sélectionner un produit à modifier."
            )
            return

        # Récupération des valeurs
        name = self.name_input.text().strip()
        category = self.category_input.currentText().strip()
        description = self.description_input.toPlainText().strip()
        purchase_price = self.purchase_price_input.value()
        selling_price = self.selling_price_input.value()

        # Validation des données
        if not name:
            QMessageBox.warning(self, "Attention", "Le nom du produit est obligatoire.")
            self.name_input.setFocus()
            return

        if selling_price < purchase_price:
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "Le prix de vente est inférieur au prix d'achat. Voulez-vous continuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        try:
            success = update_product(
                product_id=self.current_product_id,
                name=name,
                category=category,
                description=description,
                purchase_price=purchase_price,
                selling_price=selling_price
            )

            if success:
                self.load_products()
                self.load_categories()
                self.product_updated.emit()
                QMessageBox.information(
                    self, "Succès", "Le produit a été modifié avec succès."
                )
            else:
                QMessageBox.critical(
                    self, "Erreur", "Impossible de modifier le produit. Vérifiez que le nom n'existe pas déjà."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur", f"Erreur lors de la modification du produit: {e}"
            )

    def delete_selected_product(self):
        """Deletes the selected product from the database."""
        if not self.current_product_id:
            QMessageBox.warning(
                self, "Attention", "Veuillez sélectionner un produit à supprimer."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir supprimer ce produit ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_product(self.current_product_id)
                self.clear_form()
                self.load_products()
                self.load_categories()
                self.product_updated.emit()  # Emit signal when product is deleted
                QMessageBox.information(
                    self, "Succès", "Le produit a été supprimé avec succès."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Erreur", f"Erreur lors de la suppression du produit: {e}"
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
