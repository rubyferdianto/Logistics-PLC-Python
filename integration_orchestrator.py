"""
Integration Orchestrator for PLC -> OPC UA -> MES -> DATABASE
Main system that coordinates all components in the EV manufacturing pipeline
"""
import asyncio
import logging
import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import signal
import sys
from pathlib import Path

# Import our custom modules
try:
    from app.plc_connection.opcua_client import OPCUAClient, PLCDataHandler
    from app.mes_system.mes_core import MESSystem, ProductionOrder, ProductionStatus
    from app.database.enhanced_db_manager import EnhancedDatabaseManager, DatabaseConfig
    from config.settings import Settings
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are installed and paths are correct")

logger = logging.getLogger(__name__)

@dataclass
class SystemStatus:
    """Overall system status"""
    plc_connected: bool = False
    opcua_connected: bool = False
    mes_running: bool = False
    database_connected: bool = False
    last_update: str = ""
    error_count: int = 0
    uptime_seconds: int = 0

class IntegrationOrchestrator:
    """Main orchestrator for PLC -> OPC UA -> MES -> DATABASE integration"""
    
    def __init__(self, config_file: str = None):
        # Load configuration
        self.settings = Settings()
        
        # Initialize components
        self.opcua_client = None
        self.mes_system = None
        self.db_manager = None
        
        # System state
        self.system_status = SystemStatus()
        self.running = False
        self.start_time = None
        
        # Data processing
        self.data_queue = asyncio.Queue()
        self.processing_tasks = []
        
        # Statistics
        self.stats = {
            'messages_processed': 0,
            'orders_created': 0,
            'quality_tests': 0,
            'material_movements': 0,
            'system_events': 0
        }
        
        # Setup logging
        self._setup_logging()
        
        # Initialize signal handlers
        self._setup_signal_handlers()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ev_manufacturing_system.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self) -> bool:
        """Initialize all system components"""
        logger.info("🏭 Initializing EV Manufacturing Integration System...")
        
        try:
            # Initialize Database
            logger.info("📊 Initializing Database Manager...")
            db_config = DatabaseConfig(
                db_path=self.settings.DATABASE_URL.replace('sqlite:///', ''),
                enable_wal=True
            )
            self.db_manager = EnhancedDatabaseManager(db_config)
            self.system_status.database_connected = True
            logger.info("✅ Database Manager initialized")
            
            # Initialize MES System
            logger.info("🏭 Initializing MES System...")
            self.mes_system = MESSystem(db_config.db_path)
            self.mes_system.start()
            self.system_status.mes_running = True
            logger.info("✅ MES System initialized")
            
            # Initialize OPC UA Client
            logger.info("🔌 Initializing OPC UA Client...")
            self.opcua_client = OPCUAClient(
                endpoint=self.settings.OPCUA_ENDPOINT,
                namespace=self.settings.OPCUA_NAMESPACE
            )
            
            # Set up data handler for OPC UA
            data_handler = PLCDataHandler(callback=self._handle_opcua_data)
            self.opcua_client.data_handler = data_handler
            
            # Try to connect to OPC UA server
            if await self.opcua_client.connect():
                self.system_status.opcua_connected = True
                logger.info("✅ OPC UA Client connected")
                
                # Subscribe to all PLC nodes
                await self.opcua_client.subscribe_to_nodes(callback=self._handle_opcua_data)
                logger.info("✅ Subscribed to PLC nodes")
            else:
                logger.warning("⚠️ OPC UA connection failed, will retry...")
            
            # Log system initialization
            self.db_manager.log_system_event(
                event_type="INFO",
                severity=1,
                source_system="Integration_Orchestrator",
                message="System initialized successfully",
                details=f"Components: Database ✅, MES ✅, OPC UA {'✅' if self.system_status.opcua_connected else '⚠️'}"
            )
            
            self.system_status.last_update = datetime.now().isoformat()
            logger.info("🚀 EV Manufacturing Integration System initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing system: {e}")
            self.db_manager.log_system_event(
                event_type="ERROR",
                severity=5,
                source_system="Integration_Orchestrator",
                message="System initialization failed",
                details=str(e)
            )
            return False
    
    def _handle_opcua_data(self, data_point: Dict):
        """Handle incoming OPC UA data"""
        try:
            # Queue data for processing
            asyncio.create_task(self.data_queue.put(data_point))
            
        except Exception as e:
            logger.error(f"Error handling OPC UA data: {e}")
    
    async def start(self):
        """Start the integration system"""
        if not await self.initialize():
            logger.error("Failed to initialize system")
            return False
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("🚀 Starting EV Manufacturing Integration System...")
        
        # Start processing tasks
        self.processing_tasks = [
            asyncio.create_task(self._data_processor()),
            asyncio.create_task(self._system_monitor()),
            asyncio.create_task(self._opcua_reconnector()),
            asyncio.create_task(self._production_scheduler()),
            asyncio.create_task(self._quality_monitor()),
            asyncio.create_task(self._inventory_monitor())
        ]
        
        # Log system start
        self.db_manager.log_system_event(
            event_type="INFO",
            severity=1,
            source_system="Integration_Orchestrator",
            message="System started successfully",
            details="All processing tasks initiated"
        )
        
        logger.info("✅ EV Manufacturing Integration System is running!")
        
        # Wait for all tasks
        try:
            await asyncio.gather(*self.processing_tasks)
        except Exception as e:
            logger.error(f"Error in processing tasks: {e}")
        
        return True
    
    async def stop(self):
        """Stop the integration system"""
        logger.info("🛑 Stopping EV Manufacturing Integration System...")
        
        self.running = False
        
        # Cancel all tasks
        for task in self.processing_tasks:
            task.cancel()
        
        # Stop MES system
        if self.mes_system:
            self.mes_system.stop()
        
        # Disconnect OPC UA
        if self.opcua_client:
            await self.opcua_client.disconnect()
        
        # Log system stop
        if self.db_manager:
            self.db_manager.log_system_event(
                event_type="INFO",
                severity=1,
                source_system="Integration_Orchestrator",
                message="System stopped gracefully",
                details=f"Uptime: {self._get_uptime()}"
            )
        
        logger.info("✅ EV Manufacturing Integration System stopped")
    
    async def _data_processor(self):
        """Main data processing loop"""
        logger.info("📊 Starting data processor...")
        
        while self.running:
            try:
                # Process queued data
                data_point = await asyncio.wait_for(self.data_queue.get(), timeout=1.0)
                await self._process_data_point(data_point)
                self.stats['messages_processed'] += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in data processor: {e}")
                self.system_status.error_count += 1
    
    async def _process_data_point(self, data_point: Dict):
        """Process individual data point through the pipeline"""
        try:
            # Store raw PLC data in database
            self.db_manager.store_plc_data(
                node_id=data_point.get('node_id', ''),
                value=data_point.get('value'),
                quality=data_point.get('quality', 'Good'),
                conveyor_id=self._extract_conveyor_id(data_point.get('node_id', ''))
            )
            
            # Process through MES system
            self.mes_system.process_opcua_data(data_point)
            
            # Extract and process specific data types
            await self._process_specific_data(data_point)
            
        except Exception as e:
            logger.error(f"Error processing data point: {e}")
    
    def _extract_conveyor_id(self, node_id: str) -> Optional[str]:
        """Extract conveyor ID from OPC UA node ID"""
        if '.C1.' in node_id:
            return 'C1'
        elif '.C2.' in node_id:
            return 'C2'
        elif '.C3.' in node_id:
            return 'C3'
        return None
    
    async def _process_specific_data(self, data_point: Dict):
        """Process specific types of data"""
        node_id = data_point.get('node_id', '')
        value = data_point.get('value')
        
        # Production data
        if 'Production.Count' in node_id:
            conveyor_id = self._extract_conveyor_id(node_id)
            if conveyor_id:
                # Update production metrics
                metrics = {
                    'units_produced': value,
                    'production_rate': value * 60,  # Approximate rate
                    'efficiency': 85.0,  # Example calculation
                    'quality_pass_rate': 98.5,
                    'downtime_minutes': 0.0
                }
                self.db_manager.store_production_metrics(conveyor_id, metrics)
        
        # Quality data
        elif 'Quality.LastTestResult' in node_id:
            await self._process_quality_data(value)
        
        # Warehouse data
        elif 'Warehouse' in node_id:
            await self._process_warehouse_data(node_id, value)
        
        # System alarms
        elif 'EmergencyStop' in node_id or 'Fault' in node_id:
            if value:  # Alarm active
                self.db_manager.log_system_event(
                    event_type="ALARM",
                    severity=4,
                    source_system="PLC",
                    source_component=self._extract_conveyor_id(node_id) or "System",
                    message=f"System alarm: {node_id}",
                    details=f"Alarm value: {value}"
                )
    
    async def _process_quality_data(self, test_result: Any):
        """Process quality control data"""
        try:
            # Create quality record
            quality_record = {
                'record_id': f"QC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.stats['quality_tests']:04d}",
                'product_id': f"PROD_{int(time.time())}",
                'conveyor_id': 'C1',  # Example
                'test_type': 'Electrical_Test',
                'result': 'PASS' if test_result > 0.8 else 'FAIL',
                'pass_fail': 'PASS' if test_result > 0.8 else 'FAIL',
                'measurements': {'voltage': test_result, 'resistance': 1.2},
                'tested_at': datetime.now().isoformat(),
                'operator': 'System_Auto'
            }
            
            self.db_manager.store_quality_record(quality_record)
            self.stats['quality_tests'] += 1
            
        except Exception as e:
            logger.error(f"Error processing quality data: {e}")
    
    async def _process_warehouse_data(self, node_id: str, value: Any):
        """Process warehouse inventory data"""
        try:
            # Extract warehouse and material info
            if 'Warehouse.A.' in node_id:
                warehouse_id = 'WH_A'
            elif 'Warehouse.B.' in node_id:
                warehouse_id = 'WH_B'
            elif 'Warehouse.C.' in node_id:
                warehouse_id = 'WH_C'
            else:
                return
            
            if 'Anode' in node_id:
                material_type = 'anode'
            elif 'Cathode' in node_id:
                material_type = 'cathode'
            elif 'Electrolyte' in node_id:
                material_type = 'electrolyte'
            else:
                return
            
            # Check for low inventory
            if value < 10:
                self.db_manager.log_system_event(
                    event_type="WARNING",
                    severity=3,
                    source_system="Warehouse",
                    source_component=warehouse_id,
                    message=f"Low inventory: {material_type}",
                    details=f"Current stock: {value}"
                )
            
        except Exception as e:
            logger.error(f"Error processing warehouse data: {e}")
    
    async def _system_monitor(self):
        """Monitor system health and performance"""
        logger.info("🔍 Starting system monitor...")
        
        while self.running:
            try:
                # Update system status
                self.system_status.last_update = datetime.now().isoformat()
                self.system_status.uptime_seconds = self._get_uptime_seconds()
                
                # Check component health
                await self._check_component_health()
                
                # Log periodic status
                if self.system_status.uptime_seconds % 300 == 0:  # Every 5 minutes
                    logger.info(f"System Status: {self._get_status_summary()}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in system monitor: {e}")
                await asyncio.sleep(60)
    
    async def _check_component_health(self):
        """Check health of all components"""
        # Check OPC UA connection
        if self.opcua_client:
            self.system_status.opcua_connected = self.opcua_client.connected
        
        # Check MES system
        self.system_status.mes_running = self.mes_system.running if self.mes_system else False
        
        # Check database
        try:
            health = self.db_manager.get_system_health()
            self.system_status.database_connected = health.get('system_status') != 'ERROR'
        except:
            self.system_status.database_connected = False
    
    async def _opcua_reconnector(self):
        """Monitor and reconnect OPC UA if needed"""
        logger.info("🔄 Starting OPC UA reconnector...")
        
        while self.running:
            try:
                if not self.system_status.opcua_connected and self.opcua_client:
                    logger.info("Attempting to reconnect OPC UA...")
                    if await self.opcua_client.connect():
                        await self.opcua_client.subscribe_to_nodes(callback=self._handle_opcua_data)
                        logger.info("✅ OPC UA reconnected successfully")
                        
                        self.db_manager.log_system_event(
                            event_type="INFO",
                            severity=2,
                            source_system="OPC_UA",
                            message="OPC UA reconnected successfully"
                        )
                
                await asyncio.sleep(30)  # Try reconnect every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in OPC UA reconnector: {e}")
                await asyncio.sleep(60)
    
    async def _production_scheduler(self):
        """Handle production scheduling and order management"""
        logger.info("📅 Starting production scheduler...")
        
        while self.running:
            try:
                # Auto-create production orders based on demand
                await self._create_scheduled_orders()
                
                # Check order completion and start new ones
                await self._manage_production_orders()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in production scheduler: {e}")
                await asyncio.sleep(120)
    
    async def _create_scheduled_orders(self):
        """Create production orders based on schedule"""
        # Example: Create orders every hour
        if datetime.now().minute == 0:  # Top of the hour
            product_types = ["Li-Ion_18650", "Li-Ion_21700", "LiFePO4_26650"]
            
            for i, product_type in enumerate(product_types):
                order_id = self.mes_system.create_production_order(
                    product_type=product_type,
                    quantity=50 + (i * 25),  # Varying quantities
                    priority=3 - i  # Higher priority for first product
                )
                
                logger.info(f"Created scheduled production order: {order_id}")
                self.stats['orders_created'] += 1
    
    async def _manage_production_orders(self):
        """Manage active production orders"""
        if self.mes_system:
            status = self.mes_system.get_production_status()
            
            # Log production status periodically
            if datetime.now().minute % 15 == 0:  # Every 15 minutes
                logger.info(f"Production Status: Active={status['active_orders']}, "
                          f"Completed={status['completed_orders']}, "
                          f"Pending={status['pending_orders']}")
    
    async def _quality_monitor(self):
        """Monitor quality metrics and trends"""
        logger.info("🔍 Starting quality monitor...")
        
        while self.running:
            try:
                # Get quality trends
                quality_data = self.db_manager.get_quality_trends(days=1)
                
                # Check for quality issues
                for conveyor_id, data in quality_data.get('trends', {}).items():
                    pass_rate = data.get('pass_rate', 100)
                    if pass_rate < 95:  # Quality threshold
                        self.db_manager.log_system_event(
                            event_type="WARNING",
                            severity=3,
                            source_system="Quality_Monitor",
                            source_component=conveyor_id,
                            message=f"Low quality pass rate: {pass_rate:.1f}%",
                            details=f"Total tests: {data.get('total_tests', 0)}"
                        )
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in quality monitor: {e}")
                await asyncio.sleep(600)
    
    async def _inventory_monitor(self):
        """Monitor inventory levels and trigger restocking"""
        logger.info("📦 Starting inventory monitor...")
        
        while self.running:
            try:
                # Get inventory status
                inventory = self.db_manager.get_inventory_status()
                
                # Check for low stock
                for item in inventory:
                    if item['stock_status'] == 'LOW':
                        # Log material movement for auto-restocking
                        self.db_manager.log_material_movement(
                            warehouse_id=item['warehouse_id'],
                            material_type=item['material_type'],
                            movement_type='IN',
                            quantity=30,  # Restock amount
                            moved_by='Auto_Restock_System'
                        )
                        
                        self.stats['material_movements'] += 1
                        logger.info(f"Auto-restocked {item['material_type']} in {item['warehouse_id']}")
                
                await asyncio.sleep(120)  # Check every 2 minutes
                
            except Exception as e:
                logger.error(f"Error in inventory monitor: {e}")
                await asyncio.sleep(300)
    
    def _get_uptime(self) -> str:
        """Get system uptime as formatted string"""
        if not self.start_time:
            return "00:00:00"
        
        uptime = datetime.now() - self.start_time
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        seconds = int(uptime.total_seconds() % 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _get_uptime_seconds(self) -> int:
        """Get system uptime in seconds"""
        if not self.start_time:
            return 0
        return int((datetime.now() - self.start_time).total_seconds())
    
    def _get_status_summary(self) -> str:
        """Get system status summary"""
        return (f"Uptime: {self._get_uptime()}, "
               f"OPC UA: {'✅' if self.system_status.opcua_connected else '❌'}, "
               f"MES: {'✅' if self.system_status.mes_running else '❌'}, "
               f"DB: {'✅' if self.system_status.database_connected else '❌'}, "
               f"Messages: {self.stats['messages_processed']}, "
               f"Errors: {self.system_status.error_count}")
    
    def get_system_info(self) -> Dict:
        """Get comprehensive system information"""
        return {
            'status': {
                'plc_connected': self.system_status.plc_connected,
                'opcua_connected': self.system_status.opcua_connected,
                'mes_running': self.system_status.mes_running,
                'database_connected': self.system_status.database_connected,
                'uptime': self._get_uptime(),
                'last_update': self.system_status.last_update,
                'error_count': self.system_status.error_count
            },
            'statistics': self.stats,
            'configuration': {
                'opcua_endpoint': self.settings.OPCUA_ENDPOINT,
                'database_path': self.settings.DATABASE_URL,
                'mqtt_broker': self.settings.MQTT_BROKER
            }
        }

# Main execution
async def main():
    """Main execution function"""
    logger.info("🏭 EV Manufacturing Integration System Starting...")
    
    # Create and start orchestrator
    orchestrator = IntegrationOrchestrator()
    
    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await orchestrator.stop()

if __name__ == "__main__":
    # Run the integration system
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 System interrupted by user")
    except Exception as e:
        print(f"❌ System error: {e}")
        logger.error(f"System error: {e}")
    finally:
        print("👋 EV Manufacturing Integration System terminated")
