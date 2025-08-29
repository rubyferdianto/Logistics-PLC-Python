"""
Main application entry point for Logistics PLC Python system.
"""
import logging
import asyncio
import signal
import sys
from pathlib import Path

# Add app directory to Python path
sys.path.append(str(Path(__file__).parent))

from config.settings import settings
from config.database_config import init_database, test_connection
from app.plc_connection.modbus_client import ModbusClient
from app.web_dashboard.app import create_app

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class LogisticsSystemManager:
    """Main system manager for the logistics application"""
    
    def __init__(self):
        self.modbus_client = None
        self.web_app = None
        self.is_running = False
        
    async def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing Logistics PLC System...")
        
        try:
            # Initialize database
            logger.info("Initializing database...")
            if not test_connection():
                logger.error("Database connection failed")
                return False
            
            init_database()
            logger.info("Database initialized successfully")
            
            # Initialize PLC connection
            logger.info("Initializing PLC connection...")
            self.modbus_client = ModbusClient()
            
            # Test PLC connection (optional - system can run without PLC for testing)
            if self.modbus_client.test_connection():
                logger.info("PLC connection established")
            else:
                logger.warning("PLC connection failed - running in simulation mode")
            
            # Initialize web application
            logger.info("Initializing web dashboard...")
            self.web_app = create_app()
            
            logger.info("System initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            return False
    
    async def start_data_collection(self):
        """Start continuous data collection from PLC"""
        logger.info("Starting data collection service...")
        
        while self.is_running:
            try:
                if self.modbus_client and self.modbus_client.is_connected:
                    # Read sensor data
                    sensor_data = self.modbus_client.read_all_sensors()
                    
                    if sensor_data:
                        logger.debug(f"Collected sensor data: {len(sensor_data)} sensors")
                        # TODO: Store sensor data in database
                        # await self.store_sensor_data(sensor_data)
                    
                # Wait for next collection interval
                await asyncio.sleep(settings.DATA_COLLECTION_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in data collection: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def start_web_server(self):
        """Start the web dashboard server"""
        logger.info(f"Starting web server on {settings.FLASK_HOST}:{settings.FLASK_PORT}")
        
        try:
            # In production, use a proper ASGI server like Uvicorn or Hypercorn
            self.web_app.run(
                host=settings.FLASK_HOST,
                port=settings.FLASK_PORT,
                debug=settings.DEBUG
            )
        except Exception as e:
            logger.error(f"Web server error: {e}")
    
    async def run(self):
        """Run the main application"""
        self.is_running = True
        
        # Initialize system
        if not await self.initialize():
            logger.error("Failed to initialize system")
            return
        
        logger.info("Starting Logistics PLC System...")
        
        try:
            # Create tasks for concurrent execution
            tasks = [
                asyncio.create_task(self.start_data_collection()),
                # Note: Flask app.run() is blocking, so we'll start it differently in production
            ]
            
            # For development, start web server in separate process or thread
            if settings.DEBUG:
                logger.info("Starting web dashboard...")
                self.web_app.run(
                    host=settings.FLASK_HOST,
                    port=settings.FLASK_PORT,
                    debug=False,  # Disable debug in threaded mode
                    threaded=True
                )
            
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown of all services"""
        logger.info("Shutting down system...")
        self.is_running = False
        
        # Disconnect from PLC
        if self.modbus_client:
            self.modbus_client.disconnect()
        
        logger.info("System shutdown completed")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    sys.exit(0)

async def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run system manager
    system_manager = LogisticsSystemManager()
    await system_manager.run()

if __name__ == "__main__":
    print("="*60)
    print("🚀 Starting Logistics PLC Python System")
    print(f"📊 Version: {settings.APP_VERSION}")
    print(f"🔧 Debug Mode: {settings.DEBUG}")
    print(f"🌐 Web Interface: http://{settings.FLASK_HOST}:{settings.FLASK_PORT}")
    print(f"🏭 PLC Host: {settings.PLC_HOST}:{settings.PLC_PORT}")
    print("="*60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
