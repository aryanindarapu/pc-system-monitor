import sys
import time
import psutil
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QLabel, QGridLayout
)
from PyQt5.QtCore import QTimer

# Initialize NVML for GPU metrics
try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
    gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # Assuming a single GPU
except ImportError:
    NVML_AVAILABLE = False
    print("pynvml library not found. GPU temperature monitoring is unavailable.")
except pynvml.NVMLError:
    NVML_AVAILABLE = False
    print("NVIDIA GPU not found. GPU temperature monitoring is unavailable.")

PLOT_LENGTH = 60  # Number of data points to display in the graph

class SystemMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Monitor")
        self.setGeometry(100, 100, 1200, 800)

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Create tabs
        self.create_cpu_tab()
        self.create_gpu_tab()

        # Start timers for dynamic updates
        self.start_timers()

    def create_cpu_tab(self):
        self.cpu_tab = QWidget()
        self.tabs.addTab(self.cpu_tab, "CPU")
        layout = QVBoxLayout(self.cpu_tab)

        # CPU Temperature Graph
        self.cpu_temp_plot = pg.PlotWidget(title="CPU Temperature (°C)")
        self.cpu_temp_plot.setYRange(0, 100)
        self.cpu_temp_plot.setXRange(0, PLOT_LENGTH)
        self.cpu_temp_plot.setMouseEnabled(x=False, y=False)  # Disable zoom and pan
        layout.addWidget(self.cpu_temp_plot)
        self.cpu_temp_data = []
        self.cpu_temp_curve = self.cpu_temp_plot.plot(self.cpu_temp_data, pen='r')

    def create_gpu_tab(self):
        self.gpu_tab = QWidget()
        self.tabs.addTab(self.gpu_tab, "GPU")
        layout = QVBoxLayout(self.gpu_tab)

        if NVML_AVAILABLE:
            # GPU Temperature Graph
            self.gpu_temp_plot = pg.PlotWidget(title="GPU Temperature (°C)")
            self.gpu_temp_plot.setYRange(0, 100)
            self.gpu_temp_plot.setXRange(0, PLOT_LENGTH)
            self.gpu_temp_plot.setMouseEnabled(x=False, y=False)  # Disable zoom and pan
            layout.addWidget(self.gpu_temp_plot)
            self.gpu_temp_data = []
            self.gpu_temp_curve = self.gpu_temp_plot.plot(self.gpu_temp_data, pen='b')
        else:
            layout.addWidget(QLabel("GPU temperature monitoring is unavailable."))

    def start_timers(self):
        # Timer for updating CPU temperature
        self.cpu_temp_timer = QTimer()
        self.cpu_temp_timer.timeout.connect(self.update_cpu_temperature)
        self.cpu_temp_timer.start(1000)  # Update every 1 second

        if NVML_AVAILABLE:
            # Timer for updating GPU temperature
            self.gpu_temp_timer = QTimer()
            self.gpu_temp_timer.timeout.connect(self.update_gpu_temperature)
            self.gpu_temp_timer.start(1000)  # Update every 1 second

    def update_cpu_temperature(self):
        temps = psutil.sensors_temperatures()
        if 'coretemp' in temps:
            cpu_temp = temps['coretemp'][0].current
            self.cpu_temp_data.append(cpu_temp)
            if len(self.cpu_temp_data) > PLOT_LENGTH:
                self.cpu_temp_data.pop(0)
            self.cpu_temp_curve.setData(self.cpu_temp_data)
        else:
            print("No CPU temperature data available.")

    def update_gpu_temperature(self):
        if NVML_AVAILABLE:
            gpu_temp = pynvml.nvmlDeviceGetTemperature(gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
            self.gpu_temp_data.append(gpu_temp)
            if len(self.gpu_temp_data) > PLOT_LENGTH:
                self.gpu_temp_data.pop(0)
            self.gpu_temp_curve.setData(self.gpu_temp_data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    monitor = SystemMonitor()
    monitor.show()
    sys.exit(app.exec_())
