"""
Real-time data simulation engine to make the dashboard alive with dynamic data
"""
import random
import time
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class Package:
    """Package data structure"""
    id: str
    barcode: str
    destination: str
    current_location: str
    status: str
    priority: str
    received_at: str
    weight: float = 0.0
    estimated_delivery: str = ""

@dataclass
class SensorReading:
    """Sensor reading data structure"""
    id: str
    name: str
    value: float
    unit: str
    status: str
    location: str
    timestamp: str

@dataclass
class SystemAlert:
    """System alert data structure"""
    id: int
    type: str
    title: str
    description: str
    location: str
    severity: str
    created_at: str
    is_active: bool = True

class LogisticsSimulator:
    """Real-time logistics system simulator"""
    
    def __init__(self):
        self.running = False
        self.packages = {}
        self.sensors = {}
        self.alerts = []
        self.package_counter = 1
        self.alert_counter = 1
        
        # Conveyor locations in sequence
        self.conveyor_path = [
            "Intake Scanner",
            "Conveyor Belt 1", 
            "Sorting Station A",
            "Conveyor Belt 2",
            "Scanner Station B",
            "Sorting Station B",
            "Conveyor Belt 3",
            "Loading Bay A",
            "Loading Bay B",
            "Loading Bay C"
        ]
        
        # Initialize sensors
        self._initialize_sensors()
        
        # Statistics
        self.stats = {
            'total_packages_today': 0,
            'packages_processed': 0,
            'system_uptime': datetime.now(),
            'throughput_hour': 0,
            'efficiency': 85.0
        }
    
    def _initialize_sensors(self):
        """Initialize sensor readings with realistic values"""
        sensor_configs = [
            {"id": "conveyor_speed_1", "name": "Conveyor Belt 1 Speed", "unit": "rpm", "location": "Intake Section", "base": 150, "variance": 10},
            {"id": "conveyor_speed_2", "name": "Conveyor Belt 2 Speed", "unit": "rpm", "location": "Sorting Section", "base": 145, "variance": 8},
            {"id": "conveyor_speed_3", "name": "Conveyor Belt 3 Speed", "unit": "rpm", "location": "Output Section", "base": 160, "variance": 12},
            {"id": "temperature_motor_1", "name": "Motor 1 Temperature", "unit": "°C", "location": "Motor Room A", "base": 45, "variance": 15},
            {"id": "temperature_motor_2", "name": "Motor 2 Temperature", "unit": "°C", "location": "Motor Room B", "base": 48, "variance": 12},
            {"id": "vibration_1", "name": "Vibration Sensor 1", "unit": "g", "location": "Conveyor 1", "base": 2.1, "variance": 1.5},
            {"id": "vibration_2", "name": "Vibration Sensor 2", "unit": "g", "location": "Conveyor 2", "base": 1.8, "variance": 1.2},
            {"id": "power_consumption", "name": "Power Consumption", "unit": "kW", "location": "Main Panel", "base": 45, "variance": 8},
            {"id": "noise_level", "name": "Noise Level", "unit": "dB", "location": "Factory Floor", "base": 72, "variance": 5},
            {"id": "air_pressure", "name": "Air Pressure", "unit": "PSI", "location": "Pneumatic System", "base": 90, "variance": 3}
        ]
        
        for config in sensor_configs:
            self.sensors[config["id"]] = {
                **config,
                "value": config["base"] + random.uniform(-config["variance"]/2, config["variance"]/2),
                "status": "normal",
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_package(self) -> Package:
        """Generate a new package with realistic data"""
        destinations = ["Zone A", "Zone B", "Zone C", "Zone D", "Warehouse X", "Warehouse Y"]
        priorities = ["high", "normal", "low"]
        weights = [0.5, 1.2, 2.8, 0.8, 5.1, 3.2, 1.8, 4.5]
        
        package_id = f"PKG{self.package_counter:04d}"
        self.package_counter += 1
        
        return Package(
            id=package_id,
            barcode=f"{random.randint(1000000000000, 9999999999999)}",
            destination=random.choice(destinations),
            current_location=self.conveyor_path[0],
            status="in_transit",
            priority=random.choice(priorities),
            weight=random.choice(weights),
            received_at=datetime.now().isoformat(),
            estimated_delivery=(datetime.now() + timedelta(minutes=random.randint(15, 45))).isoformat()
        )
    
    def _update_sensors(self):
        """Update sensor readings with realistic variations"""
        for sensor_id, sensor in self.sensors.items():
            # Simulate realistic sensor behavior
            base_value = sensor["value"]
            
            # Add some trending behavior
            if "temperature" in sensor_id:
                # Temperature tends to rise slowly over time
                trend = random.uniform(-0.5, 1.0)
                sensor["value"] = max(25, min(85, base_value + trend + random.uniform(-2, 2)))
                
                # Generate alerts for high temperature
                if sensor["value"] > 70:
                    sensor["status"] = "warning"
                    self._generate_alert(f"High temperature detected at {sensor['location']}", 
                                       f"Temperature: {sensor['value']:.1f}°C", 
                                       sensor["location"], "warning")
                elif sensor["value"] > 80:
                    sensor["status"] = "error"
                    self._generate_alert(f"Critical temperature at {sensor['location']}", 
                                       f"Temperature: {sensor['value']:.1f}°C - Immediate attention required", 
                                       sensor["location"], "error")
                else:
                    sensor["status"] = "normal"
                    
            elif "speed" in sensor_id:
                # Speed has more variation but tends to stay around target
                target_speed = 150
                sensor["value"] = max(100, min(200, target_speed + random.uniform(-10, 10)))
                sensor["status"] = "normal" if 140 <= sensor["value"] <= 170 else "warning"
                
            elif "vibration" in sensor_id:
                # Vibration can spike occasionally
                if random.random() < 0.05:  # 5% chance of spike
                    sensor["value"] = random.uniform(4, 8)
                    sensor["status"] = "warning"
                    self._generate_alert(f"High vibration detected", 
                                       f"Vibration level: {sensor['value']:.1f}g at {sensor['location']}", 
                                       sensor["location"], "warning")
                else:
                    sensor["value"] = max(0.5, min(5, sensor["value"] + random.uniform(-0.3, 0.3)))
                    sensor["status"] = "normal"
                    
            else:
                # General sensors
                variance = random.uniform(-2, 2)
                sensor["value"] = max(0, sensor["value"] + variance)
                sensor["status"] = "normal"
            
            sensor["timestamp"] = datetime.now().isoformat()
    
    def _move_packages(self):
        """Move packages through the conveyor system"""
        packages_to_remove = []
        
        for package_id, package in self.packages.items():
            if package.status == "delivered":
                continue
                
            # 30% chance to move to next location each update
            if random.random() < 0.3:
                current_index = self.conveyor_path.index(package.current_location)
                
                if current_index < len(self.conveyor_path) - 1:
                    # Move to next location
                    package.current_location = self.conveyor_path[current_index + 1]
                    
                    # Update status based on location
                    if "Loading Bay" in package.current_location:
                        package.status = "delivered"
                        self.stats['packages_processed'] += 1
                        logger.info(f"Package {package_id} delivered to {package.current_location}")
                    elif "Sorting" in package.current_location:
                        package.status = "sorting"
                    else:
                        package.status = "in_transit"
                else:
                    # Package reached end - mark as delivered
                    package.status = "delivered"
                    packages_to_remove.append(package_id)
                    self.stats['packages_processed'] += 1
        
        # Remove delivered packages after 30 seconds
        for package_id in packages_to_remove:
            if package_id in self.packages:
                delivered_time = datetime.fromisoformat(self.packages[package_id].received_at)
                if datetime.now() - delivered_time > timedelta(seconds=30):
                    del self.packages[package_id]
    
    def _generate_alert(self, title: str, description: str, location: str, severity: str):
        """Generate a system alert"""
        # Don't duplicate alerts
        for alert in self.alerts:
            if alert.title == title and alert.is_active:
                return
                
        alert = SystemAlert(
            id=self.alert_counter,
            type="sensor" if "temperature" in title.lower() or "vibration" in title.lower() else "system",
            title=title,
            description=description,
            location=location,
            severity=severity,
            created_at=datetime.now().isoformat()
        )
        
        self.alerts.append(alert)
        self.alert_counter += 1
        logger.warning(f"Alert generated: {title}")
    
    def _simulate_random_events(self):
        """Simulate random system events"""
        if random.random() < 0.02:  # 2% chance
            events = [
                ("Package jam detected", "Conveyor temporarily stopped for clearance", "Conveyor Belt 2", "warning"),
                ("Maintenance reminder", "Scheduled maintenance due in 2 days", "Motor Room A", "info"),
                ("High throughput", "System operating at 95% capacity", "Main System", "info"),
                ("Scanner error", "Barcode scanner needs calibration", "Scanner Station B", "warning"),
                ("Low air pressure", "Pneumatic system pressure below optimal", "Pneumatic System", "warning")
            ]
            
            title, desc, location, severity = random.choice(events)
            self._generate_alert(title, desc, location, severity)
    
    def _update_statistics(self):
        """Update system statistics"""
        self.stats['total_packages_today'] += random.randint(0, 2)
        self.stats['throughput_hour'] = len([p for p in self.packages.values() if p.status != "delivered"])
        
        # Efficiency calculation based on various factors
        base_efficiency = 85
        temp_sensors = [s for s in self.sensors.values() if "temperature" in s["id"]]
        avg_temp = sum(s["value"] for s in temp_sensors) / len(temp_sensors)
        
        if avg_temp > 70:
            base_efficiency -= 5
        if len(self.alerts) > 3:
            base_efficiency -= 10
            
        self.stats['efficiency'] = max(70, min(98, base_efficiency + random.uniform(-2, 2)))
    
    def start_simulation(self):
        """Start the simulation"""
        self.running = True
        logger.info("🚀 Starting real-time logistics simulation...")
        
        def simulation_loop():
            while self.running:
                try:
                    # Add new packages occasionally
                    if random.random() < 0.3:  # 30% chance
                        new_package = self._generate_package()
                        self.packages[new_package.id] = new_package
                        logger.info(f"📦 New package added: {new_package.id}")
                    
                    # Update all components
                    self._update_sensors()
                    self._move_packages()
                    self._simulate_random_events()
                    self._update_statistics()
                    
                    # Auto-resolve some alerts after time
                    for alert in self.alerts:
                        if alert.is_active and alert.severity != "error":
                            created_time = datetime.fromisoformat(alert.created_at)
                            if datetime.now() - created_time > timedelta(minutes=2):
                                alert.is_active = False
                    
                    time.sleep(3)  # Update every 3 seconds
                    
                except Exception as e:
                    logger.error(f"Simulation error: {e}")
                    time.sleep(1)
        
        self.simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
        self.simulation_thread.start()
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        logger.info("🛑 Stopping logistics simulation...")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        uptime = datetime.now() - self.stats['system_uptime']
        active_alerts = len([a for a in self.alerts if a.is_active])
        
        return {
            'plc_connected': True,  # Simulation mode
            'database_connected': True,
            'active_sensors': len(self.sensors),
            'active_actuators': 6,
            'packages_in_system': len([p for p in self.packages.values() if p.status != "delivered"]),
            'alerts_count': active_alerts,
            'system_uptime': f"{uptime.days} days, {uptime.seconds//3600} hours",
            'efficiency': f"{self.stats['efficiency']:.1f}%",
            'throughput_today': self.stats['total_packages_today'],
            'last_updated': datetime.now().isoformat()
        }
    
    def get_sensor_data(self) -> List[Dict[str, Any]]:
        """Get current sensor readings"""
        return [
            {
                'id': sensor_id,
                'name': sensor['name'],
                'value': round(sensor['value'], 1),
                'unit': sensor['unit'],
                'status': sensor['status'],
                'location': sensor['location'],
                'timestamp': sensor['timestamp']
            }
            for sensor_id, sensor in self.sensors.items()
        ]
    
    def get_active_packages(self) -> List[Dict[str, Any]]:
        """Get active packages"""
        return [asdict(package) for package in self.packages.values() if package.status != "delivered"]
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts"""
        return [asdict(alert) for alert in self.alerts if alert.is_active][-10:]  # Last 10 alerts
    
    def get_throughput_analytics(self) -> Dict[str, Any]:
        """Get throughput analytics"""
        # Generate realistic hourly data
        current_hour = datetime.now().hour
        hourly_data = []
        
        for i in range(12):
            hour = (current_hour - 11 + i) % 24
            # Higher throughput during work hours
            if 8 <= hour <= 17:
                base_throughput = random.randint(45, 65)
            else:
                base_throughput = random.randint(10, 25)
            hourly_data.append(base_throughput)
        
        return {
            'hourly_throughput': hourly_data,
            'daily_average': sum(hourly_data) / len(hourly_data),
            'weekly_total': sum(hourly_data) * 7,
            'efficiency': self.stats['efficiency'],
            'peak_hour': f"{max(range(len(hourly_data)), key=lambda i: hourly_data[i]) + 8}:00",
            'packages_processed_today': self.stats['packages_processed'],
            'current_load': len(self.packages),
            'last_updated': datetime.now().isoformat()
        }

# Global simulator instance
simulator = None

def get_simulator() -> LogisticsSimulator:
    """Get the global simulator instance"""
    global simulator
    if simulator is None:
        simulator = LogisticsSimulator()
        simulator.start_simulation()
    return simulator
