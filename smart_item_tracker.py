#!/usr/bin/env python3
"""
Smart Item Tracking System
PLC → SCADA → MES → Digital Twin → PLC Integration

This system demonstrates real-time item location tracking through
a complete industrial automation stack.
"""

import asyncio
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class ItemStatus(Enum):
    IN_PRODUCTION = "In Production"
    TESTING = "Testing"
    IN_STORAGE = "In Storage"
    ASSEMBLY = "Assembly"
    MAINTENANCE = "Maintenance"
    PACKAGING = "Packaging"
    SHIPPING = "Shipping"

@dataclass
class Item:
    id: str
    name: str
    location: str
    status: ItemStatus
    last_update: datetime
    properties: Dict[str, Any]

@dataclass
class LocationQuery:
    item_id: str
    requested_by: str
    timestamp: datetime
    priority: int = 1

@dataclass
class LocationResponse:
    item_id: str
    location: str
    status: str
    confidence: float
    response_time_ms: int
    digital_twin_verified: bool

class PLCController:
    """Simulates PLC with sensor data and item tracking"""
    
    def __init__(self):
        self.sensor_data = {}
        self.location_requests = []
        self.items_detected = {}
        
    async def scan_sensors(self) -> Dict[str, Any]:
        """Simulate sensor scanning for item detection"""
        print(f"[PLC] 🔧 Scanning sensors at {datetime.now().strftime('%H:%M:%S')}")
        
        # Simulate sensor readings
        sensor_readings = {}
        zones = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'D1', 'D2']
        
        for zone in zones:
            # Simulate RFID/Barcode sensor readings
            sensor_readings[f"sensor_{zone}"] = {
                'status': 'active',
                'items_detected': random.choice([0, 1, 1, 1]),  # Bias towards having items
                'signal_strength': random.uniform(85, 100),
                'last_reading': datetime.now().isoformat()
            }
            
        await asyncio.sleep(0.1)  # Simulate sensor processing time
        return sensor_readings
    
    async def request_item_location(self, item_id: str, priority: int = 1) -> LocationQuery:
        """Create a location request to be processed by SCADA"""
        query = LocationQuery(
            item_id=item_id,
            requested_by="PLC_Controller",
            timestamp=datetime.now(),
            priority=priority
        )
        
        print(f"[PLC] 📡 Location request generated for {item_id}")
        return query
    
    async def receive_location_response(self, response: LocationResponse):
        """Process location response from Digital Twin"""
        print(f"[PLC] ✅ Location response received: {response.item_id} → Zone {response.location}")
        print(f"[PLC] 📊 Confidence: {response.confidence:.1%}, Response time: {response.response_time_ms}ms")
        
        # Simulate PLC action based on location
        if response.confidence > 0.8:
            print(f"[PLC] 🎯 High confidence - Directing robot to Zone {response.location}")
        else:
            print(f"[PLC] ⚠️  Low confidence - Requesting manual verification")

