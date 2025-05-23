# Import des modules système et de date/heure
import sys
import datetime

# Importation des composants nécessaires depuis PyQt6
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

# Importation des constantes et signaux depuis QtCore
from PyQt6.QtCore import Qt, pyqtSignal

# Import des fonctions liées à la base de données personnalisée
from database.database import (
    add_purchase,            # Fonction pour ajouter un achat
    get_purchase_history,    # Fonction pour récupérer l'historique des achats
    get_all_products,        # Fonction pour récupérer tous les produits
    add_product,             # Fonction pour ajouter un produit
    get_product_by_id,       # Fonction pour récupérer un produit par son ID
)

# Déclaration de la classe PurchaseView, qui hérite de QWidget
class PurchaseView(QWidget):
    # Déclaration d'un signal émis lorsqu'un achat est enregistré
    purchase_recorded = pyqtSignal()

    def __init__(self):
        super().__init__()  # Appel au constructeur parent QWidget
        self.products_data = {}  # Dictionnaire pour stocker les produits (nom -> id)
        self.init_ui()  # Initialiser l'interface graphique
        self.load_products_for_combo()  # Charger les produits dans la comboBox
        self.load_purchase_history()  # Charger l'historique des achats

    def init_ui(self):
        main_layout = QVBoxLayout(self)  # Layout vertical principal

        title_label = QLabel("Enregistrer un Achat Fournisseur")  # Titre principal
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centrer le texte
        title_label.setStyleSheet(
            "font-size: 16pt; font-weight: bold; margin-bottom: 10px;"  # Style CSS
        )
        main_layout.addWidget(title_label)  # Ajout du titre au layout

        form_widget = QWidget()  # Création du widget contenant le formulaire
        form_layout = QGridLayout(form_widget)  # Disposition en grille

        form_layout.addWidget(QLabel("Produit*:"), 0, 0)  # Label produit
        self.product_combo = QComboBox()  # ComboBox pour les produits
        form_layout.addWidget(self.product_combo, 0, 1)  # Ajout au layout

        form_layout.addWidget(QLabel("Quantité*:"), 0, 2)  # Label quantité
        self.quantity_spinbox = QSpinBox()  # SpinBox pour quantité
        self.quantity_spinbox.setRange(1, 99999)  # Valeur minimale et maximale
        form_layout.addWidget(self.quantity_spinbox, 0, 3)  # Ajout au layout

        form_layout.addWidget(QLabel("Coût Unitaire*:"), 1, 0)  # Label coût
        self.cost_spinbox = QDoubleSpinBox()  # SpinBox décimale pour le coût
        self.cost_spinbox.setRange(0.0, 999999.99)  # Limites
        self.cost_spinbox.setDecimals(2)  # 2 chiffres après la virgule
        self.cost_spinbox.setSuffix(" €")  # Suffixe €
        form_layout.addWidget(self.cost_spinbox, 1, 1)  # Ajout au layout

        form_layout.addWidget(QLabel("Fournisseur:"), 1, 2)  # Label fournisseur
        self.supplier_input = QLineEdit()  # Champ texte fournisseur
        self.supplier_input.setPlaceholderText("(Optionnel)")  # Texte grisé
        form_layout.addWidget(self.supplier_input, 1, 3)  # Ajout au layout

        self.add_purchase_button = QPushButton("Enregistrer l'Achat")  # Bouton
        self.add_purchase_button.clicked.connect(self.add_new_purchase)  # Connexion au slot
        form_layout.addWidget(self.add_purchase_button, 2, 0, 1, 4)  # Ajout (sur 4 colonnes)

        main_layout.addWidget(form_widget)  # Ajout du formulaire au layout principal

        main_layout.addSpacerItem(
            QSpacerItem(
                20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )  # Espacement vertical
        )

        history_title = QLabel("Historique des Achats Récents")  # Titre historique
        history_title.setStyleSheet(
            "font-size: 14pt; font-weight: bold; margin-top: 15px;"
        )  # Style
        main_layout.addWidget(history_title)  # Ajout du titre

        self.history_table = QTableWidget()  # Table pour afficher les achats
        self.history_table.setColumnCount(6)  # Nombre de colonnes
        self.history_table.setHorizontalHeaderLabels(
            ["ID Achat", "Date", "Produit", "Quantité", "Coût Unit.", "Fournisseur"]
        )  # En-têtes
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Non éditable
        self.history_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )  # Sélection ligne entière
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)  # Pas de sélection
        self.history_table.verticalHeader().setVisible(False)  # Cacher l'en-tête vertical
        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )  # Étirement des colonnes
        self.history_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )  # Colonne 0: auto-ajustement
        self.history_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )  # Colonne 1: auto-ajustement

        main_layout.addWidget(self.history_table)  # Ajout de la table au layout

        self.refresh_button = QPushButton("Rafraîchir l'Historique")  # Bouton refresh
        self.refresh_button.clicked.connect(self.load_purchase_history)  # Action
        refresh_layout = QHBoxLayout()  # Layout horizontal
        refresh_layout.addStretch()  # Espacement à gauche
        refresh_layout.addWidget(self.refresh_button)  # Ajout du bouton
        main_layout.addLayout(refresh_layout)  # Ajout au layout principal

        self.setLayout(main_layout)  # Appliquer le layout à la fenêtre

    def load_products_for_combo(self):
        """Charge les produits dans la comboBox"""
        self.product_combo.clear()  # Vider la comboBox
        self.products_data.clear()  # Vider le dictionnaire
        self.product_combo.addItem("Sélectionner un produit...", -1)  # Élément par défaut
        try:
            products = get_all_products()  # Récupérer produits depuis DB
            if products:
                for product in products:
                    display_text = (
                        f"{product['name']} (Stock: {product['quantity_in_stock']})"
                    )  # Texte affiché
                    self.product_combo.addItem(display_text, product["id"])  # Ajout à la comboBox
                    self.products_data[display_text] = product["id"]  # Stockage dans dictionnaire
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur Produits",
                f"Impossible de charger la liste des produits: {e}",  # Affichage de l'erreur
            )

    def load_purchase_history(self):
        """Charge l'historique des achats dans la table"""
        self.history_table.setRowCount(0)  # Vider la table
        try:
            history = get_purchase_history()  # Récupérer l'historique
            if history:
                self.history_table.setRowCount(len(history))  # Définir nombre de lignes
                for row_idx, purchase in enumerate(history):  # Pour chaque achat
                    self.history_table.setItem(
                        row_idx, 0, QTableWidgetItem(str(purchase["id"]))
                    )  # ID

                    date_str = purchase["purchase_date"]  # Date au format string
                    try:
                        dt_obj = datetime.datetime.fromisoformat(date_str)  # Convertir
                        display_date = dt_obj.strftime("%Y-%m-%d %H:%M")  # Reformater
                    except ValueError:
                        display_date = date_str  # Si erreur, afficher brut
                    self.history_table.setItem(
                        row_idx, 1, QTableWidgetItem(display_date)
                    )  # Date

                    self.history_table.setItem(
                        row_idx, 2, QTableWidgetItem(purchase["product_name"])
                    )  # Produit
                    self.history_table.setItem(
                        row_idx, 3, QTableWidgetItem(str(purchase["quantity"]))
                    )  # Quantité
                    self.history_table.setItem(
                        row_idx,
                        4,
                        QTableWidgetItem(f"{purchase['cost_per_unit']:.2f} €"),
                    )  # Coût
                    self.history_table.setItem(
                        row_idx, 5, QTableWidgetItem(purchase["supplier"] or "")
                    )  # Fournisseur
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur Historique",
                f"Impossible de charger l'historique des achats: {e}",  # Affichage erreur
            )

    def add_new_purchase(self):
        """Enregistre un nouvel achat"""
        selected_index = self.product_combo.currentIndex()
        if selected_index <= 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un produit.")
            return

        product_id = self.product_combo.itemData(selected_index)  # ID du produit
        quantity = self.quantity_spinbox.value()  # Quantité choisie
        cost = self.cost_spinbox.value()  # Coût unitaire
        supplier = self.supplier_input.text().strip() or None  # Fournisseur (optionnel)

        if quantity <= 0 or cost < 0:
            QMessageBox.warning(
                self,
                "Attention",
                "La quantité doit être positive et le coût doit être positif ou nul.",
            )
            return

        new_purchase_id = add_purchase(product_id, quantity, cost, supplier)  # Ajout à la base

        if new_purchase_id:
            QMessageBox.information(
                self, "Succès", f"Achat pour le produit ID {product_id} enregistré."
            )

            self.load_purchase_history()  # Rafraîchir l'historique
            self.load_products_for_combo()  # Mettre à jour les stocks

            # Réinitialiser le formulaire
            self.product_combo.setCurrentIndex(0)
            self.quantity_spinbox.setValue(1)
            self.cost_spinbox.setValue(0.0)
            self.supplier_input.clear()

            self.purchase_recorded.emit()  # Émettre le signal
        else:
            QMessageBox.critical(self, "Erreur", "Impossible d'enregistrer l'achat.")

# Point d'entrée principal
if __name__ == "__main__":
    from database.database import initialize_database

    initialize_database()  # Crée les tables si besoin

    if not get_all_products():  # Si aucun produit, ajouter un produit test
        add_product("Produit Test", "Description Test", "Cat Test", 10.0, 20.0, 5)

    app = QApplication(sys.argv)  # Création de l'application
    purchase_widget = PurchaseView()  # Instanciation de la vue
    purchase_widget.show()  # Affichage de la fenêtre
    sys.exit(app.exec())  # Lancement de la boucle événementielle
