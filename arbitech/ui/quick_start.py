#!/usr/bin/env python3
"""
ARBITech Dashboard - Quick Start Guide

This script provides a quick overview and easy access to the dashboard features.
Run this to see available options and start the dashboard.

Usage:
    python quick_start.py
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def print_banner():
    """Print the ARBITech dashboard banner."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ARBITECH DASHBOARD SYSTEM                            ║
║                    Real-Time Trading Monitor & Control                       ║
║                                                                              ║
║  🎯 Comprehensive Features:                                                   ║
║     ✓ Real-time WebSocket updates for live trading data                     ║
║     ✓ Interactive arbitrage opportunity monitoring                          ║
║     ✓ Trade execution tracking with progress indicators                     ║
║     ✓ Performance analytics with interactive charts                         ║
║     ✓ System health monitoring and diagnostics                              ║
║     ✓ User management and preference settings                               ║
║     ✓ Responsive design for desktop and mobile                              ║
║     ✓ Complete ARBITech platform integration                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    try:
        import websockets
        print("✅ websockets - Available")
    except ImportError:
        print("❌ websockets - Missing (pip install websockets)")
        return False
    
    try:
        import aiohttp
        print("✅ aiohttp - Available")
    except ImportError:
        print("❌ aiohttp - Missing (pip install aiohttp)")
        return False
    
    print("✅ All dependencies available\n")
    return True

def show_menu():
    """Show the main menu options."""
    print("""
📋 Available Options:
    
    1. 🚀 Start Dashboard (Development Mode)
       - Full dashboard with debug logging
       - Web interface: http://localhost:8080
       - WebSocket: ws://localhost:8765
    
    2. 🎮 Start Demo Mode
       - Interactive demo with mock data
       - Realistic trading scenarios
       - All features showcased
    
    3. 🧪 Run Tests
       - Comprehensive test suite
       - Performance validation
       - Error handling tests
    
    4. 📖 Show Documentation
       - Open README file
       - API documentation
       - Configuration guide
    
    5. ⚙️  Configuration
       - View current settings
       - Modify configuration
       - Environment variables
    
    6. 📊 System Info
       - Dashboard statistics
       - Component status
       - Performance metrics
    
    7. 🌐 Open Dashboard in Browser
       - Open current dashboard URL
       - Requires running dashboard
    
    0. ❌ Exit

""")

def start_dashboard(dev_mode=False):
    """Start the dashboard server."""
    try:
        script_path = Path(__file__).parent / "start_dashboard.py"
        
        cmd = [sys.executable, str(script_path)]
        if dev_mode:
            cmd.append("--dev")
        
        print(f"🚀 Starting dashboard...")
        print(f"📡 Command: {' '.join(cmd)}")
        
        # Start the dashboard in a subprocess
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for startup
        time.sleep(3)
        
        if process.poll() is None:  # Still running
            print("✅ Dashboard started successfully!")
            print("🌐 Dashboard URL: http://localhost:8080")
            print("🔌 WebSocket URL: ws://localhost:8765")
            
            # Ask if user wants to open browser
            try:
                response = input("\n🌍 Open dashboard in browser? (y/n): ").lower()
                if response in ['y', 'yes']:
                    webbrowser.open('http://localhost:8080')
            except KeyboardInterrupt:
                print("\n🛑 Dashboard starting in background...")
            
            print("\n💡 Press Ctrl+C to stop the dashboard")
            print("📊 Dashboard logs: /workspace/arbitech/logs/dashboard.log")
            
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping dashboard...")
                process.terminate()
                process.wait()
                
        else:
            stdout, stderr = process.communicate()
            print("❌ Failed to start dashboard")
            print(f"Error: {stderr.decode()}")
            
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

def start_demo():
    """Start the demo mode."""
    try:
        script_path = Path(__file__).parent / "demo_dashboard.py"
        
        cmd = [sys.executable, str(script_path), "--demo-mode"]
        
        print("🎮 Starting demo mode...")
        print(f"📡 Command: {' '.join(cmd)}")
        
        subprocess.run(cmd)
        
    except Exception as e:
        print(f"❌ Error starting demo: {e}")

