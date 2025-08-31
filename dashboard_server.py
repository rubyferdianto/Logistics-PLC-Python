#!/usr/bin/env python3
"""
Web Dashboard Server for PLC -> OPC UA -> SCADA -> MES -> DATABASE Integration
Provides real-time data visualization and monitoring
"""
import asyncio
import json
import logging
import random
import time
from datetime import datetime
from typing import Dict, Any, List
import threading
from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DashboardDataProvider:
    """Provides real-time data for the integration dashboard"""
    
    def __init__(self):
        self.production_data = {
            'total_units': 1247,
            'production_rate': 185,
            'efficiency': 94.5,
            'quality_rate': 98.2,
            'target_units': 1670
        }
        
        self.conveyor_data = {
            'C1': {'speed': 78, 'load': 85, 'running': True, 'units_produced': 456},
            'C2': {'speed': 82, 'load': 78, 'running': True, 'units_produced': 523},
            'C3': {'speed': 0, 'load': 0, 'running': False, 'units_produced': 268}
        }
        
        self.inventory_data = {
            'WH_A': {'anodes': 25, 'cathodes': 20, 'electrolyte': 30},
            'WH_B': {'anodes': 15, 'cathodes': 25, 'electrolyte': 10},
            'WH_C': {'anodes': 5, 'cathodes': 10, 'electrolyte': 15}
        }
        
        self.system_health = {
            'plc': {'status': 'ONLINE', 'sensors': 12, 'update_rate': '100ms'},
            'opcua': {'status': 'CONNECTED', 'nodes': 24, 'quality': 'Good', 'latency': '15ms'},
            'scada': {'status': 'MONITORING', 'alarms': 0, 'trends': 'Active', 'hmi': 'Online'},
            'mes': {'status': 'PROCESSING', 'orders': 3, 'efficiency': 94.5, 'quality': 98.2},
            'database': {'status': 'STORING', 'records': '145K', 'storage': '2.3GB', 'speed': '12ms'}
        }
        
        self.alerts = [
            {'level': 'info', 'message': 'Production order PO_20250831_143521 started on Conveyor C1', 'timestamp': datetime.now()},
            {'level': 'warning', 'message': 'Warehouse B electrolyte level below threshold (10 units)', 'timestamp': datetime.now()},
            {'level': 'critical', 'message': 'Conveyor C3 scheduled maintenance in progress', 'timestamp': datetime.now()},
            {'level': 'success', 'message': 'Quality check passed - Batch #1247 approved', 'timestamp': datetime.now()}
        ]
        
        self.data_logs = []
        self.simulation_running = True
        
    def simulate_plc_data(self) -> Dict[str, Any]:
        """Simulate PLC layer data generation"""
        # Update conveyor data
        for conveyor_id, data in self.conveyor_data.items():
            if data['running']:
                # Simulate production
                data['units_produced'] += random.randint(0, 2)
                
                # Small variations in speed and load
                data['speed'] += random.randint(-2, 2)
                data['load'] += random.randint(-3, 3)
                
                # Keep within bounds
                data['speed'] = max(70, min(100, data['speed']))
                data['load'] = max(60, min(95, data['load']))
        
        # Update total production
        total_units = sum(conv['units_produced'] for conv in self.conveyor_data.values())
        self.production_data['total_units'] = total_units
        
        # Update production rate
        self.production_data['production_rate'] = 180 + random.randint(-10, 15)
        
        # Update efficiency and quality
        self.production_data['efficiency'] = 92 + random.uniform(0, 6)
        self.production_data['quality_rate'] = 96 + random.uniform(0, 3)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'conveyors': self.conveyor_data.copy(),
            'production': self.production_data.copy()
        }
    
    def simulate_opcua_transmission(self, plc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate OPC UA data transmission"""
        node_count = 22 + random.randint(0, 5)
        latency = 12 + random.randint(0, 8)
        
        self.system_health['opcua']['nodes'] = node_count
        self.system_health['opcua']['latency'] = f'{latency}ms'
        
        return {
            'timestamp': plc_data['timestamp'],
            'nodes_transmitted': node_count,
            'latency_ms': latency,
            'connection_quality': 'Good'
        }
    
    def simulate_scada_monitoring(self, opcua_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate SCADA system monitoring"""
        # Check for alarms
        alarm_count = 0
        
        # Check conveyor thresholds
        for conveyor_id, data in self.conveyor_data.items():
            if data['running'] and data['load'] > 90:
                alarm_count += 1
        
        # Check inventory levels
        for warehouse, materials in self.inventory_data.items():
            for material, quantity in materials.items():
                if quantity < 10:
                    alarm_count += 1
        
        self.system_health['scada']['alarms'] = alarm_count
        
        return {
            'timestamp': opcua_data['timestamp'],
            'alarms_active': alarm_count,
            'trends_updated': True,
            'hmi_status': 'Online'
        }
    
    def simulate_mes_processing(self, scada_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate MES system processing"""
        # Update system health
        self.system_health['mes']['efficiency'] = self.production_data['efficiency']
        self.system_health['mes']['quality'] = self.production_data['quality_rate']
        
        # Calculate OEE (Overall Equipment Effectiveness)
        availability = 0.98  # 98% uptime
        performance = self.production_data['efficiency'] / 100
        quality = self.production_data['quality_rate'] / 100
        oee = availability * performance * quality * 100
        
        return {
            'timestamp': scada_data['timestamp'],
            'oee': oee,
            'orders_processed': 3,
            'quality_checks': random.randint(15, 25)
        }
    
    def simulate_database_storage(self, mes_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate database storage operations"""
        # Update record count
        current_records = int(self.system_health['database']['records'].replace('K', '')) * 1000
        new_records = current_records + random.randint(10, 50)
        self.system_health['database']['records'] = f'{new_records // 1000}K'
        
        # Update response time
        response_time = 10 + random.randint(0, 8)
        self.system_health['database']['speed'] = f'{response_time}ms'
        
        return {
            'timestamp': mes_data['timestamp'],
            'records_stored': random.randint(4, 8),
            'response_time_ms': response_time,
            'storage_health': 'HEALTHY'
        }
    
    def add_data_log(self, layer: str, message: str, level: str = 'info'):
        """Add a data flow log entry"""
        log_entry = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'layer': layer,
            'message': message,
            'level': level
        }
        
        self.data_logs.insert(0, log_entry)
        
        # Keep only last 50 entries
        if len(self.data_logs) > 50:
            self.data_logs = self.data_logs[:50]
    
    def process_integration_cycle(self) -> Dict[str, Any]:
        """Process one complete integration cycle"""
        if not self.simulation_running:
            return {'status': 'paused'}
        
        try:
            # Step 1: PLC Data Generation
            plc_data = self.simulate_plc_data()
            self.add_data_log('PLC', f"Sensor data updated: {len(self.conveyor_data)} conveyors")
            
            # Step 2: OPC UA Transmission
            opcua_data = self.simulate_opcua_transmission(plc_data)
            self.add_data_log('OPC UA', f"Transmitted {opcua_data['nodes_transmitted']} nodes")
            
            # Step 3: SCADA Monitoring
            scada_data = self.simulate_scada_monitoring(opcua_data)
            self.add_data_log('SCADA', f"Monitoring active, {scada_data['alarms_active']} alarms")
            
            # Step 4: MES Processing
            mes_data = self.simulate_mes_processing(scada_data)
            self.add_data_log('MES', f"OEE calculated: {mes_data['oee']:.1f}%")
            
            # Step 5: Database Storage
            db_data = self.simulate_database_storage(mes_data)
            self.add_data_log('DATABASE', f"Stored {db_data['records_stored']} records")
            
            # Consume inventory randomly
            if random.random() < 0.3:  # 30% chance
                warehouse = random.choice(list(self.inventory_data.keys()))
                material = random.choice(list(self.inventory_data[warehouse].keys()))
                if self.inventory_data[warehouse][material] > 0:
                    self.inventory_data[warehouse][material] -= 1
                    self.add_data_log('INVENTORY', f"Consumed 1 {material} from {warehouse}", 'warning')
            
            return {
                'status': 'running',
                'production': self.production_data,
                'conveyors': self.conveyor_data,
                'inventory': self.inventory_data,
                'system_health': self.system_health,
                'alerts': self.alerts[-10:],  # Last 10 alerts
                'data_logs': self.data_logs[:20],  # Last 20 log entries
                'integration_data': {
                    'plc': plc_data,
                    'opcua': opcua_data,
                    'scada': scada_data,
                    'mes': mes_data,
                    'database': db_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error in integration cycle: {e}")
            self.add_data_log('SYSTEM', f"Error: {str(e)}", 'error')
            return {'status': 'error', 'message': str(e)}
    
    def start_production(self):
        """Start production simulation"""
        self.simulation_running = True
        self.add_data_log('SYSTEM', 'Production started by operator', 'info')
        
        # Reset conveyor statuses (except C3 which is in maintenance)
        for conveyor_id in ['C1', 'C2']:
            self.conveyor_data[conveyor_id]['running'] = True
            self.conveyor_data[conveyor_id]['speed'] = 75 + random.randint(0, 10)
    
    def pause_production(self):
        """Pause production simulation"""
        self.simulation_running = False
        self.add_data_log('SYSTEM', 'Production paused by operator', 'warning')
    
    def emergency_stop(self):
        """Emergency stop all systems"""
        self.simulation_running = False
        self.add_data_log('SYSTEM', 'EMERGENCY STOP activated!', 'error')
        
        # Stop all conveyors
        for conveyor_id in self.conveyor_data:
            self.conveyor_data[conveyor_id]['running'] = False
            self.conveyor_data[conveyor_id]['speed'] = 0
            self.conveyor_data[conveyor_id]['load'] = 0

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ev_manufacturing_integration_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize data provider
data_provider = DashboardDataProvider()

@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    return send_from_directory('.', 'integration_dashboard.html')

@app.route('/api/data')
def get_dashboard_data():
    """Get current dashboard data"""
    return jsonify(data_provider.process_integration_cycle())

@app.route('/api/production/start', methods=['POST'])
def start_production():
    """Start production"""
    data_provider.start_production()
    return jsonify({'status': 'started'})

@app.route('/api/production/pause', methods=['POST'])
def pause_production():
    """Pause production"""
    data_provider.pause_production()
    return jsonify({'status': 'paused'})

@app.route('/api/production/emergency_stop', methods=['POST'])
def emergency_stop():
    """Emergency stop"""
    data_provider.emergency_stop()
    return jsonify({'status': 'emergency_stopped'})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected to dashboard')
    emit('status', {'message': 'Connected to integration dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected from dashboard')

def background_data_stream():
    """Background task to stream real-time data"""
    while True:
        if data_provider.simulation_running:
            try:
                # Process integration cycle
                cycle_data = data_provider.process_integration_cycle()
                
                # Emit real-time data to connected clients
                socketio.emit('data_update', cycle_data)
                
                # Wait before next cycle
                time.sleep(3)  # Update every 3 seconds
                
            except Exception as e:
                logger.error(f"Error in background data stream: {e}")
                time.sleep(5)
        else:
            time.sleep(1)

def main():
    """Main function to start the dashboard server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EV Manufacturing Integration Dashboard Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    print("🏭 EV Manufacturing Integration Dashboard")
    print("=" * 50)
    print(f"🌐 Server starting on http://{args.host}:{args.port}")
    print("📊 Real-time data visualization for:")
    print("   • PLC → OPC UA → SCADA → MES → DATABASE")
    print("📱 Features:")
    print("   • Live production monitoring")
    print("   • System health dashboard")
    print("   • Real-time alerts and logs")
    print("   • Interactive controls")
    print("=" * 50)
    
    # Start background data streaming in a separate thread
    background_thread = threading.Thread(target=background_data_stream, daemon=True)
    background_thread.start()
    
    try:
        # Start the web server
        socketio.run(app, host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n👋 Dashboard server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()
