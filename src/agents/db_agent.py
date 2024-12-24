from typing import Optional, Dict, Any, List, Union
import asyncio
import asyncpg
import pandas as pd
from datetime import datetime
import json
import logging

from ..core.base import Agent, Task, TaskResult, Message
from ..utils.helpers import Timer, RateLimiter

logger = logging.getLogger(__name__)

class DatabaseAgent(Agent):
    """Agent for handling database operations"""
    
    def __init__(
        self,
        agent_id: str,
        connection_params: Dict[str, str],
        max_connections: int = 10
    ):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "query",
                "execute",
                "batch_operation",
                "schema_inspection",
                "data_migration",
                "backup_restore"
            ]
        )
        self.connection_params = connection_params
        self.pool = None
        self.max_connections = max_connections
        self.query_history: List[Dict[str, Any]] = []
        self.rate_limiter = RateLimiter(max_calls=100, time_window=60)
        
    async def initialize(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(
            **self.connection_params,
            min_size=1,
            max_size=self.max_connections
        )
        
    async def cleanup(self):
        """Cleanup database connections"""
        if self.pool:
            await self.pool.close()
            
    async def process_task(self, task: Task) -> TaskResult:
        """Process database-related tasks"""
        if not self.pool:
            await self.initialize()
            
        with Timer(f"DB task {task.task_id}") as timer:
            try:
                await self.rate_limiter.acquire()
                
                if task.task_type == "query":
                    output = await self._execute_query(task.input_data, task.parameters)
                elif task.task_type == "execute":
                    output = await self._execute_statement(task.input_data, task.parameters)
                elif task.task_type == "batch_operation":
                    output = await self._execute_batch(task.input_data, task.parameters)
                elif task.task_type == "schema_inspection":
                    output = await self._inspect_schema(task.input_data, task.parameters)
                elif task.task_type == "data_migration":
                    output = await self._migrate_data(task.input_data, task.parameters)
                elif task.task_type == "backup_restore":
                    output = await self._backup_restore(task.input_data, task.parameters)
                else:
                    raise ValueError(f"Unsupported task type: {task.task_type}")
                    
                # Record query history
                self.query_history.append({
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "timestamp": datetime.now(),
                    "duration": timer.duration
                })
                
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    output=output,
                    processing_time=timer.duration,
                    agent_id=self.agent_id,
                    metadata={"query_count": len(self.query_history)}
                )
            except Exception as e:
                logger.error(f"Database error in task {task.task_id}: {str(e)}")
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
        if message.message_type == "connection_status":
            status = "connected" if self.pool else "disconnected"
            return Message(
                sender=self.agent_id,
                content={
                    "status": status,
                    "queries_executed": len(self.query_history)
                },
                message_type="connection_status_response"
            )
        elif message.message_type == "query_history":
            return Message(
                sender=self.agent_id,
                content=self.query_history,
                message_type="query_history_response"
            )
        return None
    
    async def _execute_query(self, query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a SELECT query"""
        async with self.pool.acquire() as connection:
            # Execute query
            results = await connection.fetch(
                query,
                *parameters.get("params", [])
            )
            
            # Convert results to dict
            columns = [desc for desc in results[0].keys()] if results else []
            rows = [dict(row) for row in results]
            
            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows)
            }
    
    async def _execute_statement(self, statement: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a non-SELECT statement"""
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                result = await connection.execute(
                    statement,
                    *parameters.get("params", [])
                )
                
                return {
                    "status": "success",
                    "affected_rows": result.split()[-1] if result else 0
                }
    
    async def _execute_batch(self, statements: List[str], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multiple statements in a transaction"""
        results = []
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                for statement in statements:
                    result = await connection.execute(statement)
                    results.append(result)
                    
        return {
            "status": "success",
            "results": results,
            "total_statements": len(statements)
        }
    
    async def _inspect_schema(self, target: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect database schema"""
        async with self.pool.acquire() as connection:
            if target == "tables":
                query = """
                    SELECT table_name, column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = $1
                    ORDER BY table_name, ordinal_position
                """
                results = await connection.fetch(query, parameters.get("schema", "public"))
                
                # Organize results by table
                schema_info = {}
                for row in results:
                    table = row["table_name"]
                    if table not in schema_info:
                        schema_info[table] = []
                    schema_info[table].append({
                        "column": row["column_name"],
                        "type": row["data_type"],
                        "nullable": row["is_nullable"]
                    })
                    
                return {"tables": schema_info}
            
            elif target == "indexes":
                query = """
                    SELECT
                        t.relname as table_name,
                        i.relname as index_name,
                        a.attname as column_name
                    FROM
                        pg_class t,
                        pg_class i,
                        pg_index ix,
                        pg_attribute a
                    WHERE
                        t.oid = ix.indrelid
                        AND i.oid = ix.indexrelid
                        AND a.attrelid = t.oid
                        AND a.attnum = ANY(ix.indkey)
                        AND t.relkind = 'r'
                    ORDER BY
                        t.relname,
                        i.relname
                """
                results = await connection.fetch(query)
                
                # Organize results by table
                index_info = {}
                for row in results:
                    table = row["table_name"]
                    if table not in index_info:
                        index_info[table] = {}
                    index_name = row["index_name"]
                    if index_name not in index_info[table]:
                        index_info[table][index_name] = []
                    index_info[table][index_name].append(row["column_name"])
                    
                return {"indexes": index_info}
            
            else:
                raise ValueError(f"Unsupported schema inspection target: {target}")
    
    async def _migrate_data(self, migration_config: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate data between tables or databases"""
        source = migration_config["source"]
        target = migration_config["target"]
        mappings = migration_config["mappings"]
        
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                # Extract data from source
                source_query = f"SELECT {', '.join(mappings.keys())} FROM {source}"
                source_data = await connection.fetch(source_query)
                
                # Transform data according to mappings
                target_columns = list(mappings.values())
                transformed_data = []
                for row in source_data:
                    transformed_row = []
                    for source_col in mappings.keys():
                        transformed_row.append(row[source_col])
                    transformed_data.append(transformed_row)
                
                # Load data into target
                target_cols = ', '.join(target_columns)
                placeholders = ', '.join(f'${i+1}' for i in range(len(target_columns)))
                insert_query = f"INSERT INTO {target} ({target_cols}) VALUES ({placeholders})"
                
                results = await connection.executemany(insert_query, transformed_data)
                
                return {
                    "status": "success",
                    "rows_migrated": len(transformed_data),
                    "source": source,
                    "target": target
                }
    
    async def _backup_restore(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform backup or restore operations"""
        if operation == "backup":
            tables = parameters.get("tables", [])
            backup_data = {}
            
            async with self.pool.acquire() as connection:
                for table in tables:
                    # Get table schema
                    schema_query = f"""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = $1
                        ORDER BY ordinal_position
                    """
                    schema = await connection.fetch(schema_query, table)
                    
                    # Get table data
                    data_query = f"SELECT * FROM {table}"
                    data = await connection.fetch(data_query)
                    
                    backup_data[table] = {
                        "schema": [dict(row) for row in schema],
                        "data": [dict(row) for row in data]
                    }
            
            # Save backup to file if path provided
            if "backup_path" in parameters:
                with open(parameters["backup_path"], 'w') as f:
                    json.dump(backup_data, f, default=str)
            
            return {
                "status": "success",
                "tables_backed_up": len(tables),
                "total_records": sum(len(t["data"]) for t in backup_data.values())
            }
            
        elif operation == "restore":
            if "backup_path" in parameters:
                with open(parameters["backup_path"], 'r') as f:
                    backup_data = json.load(f)
            else:
                backup_data = parameters["backup_data"]
            
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    for table, data in backup_data.items():
                        # Recreate table if specified
                        if parameters.get("recreate_tables", False):
                            # Drop existing table
                            await connection.execute(f"DROP TABLE IF EXISTS {table}")
                            
                            # Create table
                            columns = []
                            for col in data["schema"]:
                                nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
                                columns.append(f"{col['column_name']} {col['data_type']} {nullable}")
                            
                            create_query = f"CREATE TABLE {table} ({', '.join(columns)})"
                            await connection.execute(create_query)
                        
                        # Insert data
                        if data["data"]:
                            columns = data["data"][0].keys()
                            placeholders = ', '.join(f'${i+1}' for i in range(len(columns)))
                            insert_query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                            
                            # Convert data to list of tuples
                            values = [[row[col] for col in columns] for row in data["data"]]
                            await connection.executemany(insert_query, values)
            
            return {
                "status": "success",
                "tables_restored": len(backup_data),
                "total_records": sum(len(t["data"]) for t in backup_data.values())
            }
        
        else:
            raise ValueError(f"Unsupported backup/restore operation: {operation}")