class SCADASystem:
    """Handles data collection and processing from PLC"""
    
    def __init__(self):
        self.collected_data = {}
        self.data_buffer = []
        
    async def collect_sensor_data(self, plc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect and process sensor data from PLC"""
        print(f"[SCADA] 📊 Collecting data from {len(plc_data)} sensors")
        
        processed_data = {
            'timestamp': datetime.now().isoformat(),
            'total_sensors': len(plc_data),
            'active_sensors': sum(1 for data in plc_data.values() if data['status'] == 'active'),
            'items_detected': sum(data['items_detected'] for data in plc_data.values()),
            'avg_signal_strength': sum(data['signal_strength'] for data in plc_data.values()) / len(plc_data),
            'raw_data': plc_data
        }
        
        self.collected_data = processed_data
        await asyncio.sleep(0.05)  # Simulate processing time
        
        print(f"[SCADA] 📈 Data processed: {processed_data['items_detected']} items detected")
        return processed_data
    
    async def forward_to_mes(self, query: LocationQuery, scada_data: Dict[str, Any]) -> Dict[str, Any]:
        """Forward processed data to MES system"""
        forwarded_data = {
            'query': asdict(query),
            'scada_analysis': scada_data,
            'data_quality': 'high' if scada_data['avg_signal_strength'] > 90 else 'medium'
        }
        
        print(f"[SCADA] 🔄 Forwarding query for {query.item_id} to MES")
        return forwarded_data

class MESSystem:
    """Manufacturing Execution System for production tracking"""
    
    def __init__(self):
        self.production_orders = {}
        self.item_history = {}
        
    async def process_location_query(self, scada_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process location query with production context"""
        query = scada_data['query']
        item_id = query['item_id']
        
        print(f"[MES] ⚙️ Processing location query for {item_id}")
        
        # Simulate production context lookup
        production_context = {
            'current_order': f"PO_{random.randint(1000, 9999)}",
            'production_stage': random.choice(['assembly', 'testing', 'packaging']),
            'expected_location': random.choice(['A1', 'B2', 'C1']),
            'priority_level': query['priority']
        }
        
        enhanced_query = {
            'original_query': query,
            'production_context': production_context,
            'scada_data': scada_data['scada_analysis'],
            'mes_timestamp': datetime.now().isoformat()
        }
        
        await asyncio.sleep(0.1)  # Simulate MES processing
        print(f"[MES] 📋 Production context added - Stage: {production_context['production_stage']}")
        
        return enhanced_query

class DigitalTwin:
    """Digital Twin for virtual factory model and location tracking"""
    
    def __init__(self):
        self.virtual_model = {}
        self.item_locations = {
            'BATTERY_001': Item('BATTERY_001', 'Battery Unit #001', 'A1', ItemStatus.IN_PRODUCTION, datetime.now(), {}),
            'MOTOR_A45': Item('MOTOR_A45', 'Motor Assembly A45', 'B2', ItemStatus.TESTING, datetime.now(), {}),
            'CHASSIS_X12': Item('CHASSIS_X12', 'Chassis Frame X12', 'C1', ItemStatus.IN_STORAGE, datetime.now(), {}),
            'CONTROL_B78': Item('CONTROL_B78', 'Control Unit B78', 'A2', ItemStatus.ASSEMBLY, datetime.now(), {}),
            'SENSOR_S99': Item('SENSOR_S99', 'Sensor Module S99', 'D2', ItemStatus.MAINTENANCE, datetime.now(), {}),
            'CABLE_C33': Item('CABLE_C33', 'Cable Harness C33', 'C2', ItemStatus.PACKAGING, datetime.now(), {})
        }
        
    async def synchronize_with_physical(self, mes_data: Dict[str, Any]) -> bool:
        """Synchronize digital model with physical factory state"""
        print(f"[DIGITAL TWIN] 🌐 Synchronizing virtual model with physical factory")
        
        # Simulate synchronization with various data sources
        sync_sources = ['plc_sensors', 'scada_database', 'mes_orders', 'erp_system']
        
        for source in sync_sources:
            print(f"[DIGITAL TWIN] 🔄 Syncing with {source}...")
            await asyncio.sleep(0.02)
        
        # Update virtual model
        self.virtual_model = {
            'last_sync': datetime.now().isoformat(),
            'sync_quality': random.uniform(95, 99.9),
            'items_tracked': len(self.item_locations),
            'model_accuracy': random.uniform(98, 99.8)
        }
        
        print(f"[DIGITAL TWIN] ✅ Sync complete - Accuracy: {self.virtual_model['model_accuracy']:.1f}%")
        return True
    
    async def locate_item(self, mes_query: Dict[str, Any]) -> LocationResponse:
        """Find item location using digital twin model"""
        query = mes_query['original_query']
        item_id = query['item_id']
        
        start_time = time.time()
        print(f"[DIGITAL TWIN] 🔍 Searching for {item_id} in virtual model")
        
        # Simulate AI-powered location search
        await asyncio.sleep(0.15)  # Simulate complex search algorithms
        
        if item_id in self.item_locations:
            item = self.item_locations[item_id]
            confidence = random.uniform(85, 99) / 100
            
            # Update item last seen
            item.last_update = datetime.now()
            
            response = LocationResponse(
                item_id=item_id,
                location=item.location,
                status=item.status.value,
                confidence=confidence,
                response_time_ms=int((time.time() - start_time) * 1000),
                digital_twin_verified=True
            )
            
            print(f"[DIGITAL TWIN] 🎯 Item found: {item.name} at Zone {item.location}")
            print(f"[DIGITAL TWIN] 📊 Status: {item.status.value}, Confidence: {confidence:.1%}")
            
        else:
            response = LocationResponse(
                item_id=item_id,
                location="UNKNOWN",
                status="NOT_FOUND",
                confidence=0.0,
                response_time_ms=int((time.time() - start_time) * 1000),
                digital_twin_verified=False
            )
            
            print(f"[DIGITAL TWIN] ❌ Item {item_id} not found in virtual model")
        
        return response

class ItemTrackingOrchestrator:
    """Main orchestrator for the complete tracking flow"""
    
    def __init__(self):
        self.plc = PLCController()
        self.scada = SCADASystem()
        self.mes = MESSystem()
        self.digital_twin = DigitalTwin()
        
    async def track_item_location(self, item_id: str) -> LocationResponse:
        """Execute complete item tracking flow"""
        print(f"\n{'='*60}")
        print(f"🎯 STARTING ITEM TRACKING FLOW FOR: {item_id}")
        print(f"{'='*60}")
        
        try:
            # Step 1: PLC generates location request
            print(f"\n📍 STEP 1: PLC REQUEST GENERATION")
            print("-" * 40)
            query = await self.plc.request_item_location(item_id)
            
            # Step 2: PLC scans sensors
            print(f"\n🔧 STEP 2: PLC SENSOR SCANNING")
            print("-" * 40)
            sensor_data = await self.plc.scan_sensors()
            
            # Step 3: SCADA collects and processes data
            print(f"\n📊 STEP 3: SCADA DATA PROCESSING")
            print("-" * 40)
            scada_processed = await self.scada.collect_sensor_data(sensor_data)
            forwarded_data = await self.scada.forward_to_mes(query, scada_processed)
            
            # Step 4: MES adds production context
            print(f"\n⚙️ STEP 4: MES PRODUCTION CONTEXT")
            print("-" * 40)
            mes_enhanced = await self.mes.process_location_query(forwarded_data)
            
            # Step 5: Digital Twin synchronization and search
            print(f"\n🌐 STEP 5: DIGITAL TWIN PROCESSING")
            print("-" * 40)
            await self.digital_twin.synchronize_with_physical(mes_enhanced)
            location_response = await self.digital_twin.locate_item(mes_enhanced)
            
            # Step 6: PLC receives response
            print(f"\n🔄 STEP 6: PLC RESPONSE PROCESSING")
            print("-" * 40)
            await self.plc.receive_location_response(location_response)
            
            print(f"\n{'='*60}")
            print(f"✅ TRACKING FLOW COMPLETED FOR: {item_id}")
            print(f"📍 RESULT: Zone {location_response.location} ({location_response.confidence:.1%} confidence)")
            print(f"⏱️  TOTAL TIME: {location_response.response_time_ms}ms")
            print(f"{'='*60}\n")
            
            return location_response
            
        except Exception as e:
            print(f"❌ Error in tracking flow: {e}")
            raise

    async def demonstrate_system(self):
        """Run a complete system demonstration"""
        print("🏭 SMART ITEM TRACKING SYSTEM DEMONSTRATION")
        print("=" * 80)
        print("System Architecture: PLC → SCADA → MES → Digital Twin → PLC")
        print("=" * 80)
        
        # Available items to track
        items_to_track = ['BATTERY_001', 'MOTOR_A45', 'CHASSIS_X12', 'CONTROL_B78']
        
        for i, item_id in enumerate(items_to_track, 1):
            print(f"\n🎬 DEMONSTRATION {i}/{len(items_to_track)}")
            await self.track_item_location(item_id)
            
            if i < len(items_to_track):
                print("⏳ Waiting before next demonstration...")
                await asyncio.sleep(2)
        
        print("\n🎉 SYSTEM DEMONSTRATION COMPLETED!")
        print("All items successfully tracked through the complete automation stack.")

async def main():
    """Main entry point"""
    print("🚀 Initializing Smart Item Tracking System...")
    
    orchestrator = ItemTrackingOrchestrator()
    
    try:
        await orchestrator.demonstrate_system()
        
        # Interactive mode
        print("\n" + "="*50)
        print("🎮 INTERACTIVE MODE")
        print("="*50)
        
        while True:
            print("\nAvailable items:")
            items = list(orchestrator.digital_twin.item_locations.keys())
            for i, item in enumerate(items, 1):
                print(f"{i}. {item}")
            
            print("\nCommands:")
            print("- Enter item number (1-6) to track")
            print("- 'status' to show system status")
            print("- 'quit' to exit")
            
            user_input = input("\n🎯 Enter command: ").strip().lower()
            
            if user_input == 'quit':
                break
            elif user_input == 'status':
                print(f"\n📊 System Status:")
                print(f"  • Items tracked: {len(orchestrator.digital_twin.item_locations)}")
                print(f"  • Digital Twin accuracy: {orchestrator.digital_twin.virtual_model.get('model_accuracy', 'Unknown'):.1f}%")
                print(f"  • Last sync: {orchestrator.digital_twin.virtual_model.get('last_sync', 'Never')}")
            elif user_input.isdigit():
                try:
                    item_index = int(user_input) - 1
                    if 0 <= item_index < len(items):
                        item_id = items[item_index]
                        await orchestrator.track_item_location(item_id)
                    else:
                        print("❌ Invalid item number")
                except ValueError:
                    print("❌ Please enter a valid number")
            else:
                print("❌ Unknown command")
                
    except KeyboardInterrupt:
        print("\n\n🛑 System shutdown requested by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")
    finally:
        print("👋 Smart Item Tracking System terminated")

if __name__ == "__main__":
    asyncio.run(main())
