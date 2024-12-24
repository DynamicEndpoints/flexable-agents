from typing import Optional, Dict, Any, List
import os
import json
import csv
import yaml
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil
from datetime import datetime

from ..core.base import Agent, Task, TaskResult, Message
from ..utils.helpers import Timer

class FileProcessingAgent(Agent):
    """Agent for handling file operations and conversions"""
    
    def __init__(self, agent_id: str, work_dir: str):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "file_read",
                "file_write",
                "file_convert",
                "file_organize",
                "file_search"
            ]
        )
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.processed_files: List[Dict[str, Any]] = []
        
    async def process_task(self, task: Task) -> TaskResult:
        """Process file-related tasks"""
        with Timer(f"File task {task.task_id}") as timer:
            try:
                if task.task_type == "file_read":
                    output = self._read_file(task.input_data, task.parameters)
                elif task.task_type == "file_write":
                    output = self._write_file(task.input_data, task.parameters)
                elif task.task_type == "file_convert":
                    output = self._convert_file(task.input_data, task.parameters)
                elif task.task_type == "file_organize":
                    output = self._organize_files(task.input_data, task.parameters)
                elif task.task_type == "file_search":
                    output = self._search_files(task.input_data, task.parameters)
                else:
                    raise ValueError(f"Unsupported task type: {task.task_type}")
                
                # Record processing history
                self.processed_files.append({
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "timestamp": datetime.now(),
                    "file_path": str(task.input_data)
                })
                
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    output=output,
                    processing_time=timer.duration,
                    agent_id=self.agent_id,
                    metadata={"file_count": len(self.processed_files)}
                )
            except Exception as e:
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
        if message.message_type == "status_request":
            return Message(
                sender=self.agent_id,
                content={
                    "status": self.status,
                    "files_processed": len(self.processed_files),
                    "work_dir": str(self.work_dir)
                },
                message_type="status_response"
            )
        elif message.message_type == "history_request":
            return Message(
                sender=self.agent_id,
                content=self.processed_files,
                message_type="history_response"
            )
        return None
    
    def _read_file(self, file_path: str, parameters: Dict[str, Any]) -> Any:
        """Read file content based on file type"""
        path = Path(file_path)
        file_type = parameters.get("file_type", path.suffix[1:])
        
        with open(path, "r", encoding=parameters.get("encoding", "utf-8")) as f:
            if file_type == "json":
                return json.load(f)
            elif file_type == "csv":
                return list(csv.DictReader(f))
            elif file_type == "yaml" or file_type == "yml":
                return yaml.safe_load(f)
            elif file_type == "xml":
                return ET.parse(f)
            else:
                return f.read()
    
    def _write_file(self, content: Any, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to file"""
        file_path = Path(parameters["file_path"])
        file_type = parameters.get("file_type", file_path.suffix[1:])
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        mode = "w" if file_type not in ["bytes", "binary"] else "wb"
        encoding = parameters.get("encoding", "utf-8") if mode == "w" else None
        
        with open(file_path, mode, encoding=encoding) as f:
            if file_type == "json":
                json.dump(content, f, indent=2)
            elif file_type == "csv":
                writer = csv.DictWriter(f, fieldnames=content[0].keys())
                writer.writeheader()
                writer.writerows(content)
            elif file_type in ["yaml", "yml"]:
                yaml.safe_dump(content, f)
            elif file_type == "xml":
                content.write(f)
            else:
                f.write(content)
                
        return {
            "file_path": str(file_path),
            "size": file_path.stat().st_size
        }
    
    def _convert_file(self, file_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Convert file from one format to another"""
        content = self._read_file(file_path, parameters)
        output_path = parameters["output_path"]
        
        result = self._write_file(content, {
            "file_path": output_path,
            "file_type": parameters["output_type"]
        })
        
        return {
            "input_path": file_path,
            "output_path": output_path,
            "conversion": f"{parameters.get('file_type', 'txt')} -> {parameters['output_type']}"
        }
    
    def _organize_files(self, directory: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Organize files in directory based on rules"""
        dir_path = Path(directory)
        organization_type = parameters.get("organize_by", "extension")
        recursive = parameters.get("recursive", False)
        
        moved_files = []
        
        for item in dir_path.glob("**/*" if recursive else "*"):
            if item.is_file():
                if organization_type == "extension":
                    target_dir = dir_path / item.suffix[1:]
                elif organization_type == "date":
                    date = datetime.fromtimestamp(item.stat().st_mtime)
                    target_dir = dir_path / str(date.year) / str(date.month)
                elif organization_type == "size":
                    size_mb = item.stat().st_size / (1024 * 1024)
                    if size_mb < 1:
                        category = "small"
                    elif size_mb < 100:
                        category = "medium"
                    else:
                        category = "large"
                    target_dir = dir_path / category
                else:
                    continue
                
                target_dir.mkdir(parents=True, exist_ok=True)
                target_path = target_dir / item.name
                
                shutil.move(str(item), str(target_path))
                moved_files.append({
                    "file": item.name,
                    "source": str(item),
                    "destination": str(target_path)
                })
        
        return {
            "organized_by": organization_type,
            "files_moved": len(moved_files),
            "details": moved_files
        }
    
    def _search_files(self, directory: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search for files matching criteria"""
        dir_path = Path(directory)
        pattern = parameters.get("pattern", "*")
        recursive = parameters.get("recursive", False)
        
        matches = []
        for item in dir_path.glob("**/*" if recursive else "*"):
            if item.is_file():
                if item.match(pattern):
                    matches.append({
                        "path": str(item),
                        "size": item.stat().st_size,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
        
        return {
            "pattern": pattern,
            "matches_found": len(matches),
            "matches": matches
        }
