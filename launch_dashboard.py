#!/usr/bin/env python3
"""
Quick Launcher for EV Manufacturing Integration Dashboard
Simplified script to start the web-based visualization
"""
import os
import sys
import subprocess
import webbrowser
import time
import threading

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['flask', 'flask_socketio']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies():
    """Install missing dependencies"""
    print("📦 Installing dashboard dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "flask>=2.3.0", 
            "flask-socketio>=5.3.0",
            "eventlet>=0.33.0"
        ])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def start_dashboard():
    """Start the dashboard server"""
    try:
        # Import after potential installation
        from dashboard_server import main as dashboard_main
        
        print("🏭 Starting EV Manufacturing Integration Dashboard...")
        print("📊 Features:")
        print("   • Real-time PLC → OPC UA → SCADA → MES → DATABASE flow")
        print("   • Live production monitoring")
        print("   • Interactive system controls")
        print("   • Visual data flow animation")
        print()
        
        # Start dashboard server
        dashboard_main()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try installing dependencies first:")
        print("   pip install flask flask-socketio eventlet")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

def open_browser_delayed():
    """Open browser after a short delay"""
    time.sleep(3)  # Wait for server to start
    webbrowser.open('http://localhost:5000')

def main():
    """Main launcher function"""
    print("🚀 EV Manufacturing Integration Dashboard Launcher")
    print("=" * 55)
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"⚠️  Missing dependencies: {', '.join(missing)}")
        response = input("📦 Install missing dependencies? (y/N): ").lower().strip()
        
        if response in ['y', 'yes']:
            if not install_dependencies():
                print("❌ Cannot proceed without dependencies")
                return
        else:
            print("💡 Install manually with:")
            print("   pip install flask flask-socketio eventlet")
            return
    
    # Ask if user wants to auto-open browser
    browser_response = input("🌐 Open dashboard in browser automatically? (Y/n): ").lower().strip()
    
    if browser_response not in ['n', 'no']:
        # Start browser opening in background
        browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
        browser_thread.start()
    
    print("\n🎯 Dashboard will be available at: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 55)
    
    # Start dashboard
    start_dashboard()

if __name__ == "__main__":
    main()
