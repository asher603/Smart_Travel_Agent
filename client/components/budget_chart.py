from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice, QLegend, QLegendMarker
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt, QMargins
from PySide6.QtWidgets import QToolTip, QSizePolicy

class BudgetPieChart(QChartView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Chart Setup
        self.chart = QChart()
        # Remove whitespace margins so chart fills the card
        self.chart.setMargins(QMargins(0, 0, 0, 0))
        self.chart.layout().setContentsMargins(0, 0, 0, 0)
        self.chart.setBackgroundVisible(False)
        
        # Legend Setup
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignRight)
        self.chart.legend().setFont(QFont("Segoe UI", 9))
        self.chart.legend().setMarkerShape(QLegend.MarkerShape.MarkerShapeCircle)
        
        # Series Setup
        self.series = QPieSeries()
        self.series.setHoleSize(0.0) # Full pie
        self.series.setPieSize(0.9)  # Use 90% of available rect
        self.series.hovered.connect(self.on_slice_hover)
        
        self.chart.addSeries(self.series)
        self.setChart(self.chart)

    def update_data(self, data: dict):
        self.series.clear()
        total = sum(data.values())
        if total == 0: return

        colors = ["#5e35b1", "#1e88e5", "#00897b", "#fdd835", "#e53935", "#8e24aa"]
        category_names = []

        # 1. Create Slices
        for i, (category, amount) in enumerate(data.items()):
            category_names.append(category) # Store name for legend fix later
            
            # Slice Label = Money Amount
            slice_obj = self.series.append(f"${amount}", amount) 
            slice_obj.setLabelVisible(True)
            slice_obj.setLabelColor(Qt.white)
            slice_obj.setLabelPosition(QPieSlice.LabelInsideHorizontal)
            slice_obj.setColor(QColor(colors[i % len(colors)]))
            
            # Tooltip Data
            pct = (amount / total) * 100
            slice_obj.data_tooltip = f"{category}\n${amount} ({pct:.1f}%)"

        # 2. Fix Legend Labels
        # By default, Legend takes the Slice Label (which is now Money).
        # We manually update the markers to show Category Names instead.
        markers = self.chart.legend().markers(self.series)
        for i, marker in enumerate(markers):
            if i < len(category_names):
                marker.setLabel(category_names[i])

    def on_slice_hover(self, slice_obj, state):
        if state:
            slice_obj.setExploded(True)
            QToolTip.showText(self.cursor().pos(), getattr(slice_obj, "data_tooltip", ""))
        else:
            slice_obj.setExploded(False)