#!/usr/bin/env python3
"""
ARBITech Dashboard Verification Script

This script verifies that the dashboard system is properly installed
and ready to use. It checks all components and provides a system status.

Usage:
    python verify_dashboard.py
"""

import os
import sys
from pathlib import Path

def check_file_structure():
    """Verify the file structure is complete."""
    print("📁 Checking File Structure...")
    
    ui_dir = Path(__file__).parent
    required_files = [
        "__init__.py",
        "dashboard.py", 
        "README.md",
        "requirements.txt",
        "config.py",
        "start_dashboard.py",
        "demo_dashboard.py",
        "quick_start.py",
        "tests/__init__.py",
        "tests/test_dashboard.py"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = ui_dir / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"  ✅ {file} ({size:,} bytes)")
        else:
            print(f"  ❌ {file} - Missing")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_dashboard_imports():
    """Check if dashboard can be imported."""
    print("\n🔧 Checking Dashboard Imports...")
    
    try:
        # Add parent directory to path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from ui.dashboard import DashboardUI, UserSession, DashboardStats
        print("  ✅ DashboardUI class imported")
        print("  ✅ UserSession class imported")
        print("  ✅ DashboardStats class imported")
        
        # Test basic instantiation
        dashboard = DashboardUI(host="localhost", port=8080)
        print("  ✅ Dashboard instance created successfully")
        
        # Test mock data generation
        mock_data = dashboard.create_mock_data()
        if 'opportunities' in mock_data and 'trades' in mock_data:
            print("  ✅ Mock data generation working")
        else:
            print("  ❌ Mock data generation failed")
            
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available."""
    print("\n📦 Checking Dependencies...")
    
    dependencies = [
        'websockets',
        'asyncio',
        'json',
        'logging',
        'datetime',
        'threading',
        'dataclasses',
        'pathlib',
        'http.server',
        'urllib.parse',
        'uuid'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep} - Missing")
            missing.append(dep)
    
    return len(missing) == 0

def check_web_assets():
    """Check if web assets can be created."""
    print("\n🌐 Checking Web Assets...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from ui.dashboard import DashboardUI
        
        # Create temporary dashboard instance
        dashboard = DashboardUI(host="localhost", port=8080)
        dashboard._setup_web_assets()
        
        web_dir = dashboard.web_dir
        html_file = web_dir / "dashboard.html"
        css_file = web_dir / "dashboard.css"
        js_file = web_dir / "dashboard.js"
        
        files_exist = True
        if html_file.exists():
            print(f"  ✅ HTML template ({html_file.stat().st_size:,} bytes)")
        else:
            print("  ❌ HTML template missing")
            files_exist = False
            
        if css_file.exists():
            print(f"  ✅ CSS styles ({css_file.stat().st_size:,} bytes)")
        else:
            print("  ❌ CSS styles missing")
            files_exist = False
            
        if js_file.exists():
            print(f"  ✅ JavaScript ({js_file.stat().st_size:,} bytes)")
        else:
            print("  ❌ JavaScript missing")
            files_exist = False
        
        return files_exist
        
    except Exception as e:
        print(f"  ❌ Error creating web assets: {e}")
        return False

def show_system_stats():
    """Show system statistics."""
    print("\n📊 System Statistics:")
    
    ui_dir = Path(__file__).parent
    
    # Count files
    py_files = list(ui_dir.rglob("*.py"))
    md_files = list(ui_dir.rglob("*.md"))
    txt_files = list(ui_dir.rglob("*.txt"))
    
    total_lines = 0
    for py_file in py_files:
        try:
            with open(py_file, 'r') as f:
                total_lines += len(f.readlines())
        except:
            pass
    
    print(f"  📁 Python files: {len(py_files)}")
    print(f"  📄 Documentation files: {len(md_files)}")
    print(f"  📝 Text files: {len(txt_files)}")
    print(f"  📏 Total lines of code: {total_lines:,}")
    print(f"  💾 Directory size: {sum(f.stat().st_size for f in ui_dir.rglob('*') if f.is_file()):,} bytes")

def show_next_steps():
    """Show next steps for users."""
    print("\n🚀 Next Steps:")
    print("="*50)
    print("1. Install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print("2. Start the dashboard:")
    print("   python start_dashboard.py --dev")
    print("   or")
    print("   python quick_start.py")
    print()
    print("3. Run the demo:")
    print("   python demo_dashboard.py --demo-mode")
    print()
    print("4. Run tests:")
    print("   python tests/test_dashboard.py")
    print()
    print("5. Access dashboard:")
    print("   🌐 Web Interface: http://localhost:8080")
    print("   🔌 WebSocket: ws://localhost:8765")

def main():
    """Main verification function."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   ARBITECH DASHBOARD VERIFICATION                            ║
║                        System Status Check                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    checks = [
        ("File Structure", check_file_structure),
        ("Dependencies", check_dependencies),
        ("Dashboard Imports", check_dashboard_imports),
        ("Web Assets", check_web_assets)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} failed: {e}")
            all_passed = False
    
    show_system_stats()
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Dashboard system is ready!")
        print("🎉 The ARBITech Dashboard UI system has been successfully implemented.")
        show_next_steps()
    else:
        print("❌ SOME CHECKS FAILED - Please review the errors above")
        print("🔧 Fix the issues and run this verification again")
    print("="*80)

if __name__ == "__main__":
    main()