def run_tests():
    """Run the test suite."""
    try:
        script_path = Path(__file__).parent / "tests" / "test_dashboard.py"
        
        cmd = [sys.executable, str(script_path)]
        
        print("🧪 Running test suite...")
        print(f"📡 Command: {' '.join(cmd)}")
        
        subprocess.run(cmd)
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")

def show_documentation():
    """Show documentation."""
    try:
        readme_path = Path(__file__).parent / "README.md"
        
        if readme_path.exists():
            print("📖 Opening documentation...")
            
            # Try to open in default viewer
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(str(readme_path))
                elif os.name == 'posix':  # Unix/Linux/Mac
                    subprocess.run(['open', str(readme_path)])
                print(f"📄 Documentation opened: {readme_path}")
            except:
                # Fallback to displaying content
                with open(readme_path, 'r') as f:
                    content = f.read()
                print("\n" + "="*80)
                print("ARBITECH DASHBOARD DOCUMENTATION")
                print("="*80)
                print(content[:2000] + "..." if len(content) > 2000 else content)
        else:
            print("❌ README.md not found")
            
    except Exception as e:
        print(f"❌ Error showing documentation: {e}")

def show_configuration():
    """Show current configuration."""
    try:
        config_path = Path(__file__).parent / "config.py"
        
        if config_path.exists():
            print("⚙️  Current Configuration:")
            print("="*50)
            
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Show key configuration values
            lines = content.split('\n')
            for line in lines:
                if '=' in line and not line.strip().startswith('#'):
                    print(line.strip())
                    
            print("\n📝 To modify configuration, edit config.py")
        else:
            print("❌ config.py not found")
            
    except Exception as e:
        print(f"❌ Error showing configuration: {e}")

def show_system_info():
    """Show system information."""
    print("📊 System Information:")
    print("="*50)
    
    try:
        # Check if dashboard is running
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8080))
        if result == 0:
            print("🟢 Dashboard Server: Running on port 8080")
        else:
            print("🔴 Dashboard Server: Not running")
        sock.close()
        
        # Check WebSocket port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8765))
        if result == 0:
            print("🟢 WebSocket Server: Running on port 8765")
        else:
            print("🔴 WebSocket Server: Not running")
        sock.close()
        
        # Check log file
        log_path = Path("/workspace/arbitech/logs/dashboard.log")
        if log_path.exists():
            size = log_path.stat().st_size
            print(f"📄 Log File: {log_path} ({size} bytes)")
        else:
            print("📄 Log File: Not found")
            
        # Show dashboard file info
        ui_dir = Path(__file__).parent
        file_count = len(list(ui_dir.rglob("*.py")))
        print(f"📁 UI Module: {file_count} Python files")
        
    except Exception as e:
        print(f"❌ Error getting system info: {e}")

def open_browser():
    """Open dashboard in browser."""
    try:
        print("🌐 Opening dashboard in browser...")
        webbrowser.open('http://localhost:8080')
    except Exception as e:
        print(f"❌ Error opening browser: {e}")
        print("💡 Make sure the dashboard is running first")

def main():
    """Main menu loop."""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again")
        return
    
    while True:
        try:
            show_menu()
            
            choice = input("👉 Select an option (0-7): ").strip()
            
            if choice == '1':
                start_dashboard(dev_mode=True)
            elif choice == '2':
                start_demo()
            elif choice == '3':
                run_tests()
            elif choice == '4':
                show_documentation()
            elif choice == '5':
                show_configuration()
            elif choice == '6':
                show_system_info()
            elif choice == '7':
                open_browser()
            elif choice == '0':
                print("\n👋 Thanks for using ARBITech Dashboard!")
                break
            else:
                print("❌ Invalid option. Please try again.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()