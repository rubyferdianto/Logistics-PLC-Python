#!/usr/bin/env python3
"""
Startup script for PLC -> OPC UA -> MES -> DATABASE Integration
EV Manufacturing System
"""
import asyncio
import sys
import os
import argparse
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the integration orchestrator
try:
    from integration_orchestrator import IntegrationOrchestrator
    from config.settings import Settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ev_manufacturing_integration.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'asyncua',
        'pandas',
        'sqlite3',  # Built-in
        'flask',
        'paho-mqtt'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            elif package == 'asyncua':
                import asyncua
            elif package == 'pandas':
                import pandas
            elif package == 'flask':
                import flask
            elif package == 'paho-mqtt':
                import paho.mqtt.client as mqtt
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements_integration.txt")
        return False
    
    return True

def print_banner():
    """Print startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    EV Manufacturing Integration System                        ║
    ║    PLC → OPC UA → MES → DATABASE                              ║
    ║                                                              ║
    ║    Components:                                               ║
    ║    • PLC Communication via OPC UA                           ║
    ║    • Manufacturing Execution System (MES)                   ║
    ║    • Real-time Database Integration                         ║
    ║    • Production Monitoring & Analytics                      ║
    ║    • Quality Control System                                 ║
    ║    • Inventory Management                                   ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_system_info():
    """Print system configuration information"""
    settings = Settings()
    
    print("🔧 System Configuration:")
    print(f"   📡 OPC UA Endpoint: {settings.OPCUA_ENDPOINT}")
    print(f"   📊 Database: {settings.DATABASE_URL}")
    print(f"   🌐 MQTT Broker: {settings.MQTT_BROKER}")
    print(f"   🏭 MES Database: {settings.MES_DATABASE_PATH}")
    print(f"   📈 Auto Scheduling: {settings.MES_AUTO_SCHEDULING}")
    print()

async def run_integration_system(args):
    """Run the integration system"""
    print("🚀 Starting EV Manufacturing Integration System...")
    
    # Create orchestrator
    orchestrator = IntegrationOrchestrator()
    
    # Print system info
    if args.show_config:
        system_info = orchestrator.get_system_info()
        print(f"📊 System Info: {system_info}")
    
    try:
        # Start the system
        await orchestrator.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logging.error(f"System error: {e}")
    finally:
        print("🔄 Shutting down system...")
        await orchestrator.stop()
        print("✅ System shutdown complete")

def run_simulator_mode():
    """Run in simulator mode (MQTT-based simulation)"""
    print("🎮 Running in Simulator Mode...")
    print("Starting MQTT-based EV manufacturing simulation...")
    
    try:
        # Import and run the MQTT simulator
        from scripts.mqtt_simulator_advanced import EVManufacturingSimulator
        
        simulator = EVManufacturingSimulator()
        simulator.start()
        
        # Keep running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping simulator...")
            simulator.stop()
            
    except ImportError:
        print("❌ MQTT simulator not available")
        print("Run: python scripts/mqtt_simulator_advanced.py")

def run_database_setup():
    """Setup and initialize the database"""
    print("📊 Setting up database...")
    
    try:
        from app.database.enhanced_db_manager import EnhancedDatabaseManager, DatabaseConfig
        
        db_config = DatabaseConfig(
            db_path="ev_manufacturing.db",
            enable_wal=True
        )
        
        db_manager = EnhancedDatabaseManager(db_config)
        print("✅ Database initialized successfully")
        
        # Test database operations
        print("🧪 Testing database operations...")
        
        # Test storing data
        db_manager.store_plc_data(
            node_id="test_node",
            value="test_value",
            node_name="Test Node"
        )
        
        # Test system health
        health = db_manager.get_system_health()
        print(f"🏥 System Health: {health}")
        
        print("✅ Database setup complete")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="EV Manufacturing Integration System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_integration.py                    # Run full integration system
  python start_integration.py --simulator       # Run MQTT simulator only
  python start_integration.py --setup-db        # Setup database only
  python start_integration.py --debug           # Run with debug logging
  python start_integration.py --show-config     # Show configuration info
        """
    )
    
    parser.add_argument(
        '--simulator',
        action='store_true',
        help='Run in simulator mode (MQTT-based)'
    )
    
    parser.add_argument(
        '--setup-db',
        action='store_true',
        help='Setup and initialize database'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Show system configuration'
    )
    
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check if all dependencies are installed'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.debug else args.log_level
    setup_logging(log_level)
    
    # Print banner
    print_banner()
    
    # Check dependencies
    if args.check_deps or not check_requirements():
        if not check_requirements():
            sys.exit(1)
        else:
            print("✅ All dependencies are installed")
            return
    
    # Print system info
    print_system_info()
    
    # Handle different modes
    if args.setup_db:
        run_database_setup()
    elif args.simulator:
        run_simulator_mode()
    else:
        # Run full integration system
        try:
            asyncio.run(run_integration_system(args))
        except KeyboardInterrupt:
            print("\n🛑 System interrupted by user")
        except Exception as e:
            print(f"❌ System error: {e}")
            logging.error(f"System error: {e}")
        finally:
            print("👋 EV Manufacturing Integration System terminated")

if __name__ == "__main__":
    main()
