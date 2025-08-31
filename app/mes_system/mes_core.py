"""
Manufacturing Execution System (MES) for EV Manufacturing
Processes data from OPC UA and coordinates with database operations
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import threading
from queue import Queue, Empty
import sqlite3

logger = logging.getLogger(__name__)

class ProductionStatus(Enum):
    """Production order status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"

class QualityStatus(Enum):
    """Quality control status enumeration"""
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"
    RETEST = "retest"

@dataclass
class ProductionOrder:
    """Production order data structure"""
    order_id: str
    product_type: str  # Li-Ion_18650, Li-Ion_21700, LiFePO4_26650
    quantity: int
    priority: int
    status: ProductionStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_conveyor: Optional[str] = None
    progress: float = 0.0
    quality_checks: List[Dict] = None

    def __post_init__(self):
        if self.quality_checks is None:
            self.quality_checks = []

@dataclass
class ProductionMetrics:
    """Real-time production metrics"""
    conveyor_id: str
    units_produced: int
    production_rate: float  # units per hour
    efficiency: float  # percentage
    downtime: float  # minutes
    quality_pass_rate: float  # percentage
    last_update: datetime

@dataclass
class QualityRecord:
    """Quality control record"""
    record_id: str
    product_id: str
    conveyor_id: str
    test_type: str
    result: QualityStatus
    measurements: Dict[str, float]
    tested_at: datetime
    operator: str
    notes: Optional[str] = None

