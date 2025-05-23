import sys  # Module système utilisé pour accéder aux arguments de la ligne de commande et quitter l'application

# Importation des composants de l'interface utilisateur de PyQt6
from PyQt6.QtWidgets import (
    QApplication,  # Classe principale de toute application PyQt
    QMainWindow,  # Fenêtre principale avec barre de menu, barre d'outils, etc.
    QLabel,  # Étiquette de texte
    QWidget,  # Conteneur de base pour les widgets
    QVBoxLayout,  # Disposition verticale des widgets
    QHBoxLayout,  # Disposition horizontale des widgets
    QListWidget,  # Liste utilisée pour la navigation entre les vues
    QStackedWidget,  # Conteneur qui empile les vues (comme des onglets sans barre d'onglet)
    QListWidgetItem,  # Élément de la liste (utilisé pour chaque entrée de navigation)
)
from PyQt6.QtCore import Qt, QSize  # Qt contient des constantes et QSize gère les dimensions
from PyQt6.QtGui import QIcon  # (Non utilisé ici, mais permettrait de mettre des icônes)

# Importation de fonctions utilitaires pour la base de données
from database.database import initialize_database, get_db_connection

# Importation des vues personnalisées (chaque vue gère un domaine de l'application)
from views.customer_view import CustomerView
from views.product_view import ProductView
from views.purchase_view import PurchaseView
from views.sale_view import SaleView
from views.stock_view import StockView
from views.dashboard_view import DashboardView

# Classe principale de la fenêtre de l'application
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()  # Appelle le constructeur de QMainWindow
        self.setWindowTitle("Gestion Commerciale et de Stock")  # Titre de la fenêtre
        self.setGeometry(100, 100, 1000, 700)  # Position et taille initiale de la fenêtre

        self.init_ui()  # Appel à la méthode qui construit l’interface utilisateur

    def init_ui(self):
        main_layout = QHBoxLayout()  # Layout horizontal principal qui contiendra la navigation + le contenu
        main_widget = QWidget()  # Création du widget principal
        main_widget.setLayout(main_layout)  # Application du layout au widget
        self.setCentralWidget(main_widget)  # Définition du widget principal comme contenu de la fenêtre

        self.nav_list = QListWidget()  # Création de la liste de navigation
        self.nav_list.setFixedWidth(180)  # Largeur fixe pour la navigation
        self.nav_list.currentRowChanged.connect(self.change_page)  # Changement de page lors de la sélection d’un élément
        main_layout.addWidget(self.nav_list)  # Ajout de la liste au layout

        self.stacked_widget = QStackedWidget()  # Widget empilé contenant les différentes vues
        main_layout.addWidget(self.stacked_widget)  # Ajout au layout principal

        # Création de chaque vue
        self.dashboard_view = DashboardView()
        self.customer_view = CustomerView()
        self.product_view = ProductView()
        self.purchase_view = PurchaseView()
        self.sale_view = SaleView()
        self.stock_view = StockView()

        # Connexion des signaux pour mettre à jour les vues dynamiques
        self.sale_view.sale_recorded.connect(self.refresh_all_views)  # Mise à jour lors d'une nouvelle vente
        self.product_view.product_updated.connect(self.refresh_all_views)  # Mise à jour lors d’un changement de produit
        self.purchase_view.purchase_recorded.connect(self.refresh_all_views)  # Mise à jour lors d’un nouvel achat
        self.customer_view.customer_updated.connect(self.refresh_customer_views)  # Mise à jour lors d’un client modifié

        # Ajout des vues au menu de navigation et au QStackedWidget
        self.add_page("Dashboard", self.dashboard_view)
        self.add_page("Clients", self.customer_view)
        self.add_page("Produits", self.product_view)
        self.add_page("Achats", self.purchase_view)
        self.add_page("Ventes", self.sale_view)
        self.add_page("Stock", self.stock_view)

        self.nav_list.setCurrentRow(0)  # Sélectionne la première vue (Dashboard) au démarrage

    def add_page(self, name, widget):
        item = QListWidgetItem(name)  # Création d’un item pour la liste de navigation
        item.setSizeHint(QSize(0, 40))  # Taille fixe en hauteur pour l’élément
        self.nav_list.addItem(item)  # Ajout à la liste de navigation
        self.stacked_widget.addWidget(widget)  # Ajout de la vue correspondante au QStackedWidget

    def change_page(self, index):
        self.stacked_widget.setCurrentIndex(index)  # Affiche la vue correspondant à l’index sélectionné
        current_widget = self.stacked_widget.widget(index)  # Récupère la vue actuelle
        self.refresh_all_views()  # Recharge les données dynamiques

    def refresh_all_views(self):
        """Actualise toutes les vues ayant des données dynamiques"""
        print("Refreshing all views...")
        if hasattr(self.dashboard_view, "load_data"):
            self.dashboard_view.load_data()  # Recharge le tableau de bord
        if hasattr(self.product_view, "load_products"):
            self.product_view.load_products()  # Recharge les produits
            self.product_view.load_categories()  # Recharge les catégories
        if hasattr(self.purchase_view, "load_products_for_combo"):
            self.purchase_view.load_products_for_combo()  # Recharge les produits dans la vue d'achat
        if hasattr(self.stock_view, "load_stock_data"):
            self.stock_view.load_stock_data()  # Recharge les données de stock
            self.stock_view.load_categories_filter()  # Recharge les filtres de catégories
        if hasattr(self.sale_view, "load_products_for_sale"):
            self.sale_view.load_products_for_sale()  # Recharge les produits dans la vue de vente
            self.sale_view.load_sales_history()  # Recharge l'historique des ventes

    def refresh_customer_views(self):
        """Actualise les vues contenant des données clients"""
        print("Refreshing customer-related views...")
        if hasattr(self.customer_view, "load_customers"):
            self.customer_view.load_customers()  # Recharge la liste des clients
        if hasattr(self.sale_view, "load_customers_for_sale"):
            self.sale_view.load_customers_for_sale()  # Recharge les clients dans la vue de vente


# Point d’entrée principal de l’application
if __name__ == "__main__":
    print("Initializing database...")  # Message de débogage
    initialize_database()  # Initialisation de la base de données (création des tables si nécessaire)
    print("Database check complete.")  # Message de confirmation

    app = QApplication(sys.argv)  # Création de l'application PyQt
    main_win = MainWindow()  # Instanciation de la fenêtre principale
    main_win.show()  # Affichage de la fenêtre
    sys.exit(app.exec())  # Lancement de la boucle événementielle (l'application tourne jusqu'à fermeture)
