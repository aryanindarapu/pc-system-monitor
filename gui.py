import sys
import time
import psutil
import pyqtgraph as pg
# Remove pynvml if not using NVIDIA GPUs
import pynvml
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QLabel, QGridLayout, QProgressBar, QHBoxLayout
)
from PyQt5.QtCore import QTimer, Qt

PLOT_LENGTH = 60 + 1

# Initialize NVML for GPU metrics
try:
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
    gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # Assuming a single GPU
except:
    NVML_AVAILABLE = False

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
        self.create_ram_tab()
        self.create_network_tab()
        self.create_disk_tab()
        self.create_system_info_tab()

        # Start timers for dynamic updates
        self.start_timers()

    def create_cpu_tab(self):
        self.cpu_tab = QWidget()
        self.tabs.addTab(self.cpu_tab, "CPU")
        layout = QVBoxLayout(self.cpu_tab)

        # Static CPU Info
        cpu_info_layout = QGridLayout()
        layout.addLayout(cpu_info_layout)
        cpu_info_layout.addWidget(QLabel("CPU Model:"), 0, 0)
        cpu_info_layout.addWidget(QLabel(self.get_cpu_model()), 0, 1)
        cpu_info_layout.addWidget(QLabel("Physical Cores:"), 1, 0)
        cpu_info_layout.addWidget(QLabel(str(psutil.cpu_count(logical=False))), 1, 1)
        cpu_info_layout.addWidget(QLabel("Logical Cores:"), 2, 0)
        cpu_info_layout.addWidget(QLabel(str(psutil.cpu_count(logical=True))), 2, 1)

        # Dynamic CPU Usage per Core
        self.cpu_usage_labels = []
        num_cores = psutil.cpu_count(logical=True)
        cores_layout = QGridLayout()
        layout.addLayout(cores_layout)
        for i in range(num_cores):
            label = QLabel(f"Core {i} Usage: 0%")
            self.cpu_usage_labels.append(label)
            cores_layout.addWidget(label, i // 4, i % 4)

        # CPU Usage per Core Graph
        self.cpu_plot = pg.PlotWidget(title="CPU Usage per Core (%)")
        self.cpu_plot.setYRange(0, 100)
        self.cpu_plot.setXRange(0, 60)

        self.cpu_plot.setLimits(yMin=0, yMax=100)
        self.cpu_plot.setMouseEnabled(x=False, y=False)  # Disable y-axis zoom and pan
        layout.addWidget(self.cpu_plot)
        self.cpu_plot.addLegend()
        self.cpu_data = [[] for _ in range(num_cores)]
        self.cpu_curves = []
        # colors = ['r', 'g', 'b', 'c', 'm', 'y', 'w', 'k']
        colors = colors = [
            'r', 'g', 'b', 'c', 'm', 'y', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', 
            '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#9edae5', 
            '#393b79', '#637939', '#8c6d31', '#843c39', '#5254a3', '#6b6ecf', '#637939', 
            '#e6550d', '#31a354', '#3182bd', '#756bb1', '#636363', '#969696', '#fdae6b'
        ]

        
        for i in range(num_cores):
            color = colors[i % len(colors)]
            curve = self.cpu_plot.plot(self.cpu_data[i], pen=color, name=f"Core {i}")
            self.cpu_curves.append(curve)
        
        # num_colors = 32
        # colors = [cm.hsv(i / num_colors) for i in range(num_colors)]  # Generates RGB tuples

        # for i in range(num_cores):
        #     color = colors[i % len(colors)]  # Cycle through colors if num_cores > num_colors
        #     pen_color = (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255)  # Convert to 0-255 RGBA
        #     curve = self.cpu_plot.plot(self.cpu_data[i], pen=pen_color, name=f"Core {i}")
        #     self.cpu_curves.append(curve)

    def create_gpu_tab(self):
        self.gpu_tab = QWidget()
        self.tabs.addTab(self.gpu_tab, "GPU")
        layout = QVBoxLayout(self.gpu_tab)

        if NVML_AVAILABLE:
            # Static GPU Info
            gpu_info_layout = QGridLayout()
            layout.addLayout(gpu_info_layout)
            gpu_name = pynvml.nvmlDeviceGetName(gpu_handle).decode('utf-8')
            gpu_info_layout.addWidget(QLabel("GPU Model:"), 0, 0)
            gpu_info_layout.addWidget(QLabel(gpu_name), 0, 1)

            # Dynamic GPU Usage
            self.gpu_usage_label = QLabel("GPU Usage: 0%")
            layout.addWidget(self.gpu_usage_label)

            # GPU Usage Graph
            self.gpu_plot = pg.PlotWidget(title="GPU Usage (%)")
            self.gpu_plot.setYRange(0, 100)
            self.gpu_plot.setXRange(0, 60)
            self.gpu_plot.setLimits(yMin=0, yMax=100)
            self.gpu_plot.setMouseEnabled(y=False)  # Disable y-axis zoom and pan
            layout.addWidget(self.gpu_plot)
            self.gpu_data = []
            self.gpu_curve = self.gpu_plot.plot(self.gpu_data, pen='r')
        else:
            layout.addWidget(QLabel("NVIDIA NVML library not found. GPU monitoring is unavailable."))

    def create_ram_tab(self):
        self.ram_tab = QWidget()
        self.tabs.addTab(self.ram_tab, "RAM")
        layout = QVBoxLayout(self.ram_tab)

        # Static RAM Info
        ram_info_layout = QGridLayout()
        layout.addLayout(ram_info_layout)
        svmem = psutil.virtual_memory()
        total_ram = svmem.total / (1024 ** 3)
        ram_info_layout.addWidget(QLabel("Total RAM (GB):"), 0, 0)
        ram_info_layout.addWidget(QLabel(f"{total_ram:.2f}"), 0, 1)

        # Dynamic RAM Usage
        self.ram_usage_label = QLabel("RAM Usage: 0%")
        layout.addWidget(self.ram_usage_label)

        # RAM Usage Graph
        self.ram_plot = pg.PlotWidget(title="RAM Usage (%)")
        self.ram_plot.setYRange(0, 100)
        self.ram_plot.setXRange(0, 60)
        self.ram_plot.setLimits(yMin=0, yMax=100)
        self.ram_plot.setLimits(xMin=0, xMax=PLOT_LENGTH)
        # self.ram_plot.setMouseEnabled(y=False)  # Disable y-axis zoom and pan
        layout.addWidget(self.ram_plot)
        self.ram_data = []
        self.ram_curve = self.ram_plot.plot(self.ram_data, pen='g')

    def create_network_tab(self):
        self.network_tab = QWidget()
        self.tabs.addTab(self.network_tab, "Network")
        layout = QVBoxLayout(self.network_tab)

        # Network Interface Info
        net_info_layout = QGridLayout()
        layout.addLayout(net_info_layout)
        interfaces = psutil.net_if_addrs()
        self.interface_names = list(interfaces.keys())
        net_info_layout.addWidget(QLabel("Interfaces:"), 0, 0)
        net_info_layout.addWidget(QLabel(", ".join(self.interface_names)), 0, 1)

        # Dynamic Network Usage
        self.net_usage_label = QLabel("Download: 0 KB/s | Upload: 0 KB/s")
        layout.addWidget(self.net_usage_label)

        # Network Usage Graphs
        self.net_plot = pg.PlotWidget(title="Network Speed (KB/s)")
        layout.addWidget(self.net_plot)
        self.net_plot.addLegend()
        self.net_plot.setXRange(0, 60)
        self.net_plot.setLimits(xMin=0, xMax=PLOT_LENGTH)
        self.net_plot.setLimits(yMin=0)
        self.net_plot.setMouseEnabled(y=False)  # Disable y-axis zoom and pan
        self.net_download_data = []
        self.net_upload_data = []
        self.net_download_curve = self.net_plot.plot(self.net_download_data, pen='c', name='Download')
        self.net_upload_curve = self.net_plot.plot(self.net_upload_data, pen='m', name='Upload')

        # For calculating network speed
        self.last_net_io = psutil.net_io_counters()

    def create_disk_tab(self):
        self.disk_tab = QWidget()
        self.tabs.addTab(self.disk_tab, "Disk")
        layout = QVBoxLayout(self.disk_tab)

        # Disk Partitions Info
        partitions = psutil.disk_partitions()
        disk_info_layout = QGridLayout()
        layout.addLayout(disk_info_layout)
        for i, partition in enumerate(partitions):
            disk_usage = psutil.disk_usage(partition.mountpoint)
            total_disk = disk_usage.total / (1024 ** 3)
            disk_info_layout.addWidget(QLabel(f"Partition {partition.device} - Total Space (GB):"), i, 0)
            disk_info_layout.addWidget(QLabel(f"{total_disk:.2f}"), i, 1)

        # Dynamic Disk Usage
        self.disk_usage_label = QLabel("Read Speed: 0 KB/s | Write Speed: 0 KB/s")
        layout.addWidget(self.disk_usage_label)

        # Disk Usage Graphs
        self.disk_plot = pg.PlotWidget(title="Disk I/O Speed (KB/s)")
        layout.addWidget(self.disk_plot)
        self.disk_plot.addLegend()
        # self.disk_plot.setYRange(0, 1000)
        self.disk_plot.setXRange(0, 60)
        self.disk_plot.setLimits(xMin=0, xMax=PLOT_LENGTH)
        self.disk_plot.setLimits(yMin=0)
        # self.cpu_plot.setXRange(0, 60)
        self.disk_plot.setMouseEnabled(y=False)  # Disable y-axis zoom and pan
        self.disk_read_data = []
        self.disk_write_data = []
        self.disk_read_curve = self.disk_plot.plot(self.disk_read_data, pen='y', name='Read')
        self.disk_write_curve = self.disk_plot.plot(self.disk_write_data, pen='w', name='Write')

        # For calculating disk speed
        self.last_disk_io = psutil.disk_io_counters()

    def create_system_info_tab(self):
        self.sys_tab = QWidget()
        self.tabs.addTab(self.sys_tab, "System Info")
        layout = QVBoxLayout(self.sys_tab)

        # Static System Info
        sys_info_layout = QGridLayout()
        layout.addLayout(sys_info_layout)
        sys_info_layout.addWidget(QLabel("OS Version:"), 0, 0)
        sys_info_layout.addWidget(QLabel(self.get_os_version()), 0, 1)
        sys_info_layout.addWidget(QLabel("Hostname:"), 1, 0)
        sys_info_layout.addWidget(QLabel(self.get_hostname()), 1, 1)

        # Dynamic System Info
        self.uptime_label = QLabel("System Uptime: 0:00:00")
        layout.addWidget(self.uptime_label)
        self.update_uptime()

    def start_timers(self):
        # Timers for updating dynamic metrics
        self.cpu_timer = QTimer()
        self.cpu_timer.timeout.connect(self.update_cpu_metrics)
        self.cpu_timer.start(1000)  # Update every 1 second

        if NVML_AVAILABLE:
            self.gpu_timer = QTimer()
            self.gpu_timer.timeout.connect(self.update_gpu_metrics)
            self.gpu_timer.start(1000)

        self.ram_timer = QTimer()
        self.ram_timer.timeout.connect(self.update_ram_metrics)
        self.ram_timer.start(1000)

        self.net_timer = QTimer()
        self.net_timer.timeout.connect(self.update_network_metrics)
        self.net_timer.start(1000)

        self.disk_timer = QTimer()
        self.disk_timer.timeout.connect(self.update_disk_metrics)
        self.disk_timer.start(1000)

        self.uptime_timer = QTimer()
        self.uptime_timer.timeout.connect(self.update_uptime)
        self.uptime_timer.start(60000)  # Update every 1 minute
        
    def update_mentrics(self):
        pass

    def update_cpu_metrics(self):
        cpu_usages = psutil.cpu_percent(interval=None, percpu=True)
        for i, usage in enumerate(cpu_usages):
            self.cpu_usage_labels[i].setText(f"Core {i} Usage: {usage}%")
            self.cpu_data[i].append(usage)
            if len(self.cpu_data[i]) > PLOT_LENGTH:
                self.cpu_data[i].pop(0)
            self.cpu_curves[i].setData(self.cpu_data[i])

    def update_gpu_metrics(self):
        gpu_util = pynvml.nvmlDeviceGetUtilizationRates(gpu_handle).gpu
        self.gpu_usage_label.setText(f"GPU Usage: {gpu_util}%")

        self.gpu_data.append(gpu_util)
        if len(self.gpu_data) > PLOT_LENGTH:
            self.gpu_data.pop(0)
        self.gpu_curve.setData(self.gpu_data)

    def update_ram_metrics(self):
        ram = psutil.virtual_memory()
        ram_usage = ram.percent
        self.ram_usage_label.setText(f"RAM Usage: {ram_usage}%")

        self.ram_data.append(ram_usage)
        if len(self.ram_data) > PLOT_LENGTH:
            self.ram_data.pop(0)
        self.ram_curve.setData(self.ram_data)

    def update_network_metrics(self):
        net_io = psutil.net_io_counters()
        download_speed = (net_io.bytes_recv - self.last_net_io.bytes_recv) / 1024  # KB/s
        upload_speed = (net_io.bytes_sent - self.last_net_io.bytes_sent) / 1024  # KB/s
        self.last_net_io = net_io

        self.net_usage_label.setText(f"Download: {download_speed:.2f} KB/s | Upload: {upload_speed:.2f} KB/s")

        self.net_download_data.append(download_speed)
        self.net_upload_data.append(upload_speed)
        if len(self.net_download_data) > PLOT_LENGTH:
            self.net_download_data.pop(0)
            self.net_upload_data.pop(0)
        self.net_download_curve.setData(self.net_download_data)
        self.net_upload_curve.setData(self.net_upload_data)

    def update_disk_metrics(self):
        disk_io = psutil.disk_io_counters()
        read_speed = (disk_io.read_bytes - self.last_disk_io.read_bytes) / 1024  # KB/s
        write_speed = (disk_io.write_bytes - self.last_disk_io.write_bytes) / 1024  # KB/s
        self.last_disk_io = disk_io

        self.disk_usage_label.setText(f"Read Speed: {read_speed:.2f} KB/s | Write Speed: {write_speed:.2f} KB/s")

        self.disk_read_data.append(read_speed)
        self.disk_write_data.append(write_speed)
        if len(self.disk_read_data) > PLOT_LENGTH:
            self.disk_read_data.pop(0)
            self.disk_write_data.pop(0)
        self.disk_read_curve.setData(self.disk_read_data)
        self.disk_write_curve.setData(self.disk_write_data)

    def update_uptime(self):
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_string = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))
        self.uptime_label.setText(f"System Uptime: {uptime_string}")

    def get_cpu_model(self):
        try:
            if sys.platform == "win32":
                import wmi
                c = wmi.WMI()
                for processor in c.Win32_Processor():
                    return processor.Name
            elif sys.platform.startswith("linux"):
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if "model name" in line:
                            return line.strip().split(":")[1].strip()
            elif sys.platform == "darwin":
                import subprocess
                command = "sysctl -n machdep.cpu.brand_string"
                output = subprocess.check_output(command, shell=True).strip()
                return output.decode('utf-8')
        except Exception as e:
            return f"Unknown ({e})"

    def get_os_version(self):
        try:
            import platform
            return platform.platform()
        except Exception as e:
            return f"Unknown ({e})"

    def get_hostname(self):
        try:
            import socket
            return socket.gethostname()
        except Exception as e:
            return f"Unknown ({e})"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    monitor = SystemMonitor()
    monitor.show()
    sys.exit(app.exec_())
