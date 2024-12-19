import sqlite3
import os
import time
from datetime import datetime

class BackendLogger:
    def __init__(self, base_dir="./db/"):
        # Capture start time
        self.start_time = datetime.now()
        self.end_time = None

        # Initial provisional filename with start time only
        # Example: 2024-12-18_14-30-00.db
        self.start_str = self.start_time.strftime("%Y-%m-%d_%H-%M-%S")
        self.provisional_db_filename = f"{self.start_str}.db"
        self.db_path = os.path.join(base_dir, self.provisional_db_filename)

        self.conn = None
        self.create_database()

    def create_database(self):
        new_db = not os.path.exists(self.db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        if new_db:
            self._create_tables()
            # Insert start time (local time)
            start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO session_metadata (start_time) VALUES (?)", (start_time_str,))
            self.conn.commit()


    def _create_tables(self):
        cursor = self.conn.cursor()

        # Create the metadata table
        cursor.execute("""
        CREATE TABLE session_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            end_time TEXT
        )
        """)
        # Insert the start time
        cursor.execute("INSERT INTO session_metadata (start_time) VALUES (datetime('now'))")

        # CPU Metrics
        cursor.execute("""
        CREATE TABLE cpu_metrics (
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            core_usage TEXT,
            cpu_temp REAL,
            fan_speeds TEXT
        )
        """)

        # GPU Metrics
        cursor.execute("""
        CREATE TABLE gpu_metrics (
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            gpu_usage REAL,
            gpu_mem_usage REAL,
            gpu_temp REAL,
            gpu_fan REAL
        )
        """)

        # RAM Metrics
        cursor.execute("""
        CREATE TABLE ram_metrics (
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ram_usage REAL
        )
        """)

        # Network Metrics
        cursor.execute("""
        CREATE TABLE network_metrics (
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            download_speed REAL,
            upload_speed REAL
        )
        """)

        # Disk Metrics
        cursor.execute("""
        CREATE TABLE disk_metrics (
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            read_speed REAL,
            write_speed REAL
        )
        """)

        self.conn.commit()

    def log_cpu_metrics(self, core_usage_list, cpu_temp, fan_speeds):
        cursor = self.conn.cursor()
        core_usage_str = ",".join([str(u) for u in core_usage_list])
        fan_speeds_str = ",".join([str(f) for f in fan_speeds]) if fan_speeds else ""
        cursor.execute("""
        INSERT INTO cpu_metrics (core_usage, cpu_temp, fan_speeds)
        VALUES (?, ?, ?)
        """, (core_usage_str, cpu_temp, fan_speeds_str))
        self.conn.commit()

    def log_gpu_metrics(self, gpu_usage, gpu_mem_usage, gpu_temp, gpu_fan):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO gpu_metrics (gpu_usage, gpu_mem_usage, gpu_temp, gpu_fan)
        VALUES (?, ?, ?, ?)
        """, (gpu_usage, gpu_mem_usage, gpu_temp, gpu_fan))
        self.conn.commit()

    def log_ram_metrics(self, ram_usage):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO ram_metrics (ram_usage)
        VALUES (?)
        """, (ram_usage,))
        self.conn.commit()

    def log_network_metrics(self, download_speed, upload_speed):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO network_metrics (download_speed, upload_speed)
        VALUES (?, ?)
        """, (download_speed, upload_speed))
        self.conn.commit()

    def log_disk_metrics(self, read_speed, write_speed):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO disk_metrics (read_speed, write_speed)
        VALUES (?, ?)
        """, (read_speed, write_speed))
        self.conn.commit()

    def close(self):
        if self.conn:
            # Update end time (local time)
            end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor = self.conn.cursor()
            cursor.execute("""
            UPDATE session_metadata 
            SET end_time = ? 
            WHERE id = (SELECT MAX(id) FROM session_metadata)
            """, (end_time_str,))
            self.conn.commit()

            self.conn.close()
            self.conn = None

