#!/usr/bin/env python
"""
Application management script for ChatOps MVP.
Handles starting and stopping both frontend and backend servers.
"""
import os
import sys
import subprocess
import signal
import time
import psutil
import webbrowser
from pathlib import Path

def find_process_by_port(port):
    """Find process using specified port."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

def kill_process_on_port(port):
    """Kill process using specified port."""
    proc = find_process_by_port(port)
    if proc:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            proc.kill()
        print(f"Killed process on port {port}")
    else:
        print(f"No process found on port {port}")

def start_servers():
    """Start both frontend and backend servers."""
    # Kill any existing processes on our ports
    kill_process_on_port(5173)  # Frontend
    kill_process_on_port(8000)  # Backend
    
    # Get the root directory
    root_dir = Path(__file__).parent.absolute()
    
    # Start backend server
    backend_dir = root_dir / 'backend'
    backend_cmd = [sys.executable, '-m', 'uvicorn', 'app.main:app', '--reload', '--port', '8000']
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=str(backend_dir),
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    print("Started backend server")
    
    # Start frontend server
    frontend_dir = root_dir / 'frontend'
    npm_path = 'npm.cmd' if sys.platform == 'win32' else 'npm'
    frontend_cmd = [npm_path, 'run', 'dev']
    
    try:
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd=str(frontend_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print("Started frontend server")
    except Exception as e:
        print(f"Error starting frontend server: {e}")
        print("Make sure Node.js and npm are installed and in your PATH")
        backend_process.terminate()
        sys.exit(1)
    
    # Wait for servers to start
    time.sleep(3)
    
    # Open browser
    webbrowser.open('http://localhost:5173')
    
    print("\nServers started successfully!")
    print("Frontend running on: http://localhost:5173")
    print("Backend running on: http://localhost:8000")
    print("\nPress Ctrl+C to stop all servers...")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_servers()

def stop_servers():
    """Stop all running servers."""
    print("\nStopping servers...")
    kill_process_on_port(5173)  # Frontend
    kill_process_on_port(8000)  # Backend
    print("All servers stopped")

def main():
    """Main entry point."""
    if len(sys.argv) != 2 or sys.argv[1] not in ['start', 'stop']:
        print("Usage: python manage.py [start|stop]")
        sys.exit(1)
    
    command = sys.argv[1]
    if command == 'start':
        start_servers()
    else:
        stop_servers()

if __name__ == '__main__':
    main() 