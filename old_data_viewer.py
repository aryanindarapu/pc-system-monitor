import sqlite3
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget
import pyqtgraph as pg

class OldDataViewer(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.setWindowTitle(f"Old Data Viewer - {os.path.basename(db_path)}")
        self.setGeometry(200, 200, 800, 600)

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Check if the DB exists
        if not os.path.exists(self.db_path):
            self.layout.addWidget(QLabel("Database file not found."))
            return

        # Create all tabs
        self.create_cpu_tab()
        self.create_gpu_tab()
        self.create_ram_tab()
        self.create_network_tab()
        self.create_disk_tab()

    def create_cpu_tab(self):
        cpu_tab = QWidget()
        vlayout = QVBoxLayout(cpu_tab)
        cpu_data = self.get_cpu_data()

        if not cpu_data:
            vlayout.addWidget(QLabel("No CPU data available."))
            self.tabs.addTab(cpu_tab, "CPU")
            return

        # Plot average CPU usage over time
        times = []
        avg_usages = []
        for row in cpu_data:
            usage_vals = [float(x) for x in row[1].split(',') if x.strip()]
            if usage_vals:
                avg_usage = sum(usage_vals) / len(usage_vals)
                avg_usages.append(avg_usage)
                times.append(row[0])

        if times and avg_usages:
            indices = list(range(len(times)))
            plot_widget = pg.PlotWidget(title="Historical CPU Usage (%)")
            plot_widget.plot(indices, avg_usages, pen='y')
            vlayout.addWidget(plot_widget)
        else:
            vlayout.addWidget(QLabel("No valid CPU usage data to plot."))
        self.tabs.addTab(cpu_tab, "CPU")

    def create_gpu_tab(self):
        gpu_tab = QWidget()
        vlayout = QVBoxLayout(gpu_tab)
        gpu_data = self.get_gpu_data()

        if not gpu_data:
            vlayout.addWidget(QLabel("No GPU data available."))
            self.tabs.addTab(gpu_tab, "GPU")
            return

        # gpu_data = [(timestamp, gpu_usage, gpu_mem_usage, gpu_temp, gpu_fan), ...]
        # We'll plot GPU usage and memory usage on separate graphs for example
        times = list(range(len(gpu_data)))
        gpu_usages = [row[1] for row in gpu_data]
        gpu_mem_usages = [row[2] for row in gpu_data]
        gpu_temps = [row[3] for row in gpu_data]
        gpu_fans = [row[4] for row in gpu_data]

        # GPU usage
        usage_plot = pg.PlotWidget(title="GPU Usage (%)")
        usage_plot.plot(times, gpu_usages, pen='r')
        vlayout.addWidget(usage_plot)

        # GPU Memory Usage
        mem_plot = pg.PlotWidget(title="GPU Memory Usage (MB)")
        mem_plot.plot(times, gpu_mem_usages, pen='g')
        vlayout.addWidget(mem_plot)

        # GPU Temperature
        temp_plot = pg.PlotWidget(title="GPU Temperature (°C)")
        temp_plot.plot(times, gpu_temps, pen='b')
        vlayout.addWidget(temp_plot)

        # GPU Fan Speed
        fan_plot = pg.PlotWidget(title="GPU Fan Speed (%)")
        fan_plot.plot(times, gpu_fans, pen='c')
        vlayout.addWidget(fan_plot)

        self.tabs.addTab(gpu_tab, "GPU")

    def create_ram_tab(self):
        ram_tab = QWidget()
        vlayout = QVBoxLayout(ram_tab)
        ram_data = self.get_ram_data()

        if not ram_data:
            vlayout.addWidget(QLabel("No RAM data available."))
            self.tabs.addTab(ram_tab, "RAM")
            return

        times = list(range(len(ram_data)))
        usages = [row[1] for row in ram_data]

        if usages:
            plot_widget = pg.PlotWidget(title="Historical RAM Usage (%)")
            plot_widget.plot(times, usages, pen='g')
            vlayout.addWidget(plot_widget)
        else:
            vlayout.addWidget(QLabel("No valid RAM usage data to plot."))

        self.tabs.addTab(ram_tab, "RAM")

    def create_network_tab(self):
        network_tab = QWidget()
        vlayout = QVBoxLayout(network_tab)
        net_data = self.get_network_data()

        if not net_data:
            vlayout.addWidget(QLabel("No Network data available."))
            self.tabs.addTab(network_tab, "Network")
            return

        # net_data = [(timestamp, download_speed, upload_speed), ...]
        times = list(range(len(net_data)))
        downloads = [row[1] for row in net_data]
        uploads = [row[2] for row in net_data]

        if downloads or uploads:
            plot_widget = pg.PlotWidget(title="Network Speeds (KB/s)")
            plot_widget.addLegend()
            plot_widget.plot(times, downloads, pen='c', name='Download')
            plot_widget.plot(times, uploads, pen='m', name='Upload')
            vlayout.addWidget(plot_widget)
        else:
            vlayout.addWidget(QLabel("No valid Network data to plot."))

        self.tabs.addTab(network_tab, "Network")

    def create_disk_tab(self):
        disk_tab = QWidget()
        vlayout = QVBoxLayout(disk_tab)
        disk_data = self.get_disk_data()

        if not disk_data:
            vlayout.addWidget(QLabel("No Disk data available."))
            self.tabs.addTab(disk_tab, "Disk")
            return

        # disk_data = [(timestamp, read_speed, write_speed), ...]
        times = list(range(len(disk_data)))
        reads = [row[1] for row in disk_data]
        writes = [row[2] for row in disk_data]

        if reads or writes:
            plot_widget = pg.PlotWidget(title="Disk I/O Speeds (KB/s)")
            plot_widget.addLegend()
            plot_widget.plot(times, reads, pen='y', name='Read')
            plot_widget.plot(times, writes, pen='w', name='Write')
            vlayout.addWidget(plot_widget)
        else:
            vlayout.addWidget(QLabel("No valid Disk data to plot."))

        self.tabs.addTab(disk_tab, "Disk")

    def get_cpu_data(self):
        # Retrieve CPU metrics from the DB
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, core_usage, cpu_temp, fan_speeds FROM cpu_metrics ORDER BY timestamp ASC")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print("Error reading CPU data:", e)
            return []

    def get_gpu_data(self):
        # Retrieve GPU metrics from the DB
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, gpu_usage, gpu_mem_usage, gpu_temp, gpu_fan FROM gpu_metrics ORDER BY timestamp ASC")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print("Error reading GPU data:", e)
            return []

    def get_ram_data(self):
        # Retrieve RAM metrics from the DB
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, ram_usage FROM ram_metrics ORDER BY timestamp ASC")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print("Error reading RAM data:", e)
            return []

    def get_network_data(self):
        # Retrieve Network metrics from the DB
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, download_speed, upload_speed FROM network_metrics ORDER BY timestamp ASC")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print("Error reading Network data:", e)
            return []

    def get_disk_data(self):
        # Retrieve Disk metrics from the DB
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, read_speed, write_speed FROM disk_metrics ORDER BY timestamp ASC")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print("Error reading Disk data:", e)
            return []