class MESSystem:
    """Manufacturing Execution System"""
    
    def __init__(self, db_connection_string: str = "manufacturing.db"):
        self.db_connection = db_connection_string
        self.production_orders = {}
        self.active_orders = {}
        self.production_metrics = {}
        self.quality_records = []
        self.data_queue = Queue()
        self.running = False
        self.processor_thread = None
        
        # Initialize database
        self._init_database()
        
        # Load existing orders
        self._load_production_orders()
    
    def _init_database(self):
        """Initialize MES database tables"""
        try:
            conn = sqlite3.connect(self.db_connection)
            cursor = conn.cursor()
            
            # Production Orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS production_orders (
                    order_id TEXT PRIMARY KEY,
                    product_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    assigned_conveyor TEXT,
                    progress REAL DEFAULT 0.0,
                    quality_checks TEXT
                )
            ''')
            
            # Production Metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS production_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conveyor_id TEXT NOT NULL,
                    units_produced INTEGER NOT NULL,
                    production_rate REAL NOT NULL,
                    efficiency REAL NOT NULL,
                    downtime REAL NOT NULL,
                    quality_pass_rate REAL NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            # Quality Records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quality_records (
                    record_id TEXT PRIMARY KEY,
                    product_id TEXT NOT NULL,
                    conveyor_id TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    result TEXT NOT NULL,
                    measurements TEXT NOT NULL,
                    tested_at TEXT NOT NULL,
                    operator TEXT NOT NULL,
                    notes TEXT
                )
            ''')
            
            # Real-time Data Log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS realtime_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    value TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    quality TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("MES database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing MES database: {e}")
    
    def _load_production_orders(self):
        """Load existing production orders from database"""
        try:
            conn = sqlite3.connect(self.db_connection)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM production_orders WHERE status != ?', 
                         (ProductionStatus.COMPLETED.value,))
            rows = cursor.fetchall()
            
            for row in rows:
                order = ProductionOrder(
                    order_id=row[0],
                    product_type=row[1],
                    quantity=row[2],
                    priority=row[3],
                    status=ProductionStatus(row[4]),
                    created_at=datetime.fromisoformat(row[5]),
                    started_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    assigned_conveyor=row[8],
                    progress=row[9],
                    quality_checks=json.loads(row[10]) if row[10] else []
                )
                self.production_orders[order.order_id] = order
                
                if order.status == ProductionStatus.IN_PROGRESS:
                    self.active_orders[order.assigned_conveyor] = order
            
            conn.close()
            logger.info(f"Loaded {len(self.production_orders)} production orders")
            
        except Exception as e:
            logger.error(f"Error loading production orders: {e}")
    
    def start(self):
        """Start MES system processing"""
        self.running = True
        self.processor_thread = threading.Thread(target=self._process_data)
        self.processor_thread.daemon = True
        self.processor_thread.start()
        logger.info("MES System started")
    
    def stop(self):
        """Stop MES system processing"""
        self.running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        logger.info("MES System stopped")
    
    def _process_data(self):
        """Main data processing loop"""
        while self.running:
            try:
                # Process incoming OPC UA data
                try:
                    data_point = self.data_queue.get(timeout=1)
                    self._process_plc_data(data_point)
                except Empty:
                    continue
                
                # Update production metrics
                self._update_production_metrics()
                
                # Check order completion
                self._check_order_completion()
                
                # Auto-assign orders to available conveyors
                self._auto_assign_orders()
                
            except Exception as e:
                logger.error(f"Error in MES data processing: {e}")
    
    def process_opcua_data(self, data_point: Dict):
        """Process incoming OPC UA data point"""
        self.data_queue.put(data_point)
        
        # Store in real-time data log
        self._store_realtime_data(data_point)
    
    def _process_plc_data(self, data_point: Dict):
        """Process PLC data and update system state"""
        try:
            node_id = data_point.get('node_id', '')
            value = data_point.get('value')
            timestamp = data_point.get('timestamp')
            
            # Extract conveyor information from node_id
            if 'Conveyor' in node_id:
                self._process_conveyor_data(node_id, value, timestamp)
            elif 'Production' in node_id:
                self._process_production_data(node_id, value, timestamp)
            elif 'Quality' in node_id:
                self._process_quality_data(node_id, value, timestamp)
            elif 'Warehouse' in node_id:
                self._process_warehouse_data(node_id, value, timestamp)
            
        except Exception as e:
            logger.error(f"Error processing PLC data: {e}")
    
    def _process_conveyor_data(self, node_id: str, value: Any, timestamp: str):
        """Process conveyor-related data"""
        # Extract conveyor ID (C1, C2, C3)
        if '.C1.' in node_id:
            conveyor_id = 'C1'
        elif '.C2.' in node_id:
            conveyor_id = 'C2'
        elif '.C3.' in node_id:
            conveyor_id = 'C3'
        else:
            return
        
        # Initialize metrics if not exists
        if conveyor_id not in self.production_metrics:
            self.production_metrics[conveyor_id] = ProductionMetrics(
                conveyor_id=conveyor_id,
                units_produced=0,
                production_rate=0.0,
                efficiency=0.0,
                downtime=0.0,
                quality_pass_rate=0.0,
                last_update=datetime.now()
            )
        
        # Update specific metrics based on node type
        metrics = self.production_metrics[conveyor_id]
        
        if 'Running' in node_id:
            if not value:  # Conveyor stopped
                # Calculate downtime
                pass
        elif 'Speed' in node_id:
            # Update production rate based on speed
            metrics.production_rate = value * 10  # Example calculation
        elif 'Load' in node_id:
            # Update efficiency based on load
            metrics.efficiency = min(value / 100 * 85, 100)  # Max 85% efficiency
        
        metrics.last_update = datetime.now()
    
    def _process_production_data(self, node_id: str, value: Any, timestamp: str):
        """Process production count and rate data"""
        # Extract conveyor ID
        conveyor_id = None
        if '.C1.' in node_id:
            conveyor_id = 'C1'
        elif '.C2.' in node_id:
            conveyor_id = 'C2'
        elif '.C3.' in node_id:
            conveyor_id = 'C3'
        
        if not conveyor_id:
            return
        
        # Update production counts
        if conveyor_id in self.production_metrics:
            if 'Count' in node_id:
                self.production_metrics[conveyor_id].units_produced = value
                
                # Update order progress
                if conveyor_id in self.active_orders:
                    order = self.active_orders[conveyor_id]
                    order.progress = min((value / order.quantity) * 100, 100)
                    self._save_production_order(order)
    
    def _process_quality_data(self, node_id: str, value: Any, timestamp: str):
        """Process quality control data"""
        if 'PassRate' in node_id:
            # Update quality metrics for all conveyors
            for conveyor_id in self.production_metrics:
                self.production_metrics[conveyor_id].quality_pass_rate = value
        elif 'LastTestResult' in node_id:
            # Process individual quality test results
            self._create_quality_record(value, timestamp)
    
    def _process_warehouse_data(self, node_id: str, value: Any, timestamp: str):
        """Process warehouse inventory data"""
        # This could trigger material ordering or alerts
        if value < 10:  # Low inventory threshold
            logger.warning(f"Low inventory alert: {node_id} = {value}")
    
    def _store_realtime_data(self, data_point: Dict):
        """Store real-time data in database"""
        try:
            conn = sqlite3.connect(self.db_connection)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO realtime_data (source, node_id, value, timestamp, quality)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                'OPC_UA',
                data_point.get('node_id', ''),
                str(data_point.get('value', '')),
                data_point.get('timestamp', datetime.now().isoformat()),
                data_point.get('quality', 'Good')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing real-time data: {e}")
    
    def create_production_order(self, product_type: str, quantity: int, 
                              priority: int = 1) -> str:
        """Create a new production order"""
        order_id = f"PO_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.production_orders)+1:03d}"
        
        order = ProductionOrder(
            order_id=order_id,
            product_type=product_type,
            quantity=quantity,
            priority=priority,
            status=ProductionStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.production_orders[order_id] = order
        self._save_production_order(order)
        
        logger.info(f"Created production order: {order_id}")
        return order_id
    
    def _save_production_order(self, order: ProductionOrder):
        """Save production order to database"""
        try:
            conn = sqlite3.connect(self.db_connection)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO production_orders 
                (order_id, product_type, quantity, priority, status, created_at, 
                 started_at, completed_at, assigned_conveyor, progress, quality_checks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order.order_id,
                order.product_type,
                order.quantity,
                order.priority,
                order.status.value,
                order.created_at.isoformat(),
                order.started_at.isoformat() if order.started_at else None,
                order.completed_at.isoformat() if order.completed_at else None,
                order.assigned_conveyor,
                order.progress,
                json.dumps(order.quality_checks)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving production order: {e}")
    
    def assign_order_to_conveyor(self, order_id: str, conveyor_id: str) -> bool:
        """Assign production order to specific conveyor"""
        if order_id not in self.production_orders:
            logger.error(f"Order {order_id} not found")
            return False
        
        if conveyor_id in self.active_orders:
            logger.error(f"Conveyor {conveyor_id} already has active order")
            return False
        
        order = self.production_orders[order_id]
        order.assigned_conveyor = conveyor_id
        order.status = ProductionStatus.IN_PROGRESS
        order.started_at = datetime.now()
        
        self.active_orders[conveyor_id] = order
        self._save_production_order(order)
        
        logger.info(f"Assigned order {order_id} to conveyor {conveyor_id}")
        return True
    
    def _auto_assign_orders(self):
        """Automatically assign pending orders to available conveyors"""
        # Get available conveyors
        available_conveyors = ['C1', 'C2', 'C3']
        for conveyor_id in self.active_orders:
            if conveyor_id in available_conveyors:
                available_conveyors.remove(conveyor_id)
        
        if not available_conveyors:
            return
        
        # Get pending orders sorted by priority
        pending_orders = [
            order for order in self.production_orders.values()
            if order.status == ProductionStatus.PENDING
        ]
        pending_orders.sort(key=lambda x: x.priority, reverse=True)
        
        # Assign orders to available conveyors
        for order in pending_orders[:len(available_conveyors)]:
            conveyor_id = available_conveyors.pop(0)
            self.assign_order_to_conveyor(order.order_id, conveyor_id)
    
    def _check_order_completion(self):
        """Check if any orders are completed"""
        completed_orders = []
        
        for conveyor_id, order in self.active_orders.items():
            if order.progress >= 100:
                order.status = ProductionStatus.COMPLETED
                order.completed_at = datetime.now()
                self._save_production_order(order)
                completed_orders.append(conveyor_id)
                logger.info(f"Order {order.order_id} completed on {conveyor_id}")
        
        # Remove completed orders from active list
        for conveyor_id in completed_orders:
            del self.active_orders[conveyor_id]
    
    def _create_quality_record(self, test_result: Any, timestamp: str):
        """Create quality control record"""
        record_id = f"QC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.quality_records)+1:04d}"
        
        # Parse test result (assuming it's a JSON string or dict)
        try:
            if isinstance(test_result, str):
                test_data = json.loads(test_result)
            else:
                test_data = test_result
                
            record = QualityRecord(
                record_id=record_id,
                product_id=test_data.get('product_id', 'Unknown'),
                conveyor_id=test_data.get('conveyor_id', 'Unknown'),
                test_type=test_data.get('test_type', 'General'),
                result=QualityStatus(test_data.get('result', 'pending')),
                measurements=test_data.get('measurements', {}),
                tested_at=datetime.fromisoformat(timestamp),
                operator=test_data.get('operator', 'System'),
                notes=test_data.get('notes')
            )
            
            self.quality_records.append(record)
            self._save_quality_record(record)
            
        except Exception as e:
            logger.error(f"Error creating quality record: {e}")
    
    def _save_quality_record(self, record: QualityRecord):
        """Save quality record to database"""
        try:
            conn = sqlite3.connect(self.db_connection)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO quality_records 
                (record_id, product_id, conveyor_id, test_type, result, 
                 measurements, tested_at, operator, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.record_id,
                record.product_id,
                record.conveyor_id,
                record.test_type,
                record.result.value,
                json.dumps(record.measurements),
                record.tested_at.isoformat(),
                record.operator,
                record.notes
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving quality record: {e}")
    
    def _update_production_metrics(self):
        """Update and save production metrics"""
        try:
            conn = sqlite3.connect(self.db_connection)
            cursor = conn.cursor()
            
            for conveyor_id, metrics in self.production_metrics.items():
                cursor.execute('''
                    INSERT INTO production_metrics 
                    (conveyor_id, units_produced, production_rate, efficiency, 
                     downtime, quality_pass_rate, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.conveyor_id,
                    metrics.units_produced,
                    metrics.production_rate,
                    metrics.efficiency,
                    metrics.downtime,
                    metrics.quality_pass_rate,
                    metrics.last_update.isoformat()
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating production metrics: {e}")
    
    def get_production_status(self) -> Dict:
        """Get overall production status"""
        total_orders = len(self.production_orders)
        active_orders = len(self.active_orders)
        completed_orders = len([o for o in self.production_orders.values() 
                              if o.status == ProductionStatus.COMPLETED])
        
        return {
            'total_orders': total_orders,
            'active_orders': active_orders,
            'completed_orders': completed_orders,
            'pending_orders': total_orders - active_orders - completed_orders,
            'conveyors': {
                conveyor_id: {
                    'status': 'active' if conveyor_id in self.active_orders else 'idle',
                    'current_order': self.active_orders.get(conveyor_id, {}).order_id if conveyor_id in self.active_orders else None,
                    'metrics': asdict(self.production_metrics.get(conveyor_id, {}))
                }
                for conveyor_id in ['C1', 'C2', 'C3']
            },
            'last_update': datetime.now().isoformat()
        }
    
    def get_order_details(self, order_id: str) -> Optional[Dict]:
        """Get detailed information about a specific order"""
        if order_id in self.production_orders:
            order = self.production_orders[order_id]
            return {
                'order': asdict(order),
                'metrics': asdict(self.production_metrics.get(order.assigned_conveyor, {})) if order.assigned_conveyor else None
            }
        return None

# Example usage
def main():
    """Example MES system usage"""
    logging.basicConfig(level=logging.INFO)
    
    # Initialize MES system
    mes = MESSystem()
    mes.start()
    
    # Create some sample production orders
    order1 = mes.create_production_order("Li-Ion_18650", 100, priority=2)
    order2 = mes.create_production_order("Li-Ion_21700", 50, priority=1)
    order3 = mes.create_production_order("LiFePO4_26650", 75, priority=3)
    
    print("Created production orders:")
    print(f"Order 1: {order1}")
    print(f"Order 2: {order2}")
    print(f"Order 3: {order3}")
    
    # Simulate some time passing
    import time
    time.sleep(5)
    
    # Check production status
    status = mes.get_production_status()
    print(f"\nProduction Status: {json.dumps(status, indent=2)}")
    
    # Stop MES system
    mes.stop()

if __name__ == "__main__":
    main()
