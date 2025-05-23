import os
import sys
import datetime
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QGridLayout,
    QFrame,
    QHBoxLayout,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtProperty
from PyQt6.QtGui import QFont, QColor, QPalette


try:
    import pyqtgraph as pg
    from pyqtgraph import DateAxisItem, BarGraphItem

    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    print("Warning: pyqtgraph not found. Graphs will not be displayed.")


from database.database import (
    get_db_connection,
    get_monthly_sales_trend,
    get_top_selling_products,
)


class AnimatedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 1.0

    def getOpacity(self):
        return self._opacity

    def setOpacity(self, opacity):
        self._opacity = opacity
        pass

    opacity = pyqtProperty(float, getOpacity, setOpacity)


class DashboardView(QWidget):
    def __init__(self):
        super().__init__()

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#2E2F30"))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title_label = QLabel("Tableau de Bord")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_label.setStyleSheet("color: #E0E0E0;")
        main_layout.addWidget(title_label)

        summary_grid = QGridLayout()
        summary_grid.setSpacing(20)
        main_layout.addLayout(summary_grid)

        self.total_clients_card = self._create_summary_card(
            "Clients Actifs", "0", "#3498DB"
        )
        self.total_products_card = self._create_summary_card(
            "Produits Référencés", "0", "#2ECC71"
        )
        self.total_sales_card = self._create_summary_card(
            "Ventes (Mois Actuel)", "0.00 DA", "#E74C3C"
        )
        self.low_stock_card = self._create_summary_card(
            "Stock Faible (<5)", "0", "#F39C12"
        )

        summary_grid.addWidget(self.total_clients_card, 0, 0)
        summary_grid.addWidget(self.total_products_card, 0, 1)
        summary_grid.addWidget(self.total_sales_card, 1, 0)
        summary_grid.addWidget(self.low_stock_card, 1, 1)

        for card in [
            self.total_clients_card,
            self.total_products_card,
            self.total_sales_card,
            self.low_stock_card,
        ]:
            card.setGraphicsEffect(None)

        if PYQTGRAPH_AVAILABLE:
            charts_layout = QHBoxLayout()
            charts_layout.setSpacing(20)
            main_layout.addLayout(charts_layout)

            self.sales_trend_plot = self._create_chart_widget(
                "Tendance des Ventes (12 Mois)"
            )
            charts_layout.addWidget(self.sales_trend_plot)

            self.top_products_plot = self._create_chart_widget(
                "Top 5 Produits Vendus (Quantité)"
            )
            charts_layout.addWidget(self.top_products_plot)

        else:
            no_graph_label = QLabel(
                "Bibliothèque 'pyqtgraph' non installée. Graphiques désactivés."
            )
            no_graph_label.setStyleSheet("color: yellow; font-style: italic;")
            main_layout.addWidget(no_graph_label)

        self.setLayout(main_layout)

    def _create_summary_card(self, title, value, bg_color="#343536"):

        card = QFrame()
        card.setObjectName("summaryCard")
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setFrameShadow(QFrame.Shadow.Raised)
        card.setMinimumSize(220, 120)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        card.setStyleSheet(
            f"""
            QFrame#summaryCard {{
                background-color: {bg_color};
                border-radius: 12px; 
                padding: 15px;
                color: white; 
            }}
        """
        )

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(3, 3)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(5)

        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(11)

        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_label.setStyleSheet(
            "color: #F0F0F0; border: none; background: transparent;"
        )

        value_label = QLabel(str(value))
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        value_label.setObjectName("valueLabel")
        value_label.setStyleSheet(
            "color: white; border: none; background: transparent;"
        )

        card_layout.addWidget(title_label)
        card_layout.addStretch()
        card_layout.addWidget(value_label)
        card.setLayout(card_layout)

        card.value_label = value_label

        return card

    def _create_chart_widget(self, title):

        chart_container = QFrame()
        chart_container.setObjectName("chartContainer")
        chart_container.setFrameShape(QFrame.Shape.StyledPanel)
        chart_container.setStyleSheet(
            """
            QFrame#chartContainer {
                background-color: #393A3B; 
                border-radius: 8px;
                padding: 10px;
            }
        """
        )
        chart_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        container_layout = QVBoxLayout(chart_container)
        container_layout.setContentsMargins(5, 5, 5, 5)

        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            "color: #E0E0E0; margin-bottom: 5px; border: none; background: transparent;"
        )
        container_layout.addWidget(title_label)

        if PYQTGRAPH_AVAILABLE:

            pg.setConfigOption("background", "#393A3B")
            pg.setConfigOption("foreground", "w")

            plot_widget = pg.PlotWidget()
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.getPlotItem().getViewBox().setBackgroundColor(None)
            container_layout.addWidget(plot_widget)
            chart_container.plot_widget = plot_widget
        else:
            no_graph_label = QLabel("pyqtgraph non disponible")
            no_graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_graph_label.setStyleSheet("color: #AAAAAA;")
            container_layout.addWidget(no_graph_label)
            chart_container.plot_widget = None

        chart_container.setLayout(container_layout)
        return chart_container

    def load_data(self):

        print("Loading dashboard data...")
        total_clients = 0
        total_products = 0
        total_sales_current_month = 0.0
        low_stock_count = 0
        sales_trend_data = []
        top_products_data = []

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(id) FROM Customers")
            result = cursor.fetchone()
            total_clients = result[0] if result else 0

            cursor.execute("SELECT COUNT(id) FROM Products")
            result = cursor.fetchone()
            total_products = result[0] if result else 0

            current_month = datetime.datetime.now().strftime("%Y-%m")
            cursor.execute(
                "SELECT SUM(total_amount) FROM Sales WHERE strftime('%Y-%m', sale_date) = ?",
                (current_month,),
            )
            result = cursor.fetchone()
            total_sales_current_month = (
                result[0] if result and result[0] is not None else 0.0
            )

            cursor.execute("SELECT COUNT(id) FROM Products WHERE quantity_in_stock < 5")
            result = cursor.fetchone()
            low_stock_count = result[0] if result else 0

            if PYQTGRAPH_AVAILABLE:
                sales_trend_data = get_monthly_sales_trend(limit=12)
                top_products_data = get_top_selling_products(limit=5)

            conn.close()
            print("Data fetched successfully.")

        except Exception as e:
            print(f"Error loading dashboard data: {e}")

        try:
            self.total_clients_card.value_label.setText(str(total_clients))
            self.total_products_card.value_label.setText(str(total_products))
            self.total_sales_card.value_label.setText(
                f"{total_sales_current_month:.2f} DA"
            )
            self.low_stock_card.value_label.setText(str(low_stock_count))

            if PYQTGRAPH_AVAILABLE:
                self._plot_sales_trend(sales_trend_data)
                self._plot_top_products(top_products_data)

            print("Dashboard UI updated.")

        except Exception as e:
            print(f"Error updating dashboard UI: {e}")

    def _plot_sales_trend(self, data):

        if (
            not PYQTGRAPH_AVAILABLE
            or not hasattr(self.sales_trend_plot, "plot_widget")
            or not self.sales_trend_plot.plot_widget
        ):
            return
        if not data:
            self.sales_trend_plot.plot_widget.clear()
            self.sales_trend_plot.plot_widget.addItem(
                pg.TextItem("Aucune donnée de vente disponible.", color="gray")
            )
            return

        plot_item = self.sales_trend_plot.plot_widget.getPlotItem()
        plot_item.clear()

        try:
            timestamps = [
                datetime.datetime.strptime(d[0] + "-01", "%Y-%m-%d").timestamp()
                for d in data
            ]
            values = [d[1] for d in data]
        except ValueError as e:
            print(f"Error parsing date for sales trend: {e}")
            return

        axis = DateAxisItem(orientation="bottom")
        plot_item.setAxisItems({"bottom": axis})

        plot_item.plot(
            timestamps,
            values,
            pen=pg.mkPen(color="#3498DB", width=2),
            symbol="o",
            symbolBrush="#3498DB",
            symbolSize=5,
        )
        plot_item.setTitle("Tendance des Ventes Mensuelles")
        plot_item.setLabel("left", "Montant Total (DA)")
        plot_item.setLabel("bottom", "Mois")
        plot_item.showGrid(x=True, y=True, alpha=0.3)

    def _plot_top_products(self, data):

        if (
            not PYQTGRAPH_AVAILABLE
            or not hasattr(self.top_products_plot, "plot_widget")
            or not self.top_products_plot.plot_widget
        ):
            return

        plot_item = self.top_products_plot.plot_widget.getPlotItem()
        plot_item.clear()

        if not data:
            plot_item.addItem(
                pg.TextItem("Aucune donnée de produit disponible.", color="gray")
            )
            return

        product_names = [item[0] for item in data]
        quantities = [item[1] for item in data]
        x_values = list(range(len(product_names)))

        colors = ["#2ECC71", "#3498DB", "#9B59B6", "#F1C40F", "#E74C3C"]
        brushes = [pg.mkBrush(colors[i % len(colors)]) for i in range(len(data))]

        bg = BarGraphItem(x=x_values, height=quantities, width=0.6, brushes=brushes)
        plot_item.addItem(bg)

        axis = plot_item.getAxis("bottom")
        ticks = [list(zip(x_values, product_names))]
        axis.setTicks(ticks)
        axis.setLabel("Produit")
        plot_item.setLabel("left", "Quantité Vendue")
        plot_item.setTitle("Top Produits Vendus")
        plot_item.showGrid(x=False, y=True, alpha=0.3)


if __name__ == "__main__":

    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(script_dir, "..", "database")
    sys.path.insert(0, os.path.dirname(script_dir))

    db_file_path = os.path.join(os.path.dirname(script_dir), "gestion_commerciale.db")
    if not os.path.exists(db_file_path):
        print("Database file not found. Initializing...")
        from database.database import initialize_database

        initialize_database()
    else:
        print("Database file found.")

    app = QApplication(sys.argv)

    dashboard = DashboardView()
    dashboard.show()
    dashboard.load_data()
    dashboard.resize(800, 600)

    sys.exit(app.exec())
