"""Enhanced logging and monitoring system for MCP server."""

import logging
import logging.handlers
import structlog
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import traceback
import asyncio
from dataclasses import dataclass, asdict
from enum import Enum
import psutil
import time

# Rich logging for better console output
try:
    from rich.logging import RichHandler
    from rich.console import Console
    from rich.traceback import install as install_rich_traceback
    RICH_AVAILABLE = True
    install_rich_traceback(show_locals=True)
except ImportError:
    RICH_AVAILABLE = False


class LogLevel(Enum):
    """Log levels with numeric values."""
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: str
    level: str
    logger: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    thread_id: Optional[int] = None
    process_id: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None
    exception: Optional[str] = None
    stack_trace: Optional[str] = None


@dataclass
class ErrorMetrics:
    """Error tracking metrics."""
    total_errors: int = 0
    error_rate: float = 0.0
    most_common_errors: Dict[str, int] = None
    error_trends: List[Dict[str, Any]] = None
    last_error_time: Optional[str] = None
    
    def __post_init__(self):
        if self.most_common_errors is None:
            self.most_common_errors = {}
        if self.error_trends is None:
            self.error_trends = []


@dataclass
class PerformanceMetrics:
    """Performance monitoring metrics."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_usage_mb: float = 0.0
    active_connections: int = 0
    requests_per_minute: float = 0.0
    average_response_time: float = 0.0
    uptime_seconds: float = 0.0


class LoggerManager:
    """Enhanced logging manager with structured logging and monitoring."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.log_level = getattr(logging, self.config.get("log_level", "INFO").upper())
        self.log_format = self.config.get("log_format", "detailed")
        self.log_file = self.config.get("log_file")
        self.max_log_files = self.config.get("max_log_files", 10)
        self.max_log_size_mb = self.config.get("max_log_size_mb", 50)
        
        # Error tracking
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[LogEntry] = []
        self.performance_history: List[PerformanceMetrics] = []
        self.start_time = time.time()
        
        # Request tracking
        self.request_times: List[float] = []
        self.request_count = 0
        
        # Setup logging
        self._setup_logging()
        self._setup_structured_logging()
        
        # Start performance monitoring
        self._start_performance_monitoring()
        
    def _setup_logging(self):
        """Setup enhanced logging configuration."""
        # Clear existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # Create formatters
        if self.log_format == "json":
            formatter = JsonFormatter()
        elif self.log_format == "detailed":
            formatter = DetailedFormatter()
        else:
            formatter = SimpleFormatter()
            
        # Console handler with Rich if available
        if RICH_AVAILABLE:
            console_handler = RichHandler(
                console=Console(stderr=True),
                show_time=True,
                show_level=True,
                show_path=True,
                rich_tracebacks=True,
                tracebacks_show_locals=True
            )
        else:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(formatter)
            
        console_handler.setLevel(self.log_level)
        root_logger.addHandler(console_handler)
        
        # File handler with rotation
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                filename=self.log_file,
                maxBytes=self.max_log_size_mb * 1024 * 1024,
                backupCount=self.max_log_files,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)  # Log everything to file
            root_logger.addHandler(file_handler)
            
        # Error file handler
        if self.log_file:
            error_file = log_path.parent / f"{log_path.stem}_errors{log_path.suffix}"
            error_handler = logging.handlers.RotatingFileHandler(
                filename=str(error_file),
                maxBytes=self.max_log_size_mb * 1024 * 1024,
                backupCount=self.max_log_files,
                encoding='utf-8'
            )
            error_handler.setFormatter(formatter)
            error_handler.setLevel(logging.ERROR)
            root_logger.addHandler(error_handler)
            
        root_logger.setLevel(logging.DEBUG)
        
    def _setup_structured_logging(self):
        """Setup structured logging with structlog."""
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.ConsoleRenderer() if self.log_format != "json" else structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(self.log_level),
            logger_factory=structlog.WriteLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
    def _start_performance_monitoring(self):
        """Start background performance monitoring."""
        asyncio.create_task(self._monitor_performance())
        
    async def _monitor_performance(self):
        """Monitor system performance metrics."""
        while True:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Calculate request rate
                current_time = time.time()
                uptime = current_time - self.start_time
                requests_per_minute = (self.request_count / uptime) * 60 if uptime > 0 else 0
                
                # Calculate average response time
                avg_response_time = (
                    sum(self.request_times[-100:]) / len(self.request_times[-100:])
                    if self.request_times else 0
                )
                
                metrics = PerformanceMetrics(
                    cpu_usage=cpu_percent,
                    memory_usage=memory.percent,
                    memory_usage_mb=memory.used / (1024 * 1024),
                    requests_per_minute=requests_per_minute,
                    average_response_time=avg_response_time,
                    uptime_seconds=uptime
                )
                
                self.performance_history.append(metrics)
                
                # Keep only last 100 performance records
                if len(self.performance_history) > 100:
                    self.performance_history = self.performance_history[-100:]
                    
                # Log performance warnings
                if cpu_percent > 80:
                    logging.warning(f"High CPU usage: {cpu_percent}%")
                if memory.percent > 80:
                    logging.warning(f"High memory usage: {memory.percent}%")
                    
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logging.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(60)  # Wait longer on error
                
    def log_request(self, method: str, duration: float, success: bool, error: Optional[str] = None):
        """Log request metrics."""
        self.request_count += 1
        self.request_times.append(duration)
        
        # Keep only last 1000 request times for memory efficiency
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
            
        # Log errors
        if not success and error:
            self.error_counts[error] = self.error_counts.get(error, 0) + 1
            
            error_entry = LogEntry(
                timestamp=datetime.now().isoformat(),
                level="ERROR",
                logger="request",
                message=f"Request failed: {method}",
                extra_data={"method": method, "duration": duration, "error": error}
            )
            self.error_history.append(error_entry)
            
            # Keep only last 1000 error records
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-1000:]
                
    def get_error_metrics(self) -> ErrorMetrics:
        """Get current error metrics."""
        total_errors = sum(self.error_counts.values())
        error_rate = (total_errors / max(self.request_count, 1)) * 100
        
        # Sort errors by frequency
        most_common = dict(sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Get error trends (last 24 hours)
        recent_errors = [
            e for e in self.error_history 
            if (datetime.now() - datetime.fromisoformat(e.timestamp)).total_seconds() < 86400
        ]
        
        last_error_time = None
        if self.error_history:
            last_error_time = self.error_history[-1].timestamp
            
        return ErrorMetrics(
            total_errors=total_errors,
            error_rate=error_rate,
            most_common_errors=most_common,
            error_trends=[asdict(e) for e in recent_errors[-100:]],
            last_error_time=last_error_time
        )
        
    def get_performance_metrics(self) -> Optional[PerformanceMetrics]:
        """Get current performance metrics."""
        return self.performance_history[-1] if self.performance_history else None
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        error_metrics = self.get_error_metrics()
        perf_metrics = self.get_performance_metrics()
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        if error_metrics.error_rate > 10:
            health_status = "degraded"
            issues.append(f"High error rate: {error_metrics.error_rate:.1f}%")
            
        if perf_metrics:
            if perf_metrics.cpu_usage > 80:
                health_status = "degraded"
                issues.append(f"High CPU usage: {perf_metrics.cpu_usage:.1f}%")
            if perf_metrics.memory_usage > 80:
                health_status = "degraded"
                issues.append(f"High memory usage: {perf_metrics.memory_usage:.1f}%")
            if perf_metrics.average_response_time > 5:
                health_status = "degraded"
                issues.append(f"Slow response time: {perf_metrics.average_response_time:.2f}s")
                
        if error_metrics.error_rate > 25 or (perf_metrics and perf_metrics.cpu_usage > 95):
            health_status = "unhealthy"
            
        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self.start_time,
            "request_count": self.request_count,
            "error_metrics": asdict(error_metrics),
            "performance_metrics": asdict(perf_metrics) if perf_metrics else None,
            "issues": issues
        }


