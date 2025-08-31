"""
Enhanced Database Manager for PLC -> OPC UA -> MES -> DATABASE integration
Provides comprehensive data storage and retrieval for EV manufacturing system
"""
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import pandas as pd
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    db_path: str = "ev_manufacturing.db"
    pool_size: int = 10
    timeout: int = 30
    check_same_thread: bool = False
    enable_wal: bool = True  # Write-Ahead Logging for better concurrency

class EnhancedDatabaseManager:
    """Enhanced database manager for EV manufacturing system"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.db_path = self.config.db_path
        self._lock = threading.RLock()
        
        # Initialize database
        self._initialize_database()
        self._enable_optimizations()
    
    def _initialize_database(self):
        """Initialize all database tables with proper schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # PLC Real-time Data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plc_realtime_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    node_name TEXT,
                    value TEXT NOT NULL,
                    data_type TEXT,
                    quality TEXT DEFAULT 'Good',
                    timestamp TEXT NOT NULL,
                    source_system TEXT DEFAULT 'OPC_UA',
                    conveyor_id TEXT,
                    INDEX(node_id, timestamp),
                    INDEX(conveyor_id, timestamp)
                )
            ''')
            
            # Production Orders table (Enhanced)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS production_orders (
                    order_id TEXT PRIMARY KEY,
                    product_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    produced_quantity INTEGER DEFAULT 0,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    assigned_conveyor TEXT,
                    progress REAL DEFAULT 0.0,
                    estimated_completion TEXT,
                    quality_checks TEXT,
                    notes TEXT,
                    created_by TEXT DEFAULT 'System',
                    FOREIGN KEY (assigned_conveyor) REFERENCES conveyors(conveyor_id)
                )
            ''')
            
            # Conveyors table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conveyors (
                    conveyor_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    location TEXT,
                    max_speed REAL,
                    current_speed REAL DEFAULT 0,
                    status TEXT DEFAULT 'idle',
                    last_maintenance TEXT,
                    next_maintenance TEXT,
                    total_runtime_hours REAL DEFAULT 0,
                    total_units_produced INTEGER DEFAULT 0
                )
            ''')
            
            # Production Metrics table (Time-series data)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS production_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conveyor_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    units_produced INTEGER NOT NULL,
                    production_rate REAL NOT NULL,
                    efficiency REAL NOT NULL,
                    oee REAL,  -- Overall Equipment Effectiveness
                    downtime_minutes REAL NOT NULL,
                    quality_pass_rate REAL NOT NULL,
                    energy_consumption REAL,
                    cycle_time REAL,
                    INDEX(conveyor_id, timestamp),
                    FOREIGN KEY (conveyor_id) REFERENCES conveyors(conveyor_id)
                )
            ''')
            
            # Quality Control Records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quality_records (
                    record_id TEXT PRIMARY KEY,
                    product_id TEXT NOT NULL,
                    order_id TEXT,
                    conveyor_id TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    result TEXT NOT NULL,
                    pass_fail TEXT NOT NULL,
                    measurements TEXT NOT NULL,
                    tested_at TEXT NOT NULL,
                    operator TEXT NOT NULL,
                    inspector TEXT,
                    retest_count INTEGER DEFAULT 0,
                    notes TEXT,
                    corrective_action TEXT,
                    INDEX(conveyor_id, tested_at),
                    INDEX(result, tested_at),
                    FOREIGN KEY (order_id) REFERENCES production_orders(order_id),
                    FOREIGN KEY (conveyor_id) REFERENCES conveyors(conveyor_id)
                )
            ''')
            
            # Material Inventory table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS material_inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    warehouse_id TEXT NOT NULL,
                    material_type TEXT NOT NULL,
                    current_stock INTEGER NOT NULL,
                    min_stock_level INTEGER NOT NULL,
                    max_stock_level INTEGER NOT NULL,
                    unit_cost REAL,
                    supplier TEXT,
                    last_restocked TEXT,
                    expiry_date TEXT,
                    lot_number TEXT,
                    INDEX(warehouse_id, material_type)
                )
            ''')
            
            # Material Movements table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS material_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    warehouse_id TEXT NOT NULL,
                    material_type TEXT NOT NULL,
                    movement_type TEXT NOT NULL, -- 'IN', 'OUT', 'TRANSFER'
                    quantity INTEGER NOT NULL,
                    previous_stock INTEGER NOT NULL,
                    new_stock INTEGER NOT NULL,
                    moved_by TEXT, -- Robot ID or operator
                    moved_to TEXT, -- Destination (conveyor, warehouse)
                    timestamp TEXT NOT NULL,
                    order_id TEXT,
                    INDEX(warehouse_id, timestamp),
                    INDEX(movement_type, timestamp)
                )
            ''')
            
            # Alarms and Events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL, -- 'ALARM', 'WARNING', 'INFO', 'ERROR'
                    severity INTEGER NOT NULL, -- 1-5 scale
                    source_system TEXT NOT NULL,
                    source_component TEXT,
                    message TEXT NOT NULL,
                    details TEXT,
                    timestamp TEXT NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_by TEXT,
                    acknowledged_at TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_by TEXT,
                    resolved_at TEXT,
                    INDEX(event_type, timestamp),
                    INDEX(severity, timestamp)
                )
            ''')
            
            # Equipment Maintenance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maintenance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id TEXT NOT NULL,
                    equipment_type TEXT NOT NULL,
                    maintenance_type TEXT NOT NULL, -- 'PREVENTIVE', 'CORRECTIVE', 'EMERGENCY'
                    description TEXT NOT NULL,
                    performed_by TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    duration_hours REAL,
                    cost REAL,
                    parts_replaced TEXT,
                    next_maintenance TEXT,
                    status TEXT DEFAULT 'PENDING',
                    INDEX(equipment_id, started_at)
                )
            ''')
            
            # Energy Consumption table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS energy_consumption (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conveyor_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    power_consumption REAL NOT NULL, -- kW
                    energy_consumed REAL NOT NULL, -- kWh
                    efficiency_rating REAL,
                    INDEX(conveyor_id, timestamp),
                    FOREIGN KEY (conveyor_id) REFERENCES conveyors(conveyor_id)
                )
            ''')
            
            # Initialize conveyors data
            conveyors_data = [
                ('C1', 'Conveyor Line 1', 'Production Floor A', 100.0),
                ('C2', 'Conveyor Line 2', 'Production Floor A', 100.0),
                ('C3', 'Conveyor Line 3', 'Production Floor B', 100.0)
            ]
            
            cursor.executemany('''
                INSERT OR IGNORE INTO conveyors (conveyor_id, name, location, max_speed)
                VALUES (?, ?, ?, ?)
            ''', conveyors_data)
            
            # Initialize material inventory
            materials_data = [
                ('WH_A', 'anode', 30, 10, 50, 12.50, 'Supplier_A'),
                ('WH_A', 'cathode', 25, 10, 50, 15.00, 'Supplier_B'),
                ('WH_A', 'electrolyte', 35, 10, 50, 8.75, 'Supplier_C'),
                ('WH_B', 'anode', 20, 10, 50, 12.50, 'Supplier_A'),
                ('WH_B', 'cathode', 25, 10, 50, 15.00, 'Supplier_B'),
                ('WH_B', 'electrolyte', 15, 10, 50, 8.75, 'Supplier_C'),
                ('WH_C', 'anode', 10, 10, 50, 12.50, 'Supplier_A'),
                ('WH_C', 'cathode', 15, 10, 50, 15.00, 'Supplier_B'),
                ('WH_C', 'electrolyte', 20, 10, 50, 8.75, 'Supplier_C')
            ]
            
            cursor.executemany('''
                INSERT OR IGNORE INTO material_inventory 
                (warehouse_id, material_type, current_stock, min_stock_level, max_stock_level, unit_cost, supplier)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', materials_data)
            
            conn.commit()
            logger.info("Database initialized successfully with enhanced schema")
    
    def _enable_optimizations(self):
        """Enable database optimizations for better performance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.config.enable_wal:
                cursor.execute("PRAGMA journal_mode = WAL")
            
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA cache_size = 10000")
            cursor.execute("PRAGMA temp_store = memory")
            cursor.execute("PRAGMA mmap_size = 268435456")  # 256MB
            
            conn.commit()
            logger.info("Database optimizations enabled")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper context management"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.config.timeout,
                check_same_thread=self.config.check_same_thread
            )
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def store_plc_data(self, node_id: str, value: Any, node_name: str = None, 
                      data_type: str = None, quality: str = 'Good', 
                      conveyor_id: str = None) -> bool:
        """Store PLC real-time data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO plc_realtime_data 
                    (node_id, node_name, value, data_type, quality, timestamp, conveyor_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    node_id,
                    node_name,
                    str(value),
                    data_type or type(value).__name__,
                    quality,
                    datetime.now().isoformat(),
                    conveyor_id
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error storing PLC data: {e}")
            return False
    
    def store_production_metrics(self, conveyor_id: str, metrics: Dict) -> bool:
        """Store production metrics data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO production_metrics 
                    (conveyor_id, timestamp, units_produced, production_rate, efficiency, 
                     oee, downtime_minutes, quality_pass_rate, energy_consumption, cycle_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    conveyor_id,
                    datetime.now().isoformat(),
                    metrics.get('units_produced', 0),
                    metrics.get('production_rate', 0.0),
                    metrics.get('efficiency', 0.0),
                    metrics.get('oee', 0.0),
                    metrics.get('downtime_minutes', 0.0),
                    metrics.get('quality_pass_rate', 0.0),
                    metrics.get('energy_consumption', 0.0),
                    metrics.get('cycle_time', 0.0)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error storing production metrics: {e}")
            return False
    
    def store_quality_record(self, record: Dict) -> bool:
        """Store quality control record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO quality_records 
                    (record_id, product_id, order_id, conveyor_id, test_type, result, 
                     pass_fail, measurements, tested_at, operator, inspector, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.get('record_id'),
                    record.get('product_id'),
                    record.get('order_id'),
                    record.get('conveyor_id'),
                    record.get('test_type'),
                    record.get('result'),
                    record.get('pass_fail'),
                    json.dumps(record.get('measurements', {})),
                    record.get('tested_at', datetime.now().isoformat()),
                    record.get('operator', 'System'),
                    record.get('inspector'),
                    record.get('notes')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error storing quality record: {e}")
            return False
    
    def log_material_movement(self, warehouse_id: str, material_type: str, 
                            movement_type: str, quantity: int, moved_by: str = None,
                            moved_to: str = None, order_id: str = None) -> bool:
        """Log material inventory movement"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current stock
                cursor.execute('''
                    SELECT current_stock FROM material_inventory 
                    WHERE warehouse_id = ? AND material_type = ?
                ''', (warehouse_id, material_type))
                
                result = cursor.fetchone()
                if not result:
                    logger.error(f"Material not found: {warehouse_id}/{material_type}")
                    return False
                
                previous_stock = result[0]
                
                # Calculate new stock based on movement type
                if movement_type == 'OUT':
                    new_stock = previous_stock - quantity
                elif movement_type == 'IN':
                    new_stock = previous_stock + quantity
                else:
                    new_stock = previous_stock
                
                # Log the movement
                cursor.execute('''
                    INSERT INTO material_movements 
                    (warehouse_id, material_type, movement_type, quantity, 
                     previous_stock, new_stock, moved_by, moved_to, timestamp, order_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    warehouse_id,
                    material_type,
                    movement_type,
                    quantity,
                    previous_stock,
                    new_stock,
                    moved_by,
                    moved_to,
                    datetime.now().isoformat(),
                    order_id
                ))
                
                # Update inventory
                cursor.execute('''
                    UPDATE material_inventory 
                    SET current_stock = ? 
                    WHERE warehouse_id = ? AND material_type = ?
                ''', (new_stock, warehouse_id, material_type))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error logging material movement: {e}")
            return False
    
    def log_system_event(self, event_type: str, severity: int, source_system: str,
                        message: str, source_component: str = None, details: str = None) -> bool:
        """Log system event/alarm"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO system_events 
                    (event_type, severity, source_system, source_component, message, details, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_type,
                    severity,
                    source_system,
                    source_component,
                    message,
                    details,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error logging system event: {e}")
            return False
    
    def get_real_time_data(self, conveyor_id: str = None, hours: int = 1) -> List[Dict]:
        """Get real-time PLC data for analysis"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                since_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                if conveyor_id:
                    cursor.execute('''
                        SELECT * FROM plc_realtime_data 
                        WHERE conveyor_id = ? AND timestamp >= ?
                        ORDER BY timestamp DESC
                        LIMIT 1000
                    ''', (conveyor_id, since_time))
                else:
                    cursor.execute('''
                        SELECT * FROM plc_realtime_data 
                        WHERE timestamp >= ?
                        ORDER BY timestamp DESC
                        LIMIT 1000
                    ''', (since_time,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting real-time data: {e}")
            return []
    
    def get_production_analytics(self, conveyor_id: str = None, days: int = 7) -> Dict:
        """Get production analytics and KPIs"""
        try:
            with self.get_connection() as conn:
                since_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                analytics = {}
                
                # Production metrics query
                if conveyor_id:
                    query = '''
                        SELECT 
                            AVG(production_rate) as avg_production_rate,
                            AVG(efficiency) as avg_efficiency,
                            AVG(oee) as avg_oee,
                            SUM(units_produced) as total_units,
                            AVG(quality_pass_rate) as avg_quality_rate,
                            SUM(downtime_minutes) as total_downtime
                        FROM production_metrics 
                        WHERE conveyor_id = ? AND timestamp >= ?
                    '''
                    params = (conveyor_id, since_date)
                else:
                    query = '''
                        SELECT 
                            conveyor_id,
                            AVG(production_rate) as avg_production_rate,
                            AVG(efficiency) as avg_efficiency,
                            AVG(oee) as avg_oee,
                            SUM(units_produced) as total_units,
                            AVG(quality_pass_rate) as avg_quality_rate,
                            SUM(downtime_minutes) as total_downtime
                        FROM production_metrics 
                        WHERE timestamp >= ?
                        GROUP BY conveyor_id
                    '''
                    params = (since_date,)
                
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if conveyor_id:
                    row = cursor.fetchone()
                    if row:
                        analytics[conveyor_id] = dict(row)
                else:
                    rows = cursor.fetchall()
                    for row in rows:
                        analytics[row['conveyor_id']] = dict(row)
                
                return analytics
                
        except Exception as e:
            logger.error(f"Error getting production analytics: {e}")
            return {}
    
    def get_quality_trends(self, days: int = 30) -> Dict:
        """Get quality trends and analysis"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                since_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Quality trends by conveyor
                cursor.execute('''
                    SELECT 
                        conveyor_id,
                        COUNT(*) as total_tests,
                        SUM(CASE WHEN pass_fail = 'PASS' THEN 1 ELSE 0 END) as passed_tests,
                        AVG(CASE WHEN pass_fail = 'PASS' THEN 1.0 ELSE 0.0 END) * 100 as pass_rate,
                        COUNT(DISTINCT test_type) as test_types
                    FROM quality_records 
                    WHERE tested_at >= ?
                    GROUP BY conveyor_id
                ''', (since_date,))
                
                quality_data = {}
                for row in cursor.fetchall():
                    quality_data[row['conveyor_id']] = dict(row)
                
                # Recent quality issues
                cursor.execute('''
                    SELECT * FROM quality_records 
                    WHERE pass_fail = 'FAIL' AND tested_at >= ?
                    ORDER BY tested_at DESC
                    LIMIT 10
                ''', (since_date,))
                
                recent_failures = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'trends': quality_data,
                    'recent_failures': recent_failures
                }
                
        except Exception as e:
            logger.error(f"Error getting quality trends: {e}")
            return {}
    
    def get_inventory_status(self) -> List[Dict]:
        """Get current inventory status with alerts"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        warehouse_id,
                        material_type,
                        current_stock,
                        min_stock_level,
                        max_stock_level,
                        unit_cost,
                        supplier,
                        CASE 
                            WHEN current_stock <= min_stock_level THEN 'LOW'
                            WHEN current_stock >= max_stock_level THEN 'HIGH'
                            ELSE 'NORMAL'
                        END as stock_status
                    FROM material_inventory
                    ORDER BY warehouse_id, material_type
                ''')
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting inventory status: {e}")
            return []
    
    def get_system_health(self) -> Dict:
        """Get overall system health status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get recent alarms
                cursor.execute('''
                    SELECT event_type, COUNT(*) as count
                    FROM system_events 
                    WHERE timestamp >= datetime('now', '-1 hour')
                    GROUP BY event_type
                ''')
                recent_events = dict(cursor.fetchall())
                
                # Get conveyor status
                cursor.execute('''
                    SELECT conveyor_id, status
                    FROM conveyors
                ''')
                conveyor_status = dict(cursor.fetchall())
                
                # Get low inventory alerts
                cursor.execute('''
                    SELECT COUNT(*) as low_stock_count
                    FROM material_inventory
                    WHERE current_stock <= min_stock_level
                ''')
                low_stock_count = cursor.fetchone()[0]
                
                return {
                    'system_status': 'HEALTHY' if not recent_events.get('ERROR', 0) else 'WARNING',
                    'recent_events': recent_events,
                    'conveyor_status': conveyor_status,
                    'low_stock_alerts': low_stock_count,
                    'last_check': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {'system_status': 'ERROR', 'error': str(e)}
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """Clean up old data to maintain database performance"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
                
                # Clean old PLC data
                cursor.execute('''
                    DELETE FROM plc_realtime_data 
                    WHERE timestamp < ?
                ''', (cutoff_date,))
                
                # Clean old system events (keep only critical ones)
                cursor.execute('''
                    DELETE FROM system_events 
                    WHERE timestamp < ? AND severity < 4
                ''', (cutoff_date,))
                
                conn.commit()
                logger.info(f"Cleaned up data older than {days_to_keep} days")
                return True
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return False
    
    def export_data_to_csv(self, table_name: str, output_file: str, 
                          where_clause: str = None) -> bool:
        """Export data to CSV for external analysis"""
        try:
            with self.get_connection() as conn:
                query = f"SELECT * FROM {table_name}"
                if where_clause:
                    query += f" WHERE {where_clause}"
                
                df = pd.read_sql_query(query, conn)
                df.to_csv(output_file, index=False)
                
                logger.info(f"Exported {len(df)} rows to {output_file}")
                return True
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False

# Example usage and testing
def main():
    """Test the enhanced database manager"""
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    db_manager = EnhancedDatabaseManager()
    
    # Test storing PLC data
    print("Testing PLC data storage...")
    db_manager.store_plc_data(
        node_id="ns=2;s=Conveyor.C1.Running",
        value=True,
        node_name="Conveyor C1 Running Status",
        conveyor_id="C1"
    )
    
    # Test storing production metrics
    print("Testing production metrics storage...")
    metrics = {
        'units_produced': 25,
        'production_rate': 15.5,
        'efficiency': 87.2,
        'oee': 82.1,
        'downtime_minutes': 5.0,
        'quality_pass_rate': 98.5,
        'energy_consumption': 12.3,
        'cycle_time': 2.5
    }
    db_manager.store_production_metrics("C1", metrics)
    
    # Test material movement
    print("Testing material movement...")
    db_manager.log_material_movement(
        warehouse_id="WH_A",
        material_type="anode",
        movement_type="OUT",
        quantity=5,
        moved_by="Robot_01",
        moved_to="C1"
    )
    
    # Test system event logging
    print("Testing system event logging...")
    db_manager.log_system_event(
        event_type="INFO",
        severity=2,
        source_system="MES",
        source_component="C1",
        message="Production order started",
        details="Order PO_20250831_001 assigned to Conveyor C1"
    )
    
    # Get analytics
    print("Getting production analytics...")
    analytics = db_manager.get_production_analytics()
    print(f"Analytics: {analytics}")
    
    # Get inventory status
    print("Getting inventory status...")
    inventory = db_manager.get_inventory_status()
    print(f"Inventory: {inventory}")
    
    # Get system health
    print("Getting system health...")
    health = db_manager.get_system_health()
    print(f"System Health: {health}")

if __name__ == "__main__":
    main()
