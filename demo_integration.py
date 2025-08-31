#!/usr/bin/env python3
"""
Demo script for PLC -> OPC UA -> MES -> DATABASE Integration
Shows the complete data flow and system capabilities
"""
import asyncio
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegrationDemo:
    """Demo class for showing integration capabilities"""
    
    def __init__(self):
        self.demo_data = {
            'conveyors': {
                'C1': {'running': True, 'speed': 75, 'load': 80, 'units_produced': 0},
                'C2': {'running': True, 'speed': 82, 'load': 85, 'units_produced': 0},
                'C3': {'running': False, 'speed': 0, 'load': 0, 'units_produced': 0}
            },
            'warehouses': {
                'WH_A': {'anode': 25, 'cathode': 20, 'electrolyte': 30},
                'WH_B': {'anode': 15, 'cathode': 25, 'electrolyte': 10},
                'WH_C': {'anode': 5, 'cathode': 10, 'electrolyte': 15}
            },
            'quality': {
                'pass_rate': 98.5,
                'total_tests': 1250,
                'recent_failures': 18
            },
            'production_orders': []
        }
    
    def print_banner(self):
        """Print demo banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  🏭 EV Manufacturing Integration Demo                                ║
║  PLC → OPC UA → MES → DATABASE                                      ║
║                                                                      ║
║  This demo shows how data flows through the complete integration:   ║
║  1. PLC generates production data                                    ║
║  2. OPC UA transmits data in real-time                             ║
║  3. MES processes and schedules production                          ║
║  4. Database stores all data for analytics                         ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def simulate_plc_data(self) -> Dict[str, Any]:
        """Simulate PLC data generation"""
        print("🔌 [PLC LAYER] Generating sensor data...")
        
        # Simulate conveyor operations
        for conveyor_id, status in self.demo_data['conveyors'].items():
            if status['running']:
                # Simulate production
                status['units_produced'] += 1
                
                # Simulate small variations in speed and load
                import random
                status['speed'] += random.randint(-2, 2)
                status['load'] += random.randint(-3, 3)
                
                # Keep within reasonable bounds
                status['speed'] = max(0, min(100, status['speed']))
                status['load'] = max(0, min(100, status['load']))
        
        # Simulate material consumption
        for warehouse_id, materials in self.demo_data['warehouses'].items():
            for material_type in materials:
                if materials[material_type] > 0:
                    # Consume materials randomly
                    if time.time() % 10 < 1:  # 10% chance per cycle
                        materials[material_type] = max(0, materials[material_type] - 1)
        
        plc_data = {
            'timestamp': datetime.now().isoformat(),
            'conveyors': self.demo_data['conveyors'].copy(),
            'warehouses': self.demo_data['warehouses'].copy(),
            'quality_sensors': {
                'pass_rate': self.demo_data['quality']['pass_rate'],
                'current_test_result': random.uniform(0.85, 1.0)
            }
        }
        
        print(f"   📊 Conveyor C1: {status['units_produced']} units, Speed: {self.demo_data['conveyors']['C1']['speed']}%")
        print(f"   📊 Conveyor C2: {self.demo_data['conveyors']['C2']['units_produced']} units, Speed: {self.demo_data['conveyors']['C2']['speed']}%")
        print(f"   📦 Warehouse levels: WH_A={sum(self.demo_data['warehouses']['WH_A'].values())}")
        
        return plc_data
    
    def simulate_opcua_transmission(self, plc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate OPC UA data transmission"""
        print("📡 [OPC UA LAYER] Transmitting data via industrial protocol...")
        
        # Simulate OPC UA node structure
        opcua_nodes = {}
        
        # Convert PLC data to OPC UA node format
        for conveyor_id, data in plc_data['conveyors'].items():
            opcua_nodes[f"ns=2;s=Conveyor.{conveyor_id}.Running"] = data['running']
            opcua_nodes[f"ns=2;s=Conveyor.{conveyor_id}.Speed"] = data['speed']
            opcua_nodes[f"ns=2;s=Conveyor.{conveyor_id}.Load"] = data['load']
            opcua_nodes[f"ns=2;s=Production.{conveyor_id}.Count"] = data['units_produced']
        
        for warehouse_id, materials in plc_data['warehouses'].items():
            for material_type, quantity in materials.items():
                opcua_nodes[f"ns=2;s=Warehouse.{warehouse_id.split('_')[1]}.{material_type.title()}"] = quantity
        
        opcua_nodes["ns=2;s=Quality.PassRate"] = plc_data['quality_sensors']['pass_rate']
        opcua_nodes["ns=2;s=Quality.LastTestResult"] = plc_data['quality_sensors']['current_test_result']
        
        print(f"   🌐 Transmitted {len(opcua_nodes)} OPC UA nodes")
        print(f"   📡 Connection Status: Connected to opc.tcp://localhost:4840")
        
        return {
            'timestamp': plc_data['timestamp'],
            'nodes': opcua_nodes,
            'connection_quality': 'Good',
            'security_mode': 'None'
        }
    
    def simulate_mes_processing(self, opcua_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate MES system processing"""
        print("🏭 [MES LAYER] Processing production data...")
        
        # Extract production metrics
        total_production = 0
        active_conveyors = 0
        
        for node_id, value in opcua_data['nodes'].items():
            if 'Production' in node_id and 'Count' in node_id:
                total_production += value
            elif 'Running' in node_id and value:
                active_conveyors += 1
        
        # Calculate KPIs
        efficiency = (active_conveyors / 3) * 100  # 3 total conveyors
        production_rate = total_production * 60  # Units per hour (approximate)
        
        # Check for production orders
        if len(self.demo_data['production_orders']) < 2:
            # Create new production order
            order_id = f"PO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            new_order = {
                'order_id': order_id,
                'product_type': 'Li-Ion_18650',
                'quantity': 100,
                'status': 'IN_PROGRESS',
                'assigned_conveyor': 'C1',
                'progress': (total_production % 100)
            }
            self.demo_data['production_orders'].append(new_order)
            print(f"   📋 Created production order: {order_id}")
        
        # Quality analysis
        quality_status = "GOOD" if opcua_data['nodes'].get("ns=2;s=Quality.PassRate", 0) > 95 else "WARNING"
        
        mes_output = {
            'timestamp': opcua_data['timestamp'],
            'production_metrics': {
                'total_units_produced': total_production,
                'active_conveyors': active_conveyors,
                'overall_efficiency': efficiency,
                'production_rate': production_rate
            },
            'quality_status': quality_status,
            'active_orders': len(self.demo_data['production_orders']),
            'inventory_alerts': self._check_inventory_alerts(),
            'kpis': {
                'oee': efficiency * 0.85,  # Overall Equipment Effectiveness
                'throughput': production_rate,
                'quality_score': opcua_data['nodes'].get("ns=2;s=Quality.PassRate", 0)
            }
        }
        
        print(f"   📈 Overall Efficiency: {efficiency:.1f}%")
        print(f"   🏭 Production Rate: {production_rate:.0f} units/hour")
        print(f"   ✅ Quality Status: {quality_status}")
        
        return mes_output
    
    def _check_inventory_alerts(self) -> list:
        """Check for low inventory alerts"""
        alerts = []
        for warehouse_id, materials in self.demo_data['warehouses'].items():
            for material_type, quantity in materials.items():
                if quantity < 10:
                    alerts.append(f"LOW_STOCK: {warehouse_id}/{material_type} = {quantity}")
        return alerts
    
    def simulate_database_storage(self, mes_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate database storage and analytics"""
        print("📊 [DATABASE LAYER] Storing data and generating analytics...")
        
        # Simulate database operations
        stored_records = {
            'production_metrics': 1,
            'quality_records': 1 if mes_data['quality_status'] != 'GOOD' else 0,
            'inventory_movements': len(mes_data['inventory_alerts']),
            'system_events': 1
        }
        
        # Generate analytics
        analytics = {
            'daily_production': mes_data['production_metrics']['total_units_produced'] * 24,  # Projected
            'efficiency_trend': 'IMPROVING',
            'quality_trend': 'STABLE',
            'top_performing_conveyor': 'C1',
            'maintenance_recommendations': []
        }
        
        # Add maintenance recommendations based on data
        if mes_data['production_metrics']['overall_efficiency'] < 80:
            analytics['maintenance_recommendations'].append("Schedule preventive maintenance for low-efficiency conveyors")
        
        if mes_data['inventory_alerts']:
            analytics['maintenance_recommendations'].append("Replenish low-stock materials")
        
        # Simulate database query performance
        query_performance = {
            'avg_response_time_ms': 15,
            'total_records': 125000,
            'index_utilization': 95.2
        }
        
        print(f"   💾 Stored {sum(stored_records.values())} records")
        print(f"   📈 Projected daily production: {analytics['daily_production']} units")
        print(f"   🔧 Maintenance alerts: {len(analytics['maintenance_recommendations'])}")
        
        return {
            'timestamp': mes_data['timestamp'],
            'stored_records': stored_records,
            'analytics': analytics,
            'query_performance': query_performance,
            'database_health': 'HEALTHY'
        }
    
    def generate_integration_report(self, plc_data: Dict, opcua_data: Dict, 
                                   mes_data: Dict, db_data: Dict) -> Dict[str, Any]:
        """Generate comprehensive integration report"""
        print("\n📋 [INTEGRATION REPORT] Generating system summary...")
        
        report = {
            'system_status': {
                'plc_connected': True,
                'opcua_connected': True,
                'mes_running': True,
                'database_healthy': db_data['database_health'] == 'HEALTHY'
            },
            'performance_summary': {
                'data_flow_latency_ms': 45,  # Total latency PLC -> DB
                'processing_efficiency': 98.5,
                'system_uptime': '99.8%',
                'error_rate': 0.02
            },
            'production_summary': {
                'total_units': mes_data['production_metrics']['total_units_produced'],
                'efficiency': mes_data['production_metrics']['overall_efficiency'],
                'quality_score': mes_data['kpis']['quality_score'],
                'active_orders': mes_data['active_orders']
            },
            'alerts_and_warnings': mes_data['inventory_alerts'] + db_data['analytics']['maintenance_recommendations'],
            'recommendations': [
                "System operating within normal parameters",
                "Continue monitoring inventory levels",
                "Schedule quarterly efficiency review"
            ]
        }
        
        return report
    
    def print_integration_summary(self, report: Dict[str, Any]):
        """Print final integration summary"""
        print("\n" + "="*70)
        print("🏭 INTEGRATION SYSTEM SUMMARY")
        print("="*70)
        
        # System Status
        status_icons = {True: "✅", False: "❌"}
        print("\n🔧 SYSTEM STATUS:")
        for component, status in report['system_status'].items():
            icon = status_icons[status]
            print(f"   {icon} {component.replace('_', ' ').title()}: {'Online' if status else 'Offline'}")
        
        # Performance
        print("\n📊 PERFORMANCE METRICS:")
        perf = report['performance_summary']
        print(f"   ⚡ Data Flow Latency: {perf['data_flow_latency_ms']}ms")
        print(f"   🎯 Processing Efficiency: {perf['processing_efficiency']}%")
        print(f"   ⏱️  System Uptime: {perf['system_uptime']}")
        print(f"   🐛 Error Rate: {perf['error_rate']}%")
        
        # Production
        print("\n🏭 PRODUCTION SUMMARY:")
        prod = report['production_summary']
        print(f"   📦 Total Units Produced: {prod['total_units']}")
        print(f"   ⚙️  Overall Efficiency: {prod['efficiency']:.1f}%")
        print(f"   ✅ Quality Score: {prod['quality_score']:.1f}%")
        print(f"   📋 Active Orders: {prod['active_orders']}")
        
        # Alerts
        if report['alerts_and_warnings']:
            print("\n⚠️  ALERTS & WARNINGS:")
            for alert in report['alerts_and_warnings']:
                print(f"   🚨 {alert}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"   ► {rec}")
        
        print("\n" + "="*70)
        print("🎉 Integration demo completed successfully!")
        print("="*70)
    
    async def run_demo(self, cycles: int = 5, interval: float = 2.0):
        """Run the complete integration demo"""
        self.print_banner()
        
        print(f"\n🚀 Starting integration demo ({cycles} cycles, {interval}s interval)...")
        print("\nPress Ctrl+C to stop the demo at any time.\n")
        
        try:
            for cycle in range(1, cycles + 1):
                print(f"\n{'='*50}")
                print(f"🔄 CYCLE {cycle}/{cycles}")
                print('='*50)
                
                # Step 1: PLC Data Generation
                plc_data = self.simulate_plc_data()
                await asyncio.sleep(0.5)
                
                # Step 2: OPC UA Transmission
                opcua_data = self.simulate_opcua_transmission(plc_data)
                await asyncio.sleep(0.5)
                
                # Step 3: MES Processing
                mes_data = self.simulate_mes_processing(opcua_data)
                await asyncio.sleep(0.5)
                
                # Step 4: Database Storage
                db_data = self.simulate_database_storage(mes_data)
                await asyncio.sleep(0.5)
                
                print(f"\n✅ Cycle {cycle} completed - Data processed through all layers")
                
                if cycle < cycles:
                    print(f"⏳ Waiting {interval}s before next cycle...")
                    await asyncio.sleep(interval)
            
            # Generate final report
            print(f"\n{'='*50}")
            print("📊 GENERATING FINAL REPORT")
            print('='*50)
            
            # Use data from last cycle for report
            final_report = self.generate_integration_report(plc_data, opcua_data, mes_data, db_data)
            self.print_integration_summary(final_report)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Demo interrupted by user")
            print("🏭 Integration system would normally continue running...")
        except Exception as e:
            print(f"\n❌ Demo error: {e}")
            logger.error(f"Demo error: {e}")

def main():
    """Main demo function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EV Manufacturing Integration Demo")
    parser.add_argument("--cycles", type=int, default=5, help="Number of demo cycles")
    parser.add_argument("--interval", type=float, default=2.0, help="Interval between cycles (seconds)")
    
    args = parser.parse_args()
    
    # Run the demo
    demo = IntegrationDemo()
    
    try:
        asyncio.run(demo.run_demo(cycles=args.cycles, interval=args.interval))
    except KeyboardInterrupt:
        print("\n👋 Demo terminated by user")

if __name__ == "__main__":
    main()