class SimpleFormatter(logging.Formatter):
    """Simple log formatter."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class DetailedFormatter(logging.Formatter):
    """Detailed log formatter with extra context."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
    def format(self, record):
        # Add thread and process info
        record.thread_id = record.thread
        record.process_id = record.process
        return super().format(record)


class JsonFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line_number': record.lineno,
            'thread_id': record.thread,
            'process_id': record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add stack trace if present
        if record.stack_info:
            log_entry['stack_trace'] = record.stack_info
            
        # Add any extra fields
        if hasattr(record, 'extra_data'):
            log_entry['extra_data'] = record.extra_data
            
        return json.dumps(log_entry, default=str)


# Global logger manager instance
_logger_manager: Optional[LoggerManager] = None


def setup_logging(config: Optional[Dict[str, Any]] = None) -> LoggerManager:
    """Setup enhanced logging system."""
    global _logger_manager
    _logger_manager = LoggerManager(config)
    return _logger_manager


def get_logger_manager() -> Optional[LoggerManager]:
    """Get the global logger manager instance."""
    return _logger_manager


def log_request_metrics(method: str, duration: float, success: bool, error: Optional[str] = None):
    """Log request metrics to the global logger manager."""
    if _logger_manager:
        _logger_manager.log_request(method, duration, success, error)


def get_system_health() -> Dict[str, Any]:
    """Get current system health status."""
    if _logger_manager:
        return _logger_manager.get_health_status()
    return {"status": "unknown", "message": "Logger manager not initialized"}
