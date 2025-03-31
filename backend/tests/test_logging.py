"""
Test suite for validating the logging system.
"""
import pytest
import aiohttp
import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
LOG_DIR = Path("logs")
LOG_FILES = {
    "app": "app.log",
    "error": "error.log",
    "json": "json.log",
    "performance": "perf.log"  # Fixed file name to match config
}

async def clean_logs():
    """Clean all log files before testing."""
    for log_file in LOG_FILES.values():
        log_path = LOG_DIR / log_file
        try:
            if log_path.exists():
                # Try to open and truncate the file instead of deleting
                with open(log_path, 'w') as f:
                    f.truncate(0)
        except (PermissionError, OSError) as e:
            # If we can't truncate, just log a warning and continue
            print(f"Warning: Could not clean log file {log_path}: {str(e)}")
            continue
    
    # Create logs directory if it doesn't exist
    LOG_DIR.mkdir(exist_ok=True)

def check_log_format(log_file: Path) -> dict:
    """
    Check log file format and return statistics.
    
    Args:
        log_file (Path): Path to log file
        
    Returns:
        dict: Log statistics and format validation results
    """
    stats = {
        "exists": log_file.exists(),
        "size": log_file.stat().st_size if log_file.exists() else 0,
        "line_count": 0,
        "valid_json_count": 0 if "json" in log_file.name else None,
        "has_timestamps": False,
        "has_log_levels": False,
        "has_request_ids": False
    }
    
    if not stats["exists"]:
        return stats
        
    with open(log_file, "r") as f:
        for line in f:
            stats["line_count"] += 1
            
            # Check JSON format for json.log
            if "json" in log_file.name:
                try:
                    log_entry = json.loads(line)
                    stats["valid_json_count"] += 1
                    stats["has_timestamps"] |= "timestamp" in log_entry
                    stats["has_log_levels"] |= "level" in log_entry
                    stats["has_request_ids"] |= "request_id" in log_entry
                except json.JSONDecodeError:
                    continue
            else:
                # Check standard log format
                stats["has_timestamps"] |= " | " in line
                stats["has_log_levels"] |= any(level in line for level in ["INFO", "WARNING", "ERROR", "DEBUG"])
                stats["has_request_ids"] |= "request_id" in line
                
    return stats

async def test_basic_logging():
    """Test basic logging functionality."""
    await clean_logs()
    
    # Make a series of API calls
    async with aiohttp.ClientSession() as session:
        # Health check
        await session.get(f"{BASE_URL}/api/v1/health")
        
        # Chat endpoint
        chat_payload = {
            "messages": [{"role": "user", "content": "Test message"}],
            "stream": False
        }
        await session.post(f"{BASE_URL}/api/v1/chat", json=chat_payload)
        
        # LLM endpoint
        llm_payload = {
            "provider": "mock",
            "model": "mock-model",
            "prompt": "Test prompt",
            "stream": False
        }
        await session.post(f"{BASE_URL}/api/llm/generate", json=llm_payload)
        
    # Wait for logs to be written
    await asyncio.sleep(1)
    
    # Check log files
    results = {}
    for log_type, log_file in LOG_FILES.items():
        results[log_type] = check_log_format(LOG_DIR / log_file)
    
    return results

async def test_error_logging():
    """Test error logging scenarios."""
    # Make invalid requests
    async with aiohttp.ClientSession() as session:
        # Invalid JSON
        response = await session.post(
            f"{BASE_URL}/api/v1/chat",
            data="invalid json"
        )
        assert response.status in [400, 422]
        
        # Missing required fields
        response = await session.post(
            f"{BASE_URL}/api/v1/chat",
            json={}
        )
        assert response.status in [400, 422]
        
        # Invalid endpoint
        response = await session.get(f"{BASE_URL}/invalid/endpoint")
        assert response.status == 404
    
    # Check error log
    error_log = LOG_DIR / LOG_FILES["error"]
    return check_log_format(error_log)

async def test_performance_logging():
    """Test performance logging under load."""
    # Generate load
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(10):
            tasks.append(session.get(f"{BASE_URL}/api/v1/health"))
        await asyncio.gather(*tasks)
    
    # Check performance log
    perf_log = LOG_DIR / LOG_FILES["performance"]
    return check_log_format(perf_log)

async def test_security_logging():
    """Test security-related logging features."""
    sensitive_data = {
        "api_key": "test_key_123",
        "password": "secret123",
        "token": "bearer_token_123",
        "messages": [{"role": "user", "content": "Test message"}]
    }
    
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            f"{BASE_URL}/api/v1/chat",
            json=sensitive_data,
            headers={"Authorization": "Bearer test_token"}
        )
    
    # Check logs for sensitive data
    results = {}
    for log_type, log_file in LOG_FILES.items():
        log_path = LOG_DIR / log_file
        if not log_path.exists():
            continue
            
        with open(log_path, "r") as f:
            content = f.read()
            results[log_type] = {
                "contains_api_key": sensitive_data["api_key"] in content,
                "contains_password": sensitive_data["password"] in content,
                "contains_token": sensitive_data["token"] in content,
                "contains_redacted": "***REDACTED***" in content
            }
    
    return results

async def run_all_tests():
    """Run all logging tests and generate report."""
    test_results = {
        "basic_logging": await test_basic_logging(),
        "error_logging": await test_error_logging(),
        "performance_logging": await test_performance_logging(),
        "security_logging": await test_security_logging()
    }
    
    # Generate test report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "test_results": test_results,
        "summary": {
            "all_logs_created": all(
                result.get("exists", False)
                for result in test_results["basic_logging"].values()
            ),
            "json_log_valid": test_results["basic_logging"]["json"]["valid_json_count"] > 0,
            "error_logging_working": test_results["error_logging"]["line_count"] > 0,
            "performance_metrics_captured": test_results["performance_logging"]["line_count"] > 0,
            "security_measures_effective": not any(
                any(check for check in checks.values() if "contains_" in check and "redacted" not in check)
                for checks in test_results["security_logging"].values()
            )
        }
    }
    
    return report

if __name__ == "__main__":
    report = asyncio.run(run_all_tests())
    print(json.dumps(report, indent=2)) 