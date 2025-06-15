"""Data analysis and processing tools for MCP server."""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import sqlite3
from pathlib import Path

from src.core import mcp_tool

logger = logging.getLogger(__name__)


def register_data_tools(server, config):
    """Register data analysis tools with the MCP server."""
    
    server.register_tool(
        name="data_analysis",
        description="Analyze data and generate insights",
        handler=data_analysis,
        returns="Data analysis results"
    )
    
    server.register_tool(
        name="data_transformation",
        description="Transform and clean data",
        handler=data_transformation,
        returns="Data transformation results"
    )
    
    server.register_tool(
        name="data_visualization",
        description="Create data visualizations and charts",
        handler=data_visualization,
        returns="Data visualization results"
    )
    
    server.register_tool(
        name="database_operations",
        description="Perform database operations and queries",
        handler=database_operations,
        returns="Database operation results"
    )
    
    logger.info("Registered data analysis tools")


@mcp_tool(
    name="data_analysis",
    description="Analyze data and generate insights",
    category="data",
    tags=["analysis", "statistics", "insights"]
)
async def data_analysis(
    data_source: str, 
    analysis_type: str = "descriptive", 
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze data and generate insights.
    
    Args:
        data_source: Source of data (file path, database query, etc.)
        analysis_type: Type of analysis (descriptive, correlation, trend, statistical)
        options: Additional analysis options
    """
    try:
        options = options or {}
        
        # Load data based on source type
        if data_source.endswith('.csv'):
            data = pd.read_csv(data_source)
        elif data_source.endswith('.xlsx') or data_source.endswith('.xls'):
            data = pd.read_excel(data_source)
        elif data_source.endswith('.json'):
            with open(data_source, 'r') as f:
                json_data = json.load(f)
                data = pd.DataFrame(json_data)
        else:
            return {"status": "error", "message": f"Unsupported data source format: {data_source}"}
        
        results = {
            "data_source": data_source,
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat(),
            "data_shape": data.shape,
            "columns": data.columns.tolist()
        }
        
        if analysis_type == "descriptive":
            results["descriptive_stats"] = data.describe().to_dict()
            results["data_types"] = data.dtypes.to_dict()
            results["missing_values"] = data.isnull().sum().to_dict()
            
        elif analysis_type == "correlation":
            numeric_data = data.select_dtypes(include=[np.number])
            if not numeric_data.empty:
                results["correlation_matrix"] = numeric_data.corr().to_dict()
            else:
                results["correlation_matrix"] = "No numeric columns found"
                
        elif analysis_type == "trend":
            if options.get("date_column"):
                date_col = options["date_column"]
                if date_col in data.columns:
                    data[date_col] = pd.to_datetime(data[date_col])
                    data = data.sort_values(date_col)
                    
                    if options.get("value_column"):
                        value_col = options["value_column"]
                        if value_col in data.columns:
                            trend_data = data.groupby(data[date_col].dt.date)[value_col].sum()
                            results["trend_analysis"] = trend_data.to_dict()
                            
        elif analysis_type == "statistical":
            numeric_data = data.select_dtypes(include=[np.number])
            if not numeric_data.empty:
                results["statistical_summary"] = {
                    "mean": numeric_data.mean().to_dict(),
                    "median": numeric_data.median().to_dict(),
                    "std": numeric_data.std().to_dict(),
                    "skewness": numeric_data.skew().to_dict(),
                    "kurtosis": numeric_data.kurtosis().to_dict()
                }
        
        return {
            "status": "success",
            "message": f"Data analysis completed: {analysis_type}",
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Error in data analysis: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="data_transformation",
    description="Transform and clean data",
    category="data",
    tags=["transformation", "cleaning", "preprocessing"]
)
async def data_transformation(
    data_source: str,
    transformations: List[Dict[str, Any]],
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transform and clean data.
    
    Args:
        data_source: Source data file path
        transformations: List of transformation operations
        output_file: Output file path (optional)
    """
    try:
        # Load data
        if data_source.endswith('.csv'):
            data = pd.read_csv(data_source)
        elif data_source.endswith('.xlsx') or data_source.endswith('.xls'):
            data = pd.read_excel(data_source)
        else:
            return {"status": "error", "message": f"Unsupported data source format: {data_source}"}
        
        original_shape = data.shape
        transformation_log = []
        
        # Apply transformations
        for transform in transformations:
            operation = transform.get("operation")
            
            if operation == "remove_duplicates":
                before_count = len(data)
                data = data.drop_duplicates()
                after_count = len(data)
                transformation_log.append({
                    "operation": operation,
                    "removed_rows": before_count - after_count
                })
                
            elif operation == "fill_missing":
                column = transform.get("column")
                method = transform.get("method", "forward")
                if column and column in data.columns:
                    if method == "forward":
                        data[column] = data[column].fillna(method='ffill')
                    elif method == "backward":
                        data[column] = data[column].fillna(method='bfill')
                    elif method == "mean":
                        data[column] = data[column].fillna(data[column].mean())
                    elif method == "median":
                        data[column] = data[column].fillna(data[column].median())
                    transformation_log.append({
                        "operation": operation,
                        "column": column,
                        "method": method
                    })
                    
            elif operation == "convert_type":
                column = transform.get("column")
                new_type = transform.get("type")
                if column and column in data.columns:
                    try:
                        data[column] = data[column].astype(new_type)
                        transformation_log.append({
                            "operation": operation,
                            "column": column,
                            "new_type": new_type
                        })
                    except Exception as e:
                        transformation_log.append({
                            "operation": operation,
                            "column": column,
                            "error": str(e)
                        })
                        
            elif operation == "filter_rows":
                condition = transform.get("condition")
                if condition:
                    before_count = len(data)
                    data = data.query(condition)
                    after_count = len(data)
                    transformation_log.append({
                        "operation": operation,
                        "condition": condition,
                        "removed_rows": before_count - after_count
                    })
        
        # Save transformed data if output file specified
        if output_file:
            if output_file.endswith('.csv'):
                data.to_csv(output_file, index=False)
            elif output_file.endswith('.xlsx'):
                data.to_excel(output_file, index=False)
        
        return {
            "status": "success",
            "message": "Data transformation completed",
            "data": {
                "original_shape": original_shape,
                "final_shape": data.shape,
                "transformations_applied": len(transformations),
                "transformation_log": transformation_log,
                "output_file": output_file
            }
        }
        
    except Exception as e:
        logger.error(f"Error in data transformation: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="data_visualization",
    description="Create data visualizations",
    category="data",
    tags=["visualization", "charts", "graphs"]
)
async def data_visualization(
    data_source: str,
    chart_type: str,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create data visualizations and charts.
    
    Args:
        data_source: Source data file path
        chart_type: Type of chart (bar, line, scatter, histogram, pie)
        options: Chart configuration options
    """
    try:
        options = options or {}
        
        # Load data
        if data_source.endswith('.csv'):
            data = pd.read_csv(data_source)
        elif data_source.endswith('.xlsx') or data_source.endswith('.xls'):
            data = pd.read_excel(data_source)
        else:
            return {"status": "error", "message": f"Unsupported data source format: {data_source}"}
        
        # Generate chart configuration (in a real implementation, this would create actual charts)
        chart_config = {
            "chart_type": chart_type,
            "data_source": data_source,
            "data_shape": data.shape,
            "timestamp": datetime.now().isoformat()
        }
        
        if chart_type == "bar":
            x_column = options.get("x_column")
            y_column = options.get("y_column")
            if x_column and y_column and x_column in data.columns and y_column in data.columns:
                chart_config["configuration"] = {
                    "x_axis": x_column,
                    "y_axis": y_column,
                    "data_points": len(data)
                }
                
        elif chart_type == "line":
            x_column = options.get("x_column")
            y_column = options.get("y_column")
            if x_column and y_column and x_column in data.columns and y_column in data.columns:
                chart_config["configuration"] = {
                    "x_axis": x_column,
                    "y_axis": y_column,
                    "data_points": len(data)
                }
                
        elif chart_type == "histogram":
            column = options.get("column")
            if column and column in data.columns:
                chart_config["configuration"] = {
                    "column": column,
                    "bins": options.get("bins", 10),
                    "data_points": len(data)
                }
        
        return {
            "status": "success",
            "message": f"Chart configuration generated: {chart_type}",
            "data": chart_config
        }
        
    except Exception as e:
        logger.error(f"Error in data visualization: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="database_operations",
    description="Perform database operations",
    category="data",
    tags=["database", "sql", "queries"]
)
async def database_operations(
    operation: str,
    database_path: Optional[str] = None,
    query: Optional[str] = None,
    table_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Perform database operations and queries.
    
    Args:
        operation: Database operation (create, query, insert, update, delete)
        database_path: Path to SQLite database file
        query: SQL query to execute
        table_data: Data for table operations
    """
    try:
        if not database_path:
            database_path = "temp_database.db"
        
        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()
            
            if operation == "create_table":
                if not table_data:
                    return {"status": "error", "message": "Table data required for create operation"}
                
                table_name = table_data.get("table_name")
                columns = table_data.get("columns", [])
                
                column_defs = []
                for col in columns:
                    col_name = col.get("name")
                    col_type = col.get("type", "TEXT")
                    constraints = col.get("constraints", "")
                    column_defs.append(f"{col_name} {col_type} {constraints}")
                
                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
                cursor.execute(create_sql)
                
                return {
                    "status": "success",
                    "message": f"Table {table_name} created successfully",
                    "data": {"table_name": table_name, "columns": len(columns)}
                }
                
            elif operation == "query":
                if not query:
                    return {"status": "error", "message": "SQL query required for query operation"}
                
                cursor.execute(query)
                if query.strip().upper().startswith("SELECT"):
                    results = cursor.fetchall()
                    columns = [description[0] for description in cursor.description]
                    
                    return {
                        "status": "success",
                        "message": "Query executed successfully",
                        "data": {
                            "columns": columns,
                            "rows": results,
                            "row_count": len(results)
                        }
                    }
                else:
                    conn.commit()
                    return {
                        "status": "success",
                        "message": "Query executed successfully",
                        "data": {"affected_rows": cursor.rowcount}
                    }
                    
            elif operation == "insert_data":
                if not table_data:
                    return {"status": "error", "message": "Table data required for insert operation"}
                
                table_name = table_data.get("table_name")
                data_rows = table_data.get("data", [])
                
                if data_rows:
                    columns = list(data_rows[0].keys())
                    placeholders = ', '.join(['?' for _ in columns])
                    column_names = ', '.join(columns)
                    
                    insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                    
                    for row in data_rows:
                        values = [row.get(col) for col in columns]
                        cursor.execute(insert_sql, values)
                    
                    conn.commit()
                    
                    return {
                        "status": "success",
                        "message": f"Inserted {len(data_rows)} rows into {table_name}",
                        "data": {"table_name": table_name, "inserted_rows": len(data_rows)}
                    }
                    
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
                
    except Exception as e:
        logger.error(f"Error in database operations: {e}")
        return {"status": "error", "message": str(e)}
