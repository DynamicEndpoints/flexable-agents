import json
from typing import Any, Dict, List, Optional
import time
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {str(e)}")
        return {}

def save_results(results: Any, output_path: str):
    """Save results to a JSON file"""
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving results to {output_path}: {str(e)}")

class Timer:
    """Context manager for timing operations"""
    
    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, *args):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"{self.description} took {duration:.2f} seconds")
        return False
        
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

class RateLimiter:
    """Rate limiter for API calls or other operations"""
    
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        
    async def acquire(self):
        """Acquire a slot for an operation"""
        now = time.time()
        
        # Remove old calls
        self.calls = [t for t in self.calls if now - t < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            # Wait until we can make another call
            sleep_time = self.calls[0] + self.time_window - now
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                
        self.calls.append(now)
        
class Cache:
    """Simple in-memory cache with expiration"""
    
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache:
            item = self.cache[key]
            if time.time() - item['timestamp'] < self.ttl:
                return item['value']
            else:
                del self.cache[key]
        return None
        
    def set(self, key: str, value: Any):
        """Set value in cache with current timestamp"""
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
        
    def clear(self):
        """Clear all expired items from cache"""
        now = time.time()
        expired_keys = [
            k for k, v in self.cache.items()
            if now - v['timestamp'] > self.ttl
        ]
        for k in expired_keys:
            del self.cache[k]

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

async def retry_async(
    func,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Retry an async function with exponential backoff"""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = delay * (backoff_factor ** attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed with error: {str(e)}. "
                    f"Retrying in {wait_time:.2f} seconds..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"All {max_retries} attempts failed. "
                    f"Last error: {str(last_exception)}"
                )
                raise last_exception
