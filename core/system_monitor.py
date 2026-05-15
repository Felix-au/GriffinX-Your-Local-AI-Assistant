"""
Lightweight system stats collector using psutil (CPU/RAM) and optional pynvml (NVIDIA GPU).
Emits stats_updated signal every 1 second.
"""
import logging
from dataclasses import dataclass, field
from PySide6.QtCore import QObject, QTimer, Signal

import psutil

logger = logging.getLogger(__name__)


@dataclass
class SystemStats:
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    ram_used_mb: float = 0.0
    ram_total_mb: float = 0.0
    gpu_name: str = "N/A"
    gpu_util_percent: float = -1.0  # -1 = unavailable
    gpu_mem_percent: float = -1.0
    gpu_mem_used_mb: float = 0.0
    gpu_mem_total_mb: float = 0.0
    gpu_temp_c: float = -1.0


class SystemMonitor(QObject):
    """Periodic system stats collector (CPU, RAM, GPU)."""

    stats_updated = Signal(object)  # emits SystemStats

    def __init__(self, interval_ms: int = 1000, parent=None):
        super().__init__(parent)
        self._interval = interval_ms
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._collect)
        self._gpu_available = False
        self._nvml_handle = None
        self._init_gpu()

    def _init_gpu(self):
        """Try to initialize NVIDIA GPU monitoring via pynvml."""
        try:
            import pynvml
            pynvml.nvmlInit()
            count = pynvml.nvmlDeviceGetCount()
            if count > 0:
                self._nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name = pynvml.nvmlDeviceGetName(self._nvml_handle)
                if isinstance(name, bytes):
                    name = name.decode("utf-8")
                self._gpu_name = name
                self._gpu_available = True
                logger.info(f"GPU monitoring enabled: {name}")
            else:
                logger.info("No NVIDIA GPU detected")
        except ImportError:
            logger.info("pynvml not installed — GPU monitoring disabled")
        except Exception as e:
            logger.warning(f"GPU init failed: {e}")

    def start(self):
        self._timer.start(self._interval)

    def stop(self):
        self._timer.stop()

    def _collect(self):
        stats = SystemStats()

        # CPU
        stats.cpu_percent = psutil.cpu_percent(interval=None)

        # RAM
        mem = psutil.virtual_memory()
        stats.ram_percent = mem.percent
        stats.ram_used_mb = mem.used / (1024 ** 2)
        stats.ram_total_mb = mem.total / (1024 ** 2)

        # GPU
        if self._gpu_available and self._nvml_handle:
            try:
                import pynvml
                util = pynvml.nvmlDeviceGetUtilizationRates(self._nvml_handle)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(self._nvml_handle)

                stats.gpu_name = self._gpu_name
                stats.gpu_util_percent = float(util.gpu)
                stats.gpu_mem_used_mb = mem_info.used / (1024 ** 2)
                stats.gpu_mem_total_mb = mem_info.total / (1024 ** 2)
                stats.gpu_mem_percent = (mem_info.used / mem_info.total) * 100 if mem_info.total > 0 else 0

                try:
                    temp = pynvml.nvmlDeviceGetTemperature(self._nvml_handle, pynvml.NVML_TEMPERATURE_GPU)
                    stats.gpu_temp_c = float(temp)
                except Exception:
                    stats.gpu_temp_c = -1
            except Exception as e:
                logger.debug(f"GPU poll error: {e}")

        self.stats_updated.emit(stats)
