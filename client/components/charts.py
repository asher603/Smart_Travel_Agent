from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolTip

class BudgetPieChart(QChartView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        
        # 1. Create Chart and Series
        self.chart = QChart()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignRight)
        self.chart.legend().setFont(QFont("Arial", 10))
        self.chart.setBackgroundVisible(False) # Transparent background to match card
        
        self.series = QPieSeries()
        self.series.hovered.connect(self.on_slice_hover)
        self.chart.addSeries(self.series)
        
        self.setChart(self.chart)

    def update_data(self, budget_data: dict):
        """ 
        Expects dict: {"Accommodation": 500, "Food": 300, ...}
        """
        self.series.clear()
        
        total = sum(budget_data.values())
        if total == 0: return

        # Define a modern color palette
        colors = ["#5e35b1", "#1e88e5", "#00897b", "#fdd835", "#e53935", "#8e24aa"]
        
        for i, (category, amount) in enumerate(budget_data.items()):
            slice_obj = self.series.append(category, amount)
            
            # Label on the slice (Amount)
            slice_obj.setLabel(f"${amount}")
            slice_obj.setLabelVisible(True)
            slice_obj.setLabelColor(Qt.white)
            
            # Color
            color = colors[i % len(colors)]
            slice_obj.setColor(QColor(color))
            
            # Store data for tooltip
            percentage = (amount / total) * 100
            slice_obj.data_tooltip = f"{category}\n${amount} ({percentage:.1f}%)"

    def on_slice_hover(self, slice_obj, state):
        """ Shows tooltip on hover and explodes the slice slightly """
        if state:
            slice_obj.setExploded(True)
            slice_obj.setLabelVisible(True)
            QToolTip.showText(self.cursor().pos(), getattr(slice_obj, "data_tooltip", ""))
        else:
            slice_obj.setExploded(False)