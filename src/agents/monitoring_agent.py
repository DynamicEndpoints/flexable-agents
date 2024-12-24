from typing import Optional, Dict, Any, List
import psutil
import platform
import logging
from datetime import datetime, timedelta
import json
from pathlib import Path
import asyncio
import aiohttp
import socket

from ..core.base import Agent, Task, TaskResult, Message
from ..utils.helpers import Timer

logger = logging.getLogger(__name__)

class MonitoringAgent(Agent):
    """Agent for system and application monitoring"""
    
    def __init__(self, agent_id: str, log_dir: str):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "system_metrics",
                "process_monitoring",
                "network_monitoring",
                "log_analysis",
                "alert_management",
                "health_check"
            ]
        )
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_history: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        
    async def process_task(self, task: Task) -> TaskResult:
        """Process monitoring tasks"""
        with Timer(f"Monitoring task {task.task_id}") as timer:
            try:
                if task.task_type == "system_metrics":
                    output = self._collect_system_metrics()
                elif task.task_type == "process_monitoring":
                    output = self._monitor_processes(task.parameters)
                elif task.task_type == "network_monitoring":
                    output = await self._monitor_network(task.parameters)
                elif task.task_type == "log_analysis":
                    output = self._analyze_logs(task.input_data, task.parameters)
                elif task.task_type == "alert_management":
                    output = self._manage_alerts(task.input_data, task.parameters)
                elif task.task_type == "health_check":
                    output = await self._perform_health_check(task.input_data, task.parameters)
                else:
                    raise ValueError(f"Unsupported task type: {task.task_type}")
                
                # Store metrics if applicable
                if task.task_type in ["system_metrics", "process_monitoring", "network_monitoring"]:
                    self.metrics_history.append({
                        "timestamp": datetime.now(),
                        "task_type": task.task_type,
                        "metrics": output
                    })
                    
                    # Check alert rules
                    await self._check_alert_rules(output)
                
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    output=output,
                    processing_time=timer.duration,
                    agent_id=self.agent_id,
                    metadata={"metrics_count": len(self.metrics_history)}
                )
            except Exception as e:
                logger.error(f"Monitoring error in task {task.task_id}: {str(e)}")
                return TaskResult(
                    task_id=task.task_id,
                    status="failed",
                    output=None,
                    processing_time=timer.duration,
                    agent_id=self.agent_id,
                    error=str(e)
                )
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle incoming messages"""
        if message.message_type == "metrics_request":
            metric_type = message.content.get("metric_type")
            duration = message.content.get("duration", "1h")
            
            # Filter metrics by type and time
            duration_seconds = self._parse_duration(duration)
            cutoff_time = datetime.now() - timedelta(seconds=duration_seconds)
            
            filtered_metrics = [
                m for m in self.metrics_history
                if (metric_type is None or m["task_type"] == metric_type) and
                m["timestamp"] >= cutoff_time
            ]
            
            return Message(
                sender=self.agent_id,
                content=filtered_metrics,
                message_type="metrics_response"
            )
        elif message.message_type == "alert_config":
            # Configure alert rules
            self.alert_rules.update(message.content)
            return Message(
                sender=self.agent_id,
                content={"status": "configured", "rules": len(self.alert_rules)},
                message_type="alert_config_response"
            )
        elif message.message_type == "alert_status":
            return Message(
                sender=self.agent_id,
                content={
                    "active_alerts": len(self.alerts),
                    "alert_history": self.alerts[-10:]  # Last 10 alerts
                },
                message_type="alert_status_response"
            )
        return None
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-wide metrics"""
        cpu_times = psutil.cpu_times()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "cores": psutil.cpu_count(),
                "times": {
                    "user": cpu_times.user,
                    "system": cpu_times.system,
                    "idle": cpu_times.idle
                }
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "system": {
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "platform": platform.platform(),
                "python_version": platform.python_version()
            }
        }
        
        return metrics
    
    def _monitor_processes(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor specific processes or all processes"""
        process_list = []
        target_processes = parameters.get("processes", [])
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                pinfo = proc.info
                if not target_processes or pinfo['name'] in target_processes:
                    process_list.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "cpu_percent": pinfo['cpu_percent'],
                        "memory_percent": pinfo['memory_percent'],
                        "status": pinfo['status']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            "processes": process_list,
            "total_processes": len(process_list)
        }
    
    async def _monitor_network(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor network connections and perform connectivity tests"""
        # Get network interfaces
        interfaces = psutil.net_if_stats()
        
        # Get network connections
        connections = psutil.net_connections()
        
        # Perform connectivity tests if endpoints specified
        connectivity_results = {}
        if "endpoints" in parameters:
            async with aiohttp.ClientSession() as session:
                for endpoint in parameters["endpoints"]:
                    try:
                        async with session.get(endpoint) as response:
                            connectivity_results[endpoint] = {
                                "status": response.status,
                                "response_time": response.elapsed.total_seconds()
                            }
                    except Exception as e:
                        connectivity_results[endpoint] = {
                            "status": "error",
                            "error": str(e)
                        }
        
        return {
            "interfaces": {
                name: {
                    "isup": stats.isup,
                    "duplex": stats.duplex,
                    "speed": stats.speed,
                    "mtu": stats.mtu
                }
                for name, stats in interfaces.items()
            },
            "connections": [
                {
                    "local_address": f"{conn.laddr.ip}:{conn.laddr.port}",
                    "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                    "status": conn.status,
                    "pid": conn.pid
                }
                for conn in connections if conn.type == socket.SOCK_STREAM
            ],
            "connectivity_tests": connectivity_results
        }
    
    def _analyze_logs(self, log_data: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze log files or log data"""
        patterns = parameters.get("patterns", [])
        severity_levels = parameters.get("severity_levels", ["ERROR", "WARNING", "INFO"])
        
        analysis = {
            "matches": [],
            "severity_counts": {level: 0 for level in severity_levels},
            "timestamp_distribution": {}
        }
        
        # Process log lines
        for line in log_data.splitlines():
            # Extract timestamp if present
            timestamp_match = parameters.get("timestamp_pattern", "").search(line)
            if timestamp_match:
                timestamp = timestamp_match.group(0)
                analysis["timestamp_distribution"][timestamp] = \
                    analysis["timestamp_distribution"].get(timestamp, 0) + 1
            
            # Check severity levels
            for level in severity_levels:
                if level in line:
                    analysis["severity_counts"][level] += 1
            
            # Check patterns
            for pattern in patterns:
                if pattern in line:
                    analysis["matches"].append({
                        "pattern": pattern,
                        "line": line
                    })
        
        return analysis
    
    def _manage_alerts(self, alert_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Manage alert rules and handle alert notifications"""
        operation = parameters.get("operation", "create")
        
        if operation == "create":
            # Add new alert rule
            rule_id = alert_data["rule_id"]
            self.alert_rules[rule_id] = {
                "condition": alert_data["condition"],
                "threshold": alert_data["threshold"],
                "severity": alert_data.get("severity", "warning"),
                "notification": alert_data.get("notification", {})
            }
            return {"status": "created", "rule_id": rule_id}
            
        elif operation == "delete":
            # Remove alert rule
            rule_id = alert_data["rule_id"]
            if rule_id in self.alert_rules:
                del self.alert_rules[rule_id]
                return {"status": "deleted", "rule_id": rule_id}
            return {"status": "not_found", "rule_id": rule_id}
            
        elif operation == "list":
            # List all alert rules
            return {"rules": self.alert_rules}
            
        elif operation == "clear":
            # Clear alerts
            self.alerts = []
            return {"status": "cleared"}
            
        else:
            raise ValueError(f"Unsupported alert operation: {operation}")
    
    async def _perform_health_check(self, targets: List[str], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform health checks on specified targets"""
        results = {}
        
        for target in targets:
            if target == "system":
                # Check system health
                results["system"] = self._check_system_health()
            elif target == "processes":
                # Check process health
                results["processes"] = self._check_process_health(parameters.get("process_list", []))
            elif target == "network":
                # Check network health
                results["network"] = await self._check_network_health(
                    parameters.get("endpoints", [])
                )
            elif target == "disk":
                # Check disk health
                results["disk"] = self._check_disk_health(
                    parameters.get("thresholds", {"usage": 90})
                )
            else:
                results[target] = {"status": "unknown", "error": "Unsupported target"}
        
        return results
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        status = "healthy"
        issues = []
        
        if cpu_percent > 90:
            status = "warning"
            issues.append("High CPU usage")
            
        if memory.percent > 90:
            status = "warning"
            issues.append("High memory usage")
            
        return {
            "status": status,
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "issues": issues
        }
    
    def _check_process_health(self, process_list: List[str]) -> Dict[str, Any]:
        """Check health of specific processes"""
        results = {}
        
        for process_name in process_list:
            process_found = False
            for proc in psutil.process_iter(['name', 'status']):
                try:
                    if proc.info['name'] == process_name:
                        process_found = True
                        results[process_name] = {
                            "status": "running" if proc.info['status'] == "running" else "warning",
                            "pid": proc.pid
                        }
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            if not process_found:
                results[process_name] = {
                    "status": "not_found",
                    "error": "Process not running"
                }
        
        return results
    
    async def _check_network_health(self, endpoints: List[str]) -> Dict[str, Any]:
        """Check network connectivity and health"""
        results = {
            "connectivity": {},
            "interfaces": {}
        }
        
        # Check endpoints
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    start_time = datetime.now()
                    async with session.get(endpoint) as response:
                        response_time = (datetime.now() - start_time).total_seconds()
                        results["connectivity"][endpoint] = {
                            "status": "healthy" if response.status == 200 else "warning",
                            "response_time": response_time,
                            "status_code": response.status
                        }
                except Exception as e:
                    results["connectivity"][endpoint] = {
                        "status": "error",
                        "error": str(e)
                    }
        
        # Check network interfaces
        for name, stats in psutil.net_if_stats().items():
            results["interfaces"][name] = {
                "status": "up" if stats.isup else "down",
                "speed": stats.speed
            }
        
        return results
    
    def _check_disk_health(self, thresholds: Dict[str, float]) -> Dict[str, Any]:
        """Check disk health and usage"""
        results = {}
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                status = "healthy"
                
                if usage.percent > thresholds.get("usage", 90):
                    status = "warning"
                
                results[partition.mountpoint] = {
                    "status": status,
                    "usage_percent": usage.percent,
                    "free_space": usage.free,
                    "filesystem": partition.fstype
                }
            except Exception as e:
                results[partition.mountpoint] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    async def _check_alert_rules(self, metrics: Dict[str, Any]) -> None:
        """Check metrics against alert rules"""
        for rule_id, rule in self.alert_rules.items():
            try:
                # Evaluate condition
                condition = rule["condition"]
                threshold = rule["threshold"]
                
                # Extract metric value using the condition path
                value = metrics
                for key in condition.split('.'):
                    value = value[key]
                
                if value > threshold:
                    alert = {
                        "rule_id": rule_id,
                        "timestamp": datetime.now(),
                        "severity": rule["severity"],
                        "message": f"Metric {condition} exceeded threshold: {value} > {threshold}"
                    }
                    
                    self.alerts.append(alert)
                    
                    # Handle notification if configured
                    if "notification" in rule:
                        await self._send_notification(alert, rule["notification"])
                        
            except Exception as e:
                logger.error(f"Error checking alert rule {rule_id}: {str(e)}")
    
    async def _send_notification(self, alert: Dict[str, Any], config: Dict[str, Any]) -> None:
        """Send alert notification"""
        method = config.get("method", "log")
        
        if method == "log":
            logger.warning(f"Alert: {alert['message']}")
        elif method == "http":
            # Send HTTP webhook
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        config["url"],
                        json=alert,
                        headers=config.get("headers", {})
                    ) as response:
                        if response.status != 200:
                            logger.error(f"Failed to send alert notification: {response.status}")
                except Exception as e:
                    logger.error(f"Error sending alert notification: {str(e)}")
    
    @staticmethod
    def _parse_duration(duration: str) -> int:
        """Parse duration string to seconds"""
        unit = duration[-1]
        value = int(duration[:-1])
        
        if unit == 's':
            return value
        elif unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 3600
        elif unit == 'd':
            return value * 86400
        else:
            raise ValueError(f"Invalid duration unit: {unit}")
