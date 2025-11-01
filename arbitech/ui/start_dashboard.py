#!/usr/bin/env python3
"""
ARBitech Dashboard Startup Script

Simple script to start the ARBitech dashboard with sensible defaults.
Provides easy launch options for development and production use.

Usage:
    python start_dashboard.py [--dev] [--port PORT] [--host HOST]

Options:
    --dev         Start in development mode with debug logging
    --port PORT   Port to run the dashboard on (default: 8080)
    --host HOST   Host to bind to (default: 0.0.0.0)
    --demo        Start with demo mode and mock data
    --help        Show this help message
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/workspace/arbitech/logs/dashboard.log')
        ]
    )

def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []
    
    try:
        import websockets
    except ImportError:
        missing_deps.append('websockets')
    
    try:
        import aiohttp
    except ImportError:
        missing_deps.append('aiohttp')
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Please install them using:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    
    return True

async def start_dashboard(host: str, port: int, debug: bool = False):
    """Start the ARBitech dashboard."""
    try:
        from ui.dashboard import DashboardUI
        
        logging.info(f"🚀 Starting ARBitech Dashboard on {host}:{port}")
        logging.info(f"📱 Dashboard URL: http://{host}:{port}")
        logging.info(f"🔌 WebSocket URL: ws://{host}:8765")
        
        # Create and configure dashboard
        dashboard = DashboardUI(
            host=host,
            port=port
        )
        
        # Start the dashboard
        await dashboard.start()
        
    except KeyboardInterrupt:
        logging.info("🛑 Dashboard stopped by user")
    except Exception as e:
        logging.error(f"❌ Dashboard error: {e}")
        if debug:
            raise

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Start the ARBitech Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_dashboard.py --dev
  python start_dashboard.py --port 3000 --host localhost
  python start_dashboard.py --demo
  python start_dashboard.py --port 443 --host 0.0.0.0
        """
    )
    
    parser.add_argument(
        "--dev", 
        action="store_true",
        help="Start in development mode with debug logging"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)"
    )
    
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Start with demo mode and mock data"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.dev)
    
    # Print startup banner
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                            ARBITECH DASHBOARD                                ║
║                    Real-Time Trading Monitor & Control                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🎯 Features:                                                                 ║
║     • Real-time WebSocket updates for live trading data                     ║
║     • Interactive arbitrage opportunity monitoring                          ║
║     • Trade execution tracking with progress indicators                     ║
║     • Performance analytics with interactive charts                         ║
║     • System health monitoring and diagnostics                              ║
║     • User management and preference settings                               ║
║     • Responsive design for desktop and mobile                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create logs directory if it doesn't exist
    os.makedirs('/workspace/arbitech/logs', exist_ok=True)
    
    # Handle demo mode
    if args.demo:
        print("🎮 Starting in demo mode with mock data...")
        print("📝 Demo will generate realistic trading data for testing")
        
        try:
            from ui.demo_dashboard import main as demo_main
            # Create mock arguments for demo
            import sys
            sys.argv = [
                'demo_dashboard.py',
                '--host', args.host,
                '--port', str(args.port),
                '--demo-mode'
            ]
            demo_main()
        except ImportError:
            logging.error("Demo modules not available")
            print("❌ Demo mode requires ui.demo_dashboard module")
            sys.exit(1)
        
        return
    
    # Start regular dashboard
    try:
        print(f"🌐 Starting dashboard server...")
        print(f"📡 Host: {args.host}")
        print(f"🔌 Port: {args.port}")
        
        if args.dev:
            print("🔍 Debug mode enabled")
        
        print("\n" + "="*80)
        print("🚀 Dashboard is starting...")
        print("="*80 + "\n")
        
        asyncio.run(start_dashboard(args.host, args.port, args.dev))
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        logging.error(f"Failed to start dashboard: {e}")
        if args.dev:
            raise
        sys.exit(1)

if __name__ == "__main__":
    main()