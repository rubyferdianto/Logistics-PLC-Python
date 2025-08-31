"""
Advanced EV Manufacturing MQTT Simulator
Enterprise-grade simulation with warehouse management, quality control, and analytics
"""

import paho.mqtt.client as mqtt
import json
import time
import threading
import random
import logging
import uuid
import datetime
import signal
import sys
from database_manager import ManufacturingDatabase, ProductionOrder, WarehouseLocation, ConveyorStatus, QualityCheck

# Enhanced Configuration
BROKER = "test.mosquitto.org"
PORT = 1883

TOPIC_PREFIX = "evfactory"
TOPIC_CONVEYOR = f"{TOPIC_PREFIX}/conveyor"
TOPIC_WAREHOUSE = f"{TOPIC_PREFIX}/warehouse"
TOPIC_COMMANDS = f"{TOPIC_PREFIX}/commands"
TOPIC_QUALITY = f"{TOPIC_PREFIX}/quality"
TOPIC_PRODUCTION = f"{TOPIC_PREFIX}/production"
TOPIC_ANALYTICS = f"{TOPIC_PREFIX}/analytics"
TOPIC_ALERTS = f"{TOPIC_PREFIX}/alerts"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("advanced_simulator")

class AdvancedEVManufacturingSimulator:
    def __init__(self):
        self.client = mqtt.Client(client_id=f"ev-factory-{random.randint(1000,9999)}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Initialize database
        self.db = ManufacturingDatabase()
        
        # Enhanced warehouse system with multiple locations
        self.warehouses = {
            "WH-A1": {"anode": 200, "cathode": 180, "electrolyte": 250},
            "WH-B2": {"separator": 500, "casing": 400, "terminals": 600}, 
            "WH-C3": {"completed_batteries": 0},
            "WH-QC": {"quality_passed": 0, "quality_failed": 0}
        }
        
        # Enhanced conveyor system with specifications
        self.conveyors = {
            "C1": {
                "name": "High-Speed Line 1",
                "materials": {"anode": 5, "cathode": 5, "electrolyte": 5},
                "max_materials": 10,
                "status": "idle",
                "battery_type": "Li-Ion 18650",
                "production_rate": 120,  # batteries/hour
                "efficiency": 94.5,
                "temperature": 22.5,
                "vibration": 0.2,
                "current_order": None,
                "maintenance_due": False
            },
            "C2": {
                "name": "Precision Line 2", 
                "materials": {"anode": 5, "cathode": 5, "electrolyte": 5},
                "max_materials": 10,
                "status": "idle",
                "battery_type": "Li-Ion 21700",
                "production_rate": 100,
                "efficiency": 97.2,
                "temperature": 21.0,
                "vibration": 0.15,
                "current_order": None,
                "maintenance_due": False
            },
            "C3": {
                "name": "Heavy-Duty Line 3",
                "materials": {"anode": 5, "cathode": 5, "electrolyte": 5},
                "max_materials": 10,
                "status": "idle", 
                "battery_type": "LiFePO4 26650",
                "production_rate": 80,
                "efficiency": 91.8,
                "temperature": 20.5,
                "vibration": 0.25,
                "current_order": None,
                "maintenance_due": False
            }
        }
        
        # Production tracking
        self.production_stats = {
            "total_batteries": 0,
            "quality_passed": 0,
            "quality_failed": 0,
            "energy_consumption": 0.0,
            "co2_emissions": 0.0,
            "efficiency_average": 0.0
        }
        
        # Quality control parameters
        self.quality_standards = {
            "Li-Ion 18650": {"voltage": 3.7, "capacity": 2500, "resistance": 0.05},
            "Li-Ion 21700": {"voltage": 3.7, "capacity": 4000, "resistance": 0.04},
            "LiFePO4 26650": {"voltage": 3.2, "capacity": 3000, "resistance": 0.06}
        }
        
        self.running = False
        self.threads = []

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connected to MQTT broker {BROKER}:{PORT}")
            client.subscribe(f"{TOPIC_COMMANDS}/#")
            client.subscribe(f"{TOPIC_PRODUCTION}/orders")
            
            # Publish initial system status
            self.publish_system_status()
            
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            logger.info(f"Command received on {topic}: {payload}")
            
            if topic == f"{TOPIC_COMMANDS}/conveyor":
                self.handle_conveyor_command(payload)
            elif topic == f"{TOPIC_COMMANDS}/warehouse":
                self.handle_warehouse_command(payload)
            elif topic == f"{TOPIC_COMMANDS}/production":
                self.handle_production_command(payload)
            elif topic == f"{TOPIC_COMMANDS}/maintenance":
                self.handle_maintenance_command(payload)
            elif topic == f"{TOPIC_PRODUCTION}/orders":
                self.handle_production_order(payload)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def handle_conveyor_command(self, payload):
        """Handle conveyor-specific commands"""
        cmd = payload.get("cmd")
        conveyor_id = payload.get("conveyor")
        
        if cmd == "start" and conveyor_id in self.conveyors:
            self.conveyors[conveyor_id]["status"] = "running"
            logger.info(f"Started conveyor {conveyor_id}")
            
        elif cmd == "stop" and conveyor_id in self.conveyors:
            self.conveyors[conveyor_id]["status"] = "idle"
            logger.info(f"Stopped conveyor {conveyor_id}")
            
        elif cmd == "emergency_stop":
            for conv_id in self.conveyors:
                self.conveyors[conv_id]["status"] = "emergency_stop"
            logger.warning("EMERGENCY STOP activated on all conveyors")
            
        elif cmd == "refill_materials":
            self.refill_conveyor_materials(conveyor_id, payload.get("materials", {}))

    def handle_warehouse_command(self, payload):
        """Handle warehouse operations"""
        cmd = payload.get("cmd")
        
        if cmd == "restock":
            warehouse_id = payload.get("warehouse")
            materials = payload.get("materials", {})
            
            if warehouse_id in self.warehouses:
                for material, quantity in materials.items():
                    if material in self.warehouses[warehouse_id]:
                        self.warehouses[warehouse_id][material] += quantity
                    else:
                        self.warehouses[warehouse_id][material] = quantity
                
                # Log transaction
                transaction_id = str(uuid.uuid4())
                for material, quantity in materials.items():
                    self.db.log_material_transaction(
                        transaction_id, material, quantity, "INBOUND",
                        destination=warehouse_id, notes="Manual restock"
                    )
                
                logger.info(f"Restocked warehouse {warehouse_id} with {materials}")
                self.publish_warehouse_status()

    def handle_production_order(self, payload):
        """Handle new production orders"""
        order = ProductionOrder(
            id=payload.get("order_id", str(uuid.uuid4())),
            battery_type=payload.get("battery_type"),
            quantity=payload.get("quantity"),
            priority=payload.get("priority", "MEDIUM"),
            status="PENDING",
            created_at=datetime.datetime.now().isoformat(),
            due_date=payload.get("due_date")
        )
        
        self.db.upsert_production_order(order)
        logger.info(f"New production order created: {order.id}")
        
        # Auto-assign to available conveyor
        self.assign_production_order(order)

    def assign_production_order(self, order: ProductionOrder):
        """Automatically assign production order to best available conveyor"""
        best_conveyor = None
        best_efficiency = 0
        
        for conv_id, conv_data in self.conveyors.items():
            if (conv_data["status"] == "idle" and 
                conv_data["current_order"] is None and
                conv_data["efficiency"] > best_efficiency):
                best_conveyor = conv_id
                best_efficiency = conv_data["efficiency"]
        
        if best_conveyor:
            self.conveyors[best_conveyor]["current_order"] = order.id
            self.conveyors[best_conveyor]["status"] = "running"
            
            order.assigned_conveyor = best_conveyor
            order.status = "IN_PROGRESS"
            self.db.upsert_production_order(order)
            
            logger.info(f"Assigned order {order.id} to conveyor {best_conveyor}")

    def conveyor_worker(self, conveyor_id):
        """Enhanced conveyor processing with quality control"""
        while self.running:
            try:
                conv = self.conveyors[conveyor_id]
                
                if conv["status"] == "running":
                    # Check if materials are available
                    if all(conv["materials"][mat] > 0 for mat in ["anode", "cathode", "electrolyte"]):
                        
                        # Simulate processing time based on production rate
                        processing_time = 3600 / conv["production_rate"]  # seconds per battery
                        processing_time += random.uniform(-0.5, 0.5)  # Add variance
                        
                        time.sleep(processing_time)
                        
                        # Consume materials
                        for material in ["anode", "cathode", "electrolyte"]:
                            conv["materials"][material] -= 1
                        
                        # Produce battery
                        battery_id = f"BAT-{conveyor_id}-{int(time.time())}"
                        
                        # Quality control check
                        quality_result = self.perform_quality_check(battery_id, conveyor_id, conv["battery_type"])
                        
                        if quality_result.passed:
                            self.production_stats["quality_passed"] += 1
                            self.warehouses["WH-QC"]["quality_passed"] += 1
                            
                            # Move to finished goods
                            self.warehouses["WH-C3"]["completed_batteries"] += 1
                            
                        else:
                            self.production_stats["quality_failed"] += 1
                            self.warehouses["WH-QC"]["quality_failed"] += 1
                        
                        self.production_stats["total_batteries"] += 1
                        
                        # Update conveyor metrics
                        conv["temperature"] += random.uniform(-0.5, 0.5)
                        conv["vibration"] += random.uniform(-0.02, 0.02)
                        
                        # Energy consumption (kWh per battery)
                        energy_used = random.uniform(0.5, 1.2)
                        self.production_stats["energy_consumption"] += energy_used
                        
                        # CO2 emissions (kg per battery)
                        co2_produced = energy_used * 0.5  # Assume 0.5 kg CO2 per kWh
                        self.production_stats["co2_emissions"] += co2_produced
                        
                        logger.info(f"{conveyor_id} produced battery {battery_id}. Quality: {'PASS' if quality_result.passed else 'FAIL'}")
                        
                        # Publish updates
                        self.publish_conveyor_status(conveyor_id)
                        self.publish_production_metrics()
                        
                        # Random maintenance event
                        if random.random() < 0.001:  # 0.1% chance
                            conv["maintenance_due"] = True
                            conv["status"] = "maintenance_required"
                            logger.warning(f"{conveyor_id} requires maintenance")
                        
                    else:
                        # Waiting for materials
                        missing = [mat for mat in ["anode", "cathode", "electrolyte"] 
                                 if conv["materials"][mat] == 0]
                        
                        conv["status"] = "waiting_materials"
                        
                        self.client.publish(
                            f"{TOPIC_CONVEYOR}/{conveyor_id}",
                            json.dumps({
                                "conveyor": conveyor_id,
                                "status": "waiting",
                                "missing_materials": missing,
                                "materials_left": conv["materials"],
                                "timestamp": datetime.datetime.now().isoformat()
                            })
                        )
                        
                        # Auto-refill if warehouse has materials
                        self.auto_refill_materials(conveyor_id)
                        
                        time.sleep(2)
                        
                elif conv["status"] == "maintenance_required":
                    # Simulate maintenance time
                    time.sleep(10)
                    conv["status"] = "idle"
                    conv["maintenance_due"] = False
                    conv["efficiency"] = min(99.0, conv["efficiency"] + random.uniform(0.5, 1.5))
                    logger.info(f"{conveyor_id} maintenance completed. Efficiency: {conv['efficiency']:.1f}%")
                    
                else:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in conveyor {conveyor_id}: {e}")
                time.sleep(1)

    def perform_quality_check(self, battery_id: str, conveyor_id: str, battery_type: str) -> QualityCheck:
        """Perform comprehensive quality control testing"""
        standards = self.quality_standards[battery_type]
        
        # Simulate test measurements with realistic variations
        test_voltage = standards["voltage"] + random.uniform(-0.1, 0.1)
        test_capacity = standards["capacity"] + random.uniform(-100, 50)
        test_resistance = standards["resistance"] + random.uniform(-0.01, 0.01)
        temperature_test = 25.0 + random.uniform(-2, 2)
        
        # Determine pass/fail (95% pass rate)
        voltage_ok = abs(test_voltage - standards["voltage"]) <= 0.05
        capacity_ok = test_capacity >= standards["capacity"] * 0.9
        resistance_ok = test_resistance <= standards["resistance"] * 1.1
        
        passed = voltage_ok and capacity_ok and resistance_ok and random.random() < 0.95
        
        quality_check = QualityCheck(
            id=str(uuid.uuid4()),
            battery_id=battery_id,
            conveyor_id=conveyor_id,
            test_voltage=test_voltage,
            test_capacity=test_capacity,
            test_resistance=test_resistance,
            temperature_test=temperature_test,
            passed=passed,
            timestamp=datetime.datetime.now().isoformat(),
            notes="Automated quality check" + ("" if passed else " - Failed standards")
        )
        
        # Log to database
        self.db.log_quality_check(quality_check)
        
        # Publish quality result
        self.client.publish(
            f"{TOPIC_QUALITY}/{conveyor_id}",
            json.dumps({
                "battery_id": battery_id,
                "conveyor_id": conveyor_id,
                "test_results": {
                    "voltage": round(test_voltage, 2),
                    "capacity": round(test_capacity, 0),
                    "resistance": round(test_resistance, 4),
                    "temperature": round(temperature_test, 1)
                },
                "passed": passed,
                "timestamp": quality_check.timestamp
            })
        )
        
        return quality_check

    def auto_refill_materials(self, conveyor_id):
        """Automatically refill materials from warehouse"""
        conv = self.conveyors[conveyor_id]
        refilled = False
        
        for material in ["anode", "cathode", "electrolyte"]:
            if conv["materials"][material] == 0:
                # Check warehouse availability
                for warehouse_id, warehouse in self.warehouses.items():
                    if material in warehouse and warehouse[material] >= 5:
                        # Transfer materials
                        transfer_amount = min(5, warehouse[material], 
                                           conv["max_materials"] - conv["materials"][material])
                        
                        warehouse[material] -= transfer_amount
                        conv["materials"][material] += transfer_amount
                        
                        # Log transaction
                        self.db.log_material_transaction(
                            str(uuid.uuid4()), material, transfer_amount, "TRANSFER",
                            source=warehouse_id, destination=conveyor_id,
                            notes="Auto-refill"
                        )
                        
                        logger.info(f"Auto-refilled {material} for {conveyor_id} from {warehouse_id} (+{transfer_amount})")
                        refilled = True
                        break
        
        if refilled:
            conv["status"] = "running"
            self.publish_conveyor_status(conveyor_id)
            self.publish_warehouse_status()

    def publish_conveyor_status(self, conveyor_id):
        """Publish detailed conveyor status"""
        conv = self.conveyors[conveyor_id]
        
        status_data = {
            "conveyor": conveyor_id,
            "name": conv["name"],
            "status": conv["status"],
            "battery_type": conv["battery_type"],
            "materials_left": conv["materials"],
            "production_rate": conv["production_rate"],
            "efficiency": round(conv["efficiency"], 1),
            "temperature": round(conv["temperature"], 1),
            "vibration": round(conv["vibration"], 2),
            "current_order": conv["current_order"],
            "maintenance_due": conv["maintenance_due"],
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.client.publish(f"{TOPIC_CONVEYOR}/{conveyor_id}", json.dumps(status_data))

    def publish_warehouse_status(self):
        """Publish warehouse inventory status"""
        warehouse_data = {
            "warehouses": self.warehouses,
            "total_materials": sum(sum(wh.values()) for wh in self.warehouses.values()),
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.client.publish(TOPIC_WAREHOUSE, json.dumps(warehouse_data))

    def publish_production_metrics(self):
        """Publish production analytics"""
        total_tested = self.production_stats["quality_passed"] + self.production_stats["quality_failed"]
        quality_rate = (self.production_stats["quality_passed"] / max(1, total_tested)) * 100
        
        metrics = {
            "total_batteries_produced": self.production_stats["total_batteries"],
            "quality_pass_rate": round(quality_rate, 1),
            "energy_consumption_kwh": round(self.production_stats["energy_consumption"], 2),
            "co2_emissions_kg": round(self.production_stats["co2_emissions"], 2),
            "average_efficiency": round(sum(c["efficiency"] for c in self.conveyors.values()) / len(self.conveyors), 1),
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Update database
        self.db.update_production_metrics(
            self.production_stats["total_batteries"],
            metrics["average_efficiency"],
            100 - quality_rate,
            self.production_stats["energy_consumption"],
            self.production_stats["co2_emissions"],
            self.production_stats["quality_failed"]
        )
        
        self.client.publish(TOPIC_ANALYTICS, json.dumps(metrics))

    def publish_system_status(self):
        """Publish overall system status"""
        system_status = {
            "system": "EV Manufacturing Plant",
            "timestamp": datetime.datetime.now().isoformat(),
            "conveyors": len(self.conveyors),
            "warehouses": len(self.warehouses),
            "status": "OPERATIONAL",
            "uptime_hours": random.randint(720, 8760),  # 1 month to 1 year
            "version": "2.1.0"
        }
        
        self.client.publish(f"{TOPIC_PREFIX}/system", json.dumps(system_status))

    def analytics_worker(self):
        """Publish periodic analytics updates"""
        while self.running:
            try:
                time.sleep(30)  # Every 30 seconds
                
                if self.running:
                    self.publish_production_metrics()
                    self.publish_warehouse_status()
                    
                    # Publish quality metrics
                    quality_metrics = self.db.get_quality_metrics(24)
                    self.client.publish(f"{TOPIC_QUALITY}/metrics", json.dumps(quality_metrics))
                    
            except Exception as e:
                logger.error(f"Error in analytics worker: {e}")

    def start_simulator(self):
        """Start the advanced manufacturing simulator"""
        self.running = True
        
        # Connect to MQTT broker
        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return
        
        # Start conveyor threads
        for conveyor_id in self.conveyors:
            thread = threading.Thread(target=self.conveyor_worker, args=(conveyor_id,))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
        
        # Start analytics thread
        analytics_thread = threading.Thread(target=self.analytics_worker)
        analytics_thread.daemon = True
        analytics_thread.start()
        self.threads.append(analytics_thread)
        
        logger.info("Advanced EV Manufacturing Simulator started")
        
        # Signal handling
        def signal_handler(sig, frame):
            logger.info("Stopping simulator...")
            self.stop_simulator()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_simulator()

    def stop_simulator(self):
        """Stop the simulator gracefully"""
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1)
        
        # Disconnect MQTT
        self.client.loop_stop()
        self.client.disconnect()
        
        logger.info("Simulator stopped.")

if __name__ == "__main__":
    print("🏭 Starting Advanced EV Manufacturing Simulator...")
    print(f"📡 MQTT Broker: {BROKER}")
    print("🔋 Features: Warehouses, Quality Control, Analytics, Production Orders")
    
    simulator = AdvancedEVManufacturingSimulator()
    simulator.start_simulator()
