"""
OPC UA Client for EV Manufacturing System
Connects PLC data to MES system via OPC UA protocol
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from asyncua import Client, Node, ua
from asyncua.common.subscription import SubHandler
import json

logger = logging.getLogger(__name__)

class PLCDataHandler(SubHandler):
    """Handler for OPC UA subscription data changes"""
    
    def __init__(self, callback: Callable = None):
        super().__init__()
        self.callback = callback
        
    def datachange_notification(self, node: Node, val, data):
        """Handle data change notifications from OPC UA server"""
        try:
            node_id = str(node.nodeid)
            timestamp = datetime.now().isoformat()
            
            data_point = {
                'node_id': node_id,
                'value': val,
                'timestamp': timestamp,
                'quality': str(data.monitored_item.Value.StatusCode)
            }
            
            logger.info(f"OPC UA Data Change - Node: {node_id}, Value: {val}")
            
            if self.callback:
                self.callback(data_point)
                
        except Exception as e:
            logger.error(f"Error processing OPC UA data change: {e}")

class OPCUAClient:
    """OPC UA Client for PLC Communication"""
    
    def __init__(self, endpoint: str, namespace: int = 2):
        self.endpoint = endpoint
        self.namespace = namespace
        self.client = None
        self.subscription = None
        self.connected = False
        self.data_handler = None
        self.monitored_nodes = {}
        
        # Define PLC node mappings for EV manufacturing
        self.plc_nodes = {
            # Conveyor Status
            'conveyor_c1_running': f"ns={namespace};s=Conveyor.C1.Running",
            'conveyor_c1_speed': f"ns={namespace};s=Conveyor.C1.Speed",
            'conveyor_c1_load': f"ns={namespace};s=Conveyor.C1.Load",
            'conveyor_c2_running': f"ns={namespace};s=Conveyor.C2.Running",
            'conveyor_c2_speed': f"ns={namespace};s=Conveyor.C2.Speed",
            'conveyor_c2_load': f"ns={namespace};s=Conveyor.C2.Load",
            'conveyor_c3_running': f"ns={namespace};s=Conveyor.C3.Running",
            'conveyor_c3_speed': f"ns={namespace};s=Conveyor.C3.Speed",
            'conveyor_c3_load': f"ns={namespace};s=Conveyor.C3.Load",
            
            # Production Data
            'production_count_c1': f"ns={namespace};s=Production.C1.Count",
            'production_count_c2': f"ns={namespace};s=Production.C2.Count",
            'production_count_c3': f"ns={namespace};s=Production.C3.Count",
            'production_rate_c1': f"ns={namespace};s=Production.C1.Rate",
            'production_rate_c2': f"ns={namespace};s=Production.C2.Rate",
            'production_rate_c3': f"ns={namespace};s=Production.C3.Rate",
            
            # Quality Control
            'quality_pass_rate': f"ns={namespace};s=Quality.PassRate",
            'quality_fail_count': f"ns={namespace};s=Quality.FailCount",
            'quality_last_test': f"ns={namespace};s=Quality.LastTestResult",
            
            # Warehouse Status
            'warehouse_a_anode': f"ns={namespace};s=Warehouse.A.Anode",
            'warehouse_a_cathode': f"ns={namespace};s=Warehouse.A.Cathode",
            'warehouse_a_electrolyte': f"ns={namespace};s=Warehouse.A.Electrolyte",
            'warehouse_b_anode': f"ns={namespace};s=Warehouse.B.Anode",
            'warehouse_b_cathode': f"ns={namespace};s=Warehouse.B.Cathode",
            'warehouse_b_electrolyte': f"ns={namespace};s=Warehouse.B.Electrolyte",
            
            # Robot Status
            'robot_active': f"ns={namespace};s=Robot.Active",
            'robot_position': f"ns={namespace};s=Robot.Position",
            'robot_task': f"ns={namespace};s=Robot.CurrentTask",
            
            # System Alarms
            'emergency_stop': f"ns={namespace};s=System.EmergencyStop",
            'maintenance_mode': f"ns={namespace};s=System.MaintenanceMode",
            'system_fault': f"ns={namespace};s=System.Fault"
        }
    
    async def connect(self) -> bool:
        """Connect to OPC UA server"""
        try:
            logger.info(f"Connecting to OPC UA server: {self.endpoint}")
            self.client = Client(url=self.endpoint)
            await self.client.connect()
            
            # Create subscription for data changes
            self.subscription = await self.client.create_subscription(
                period=100,  # 100ms update rate
                handler=self.data_handler or PLCDataHandler()
            )
            
            self.connected = True
            logger.info("Successfully connected to OPC UA server")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to OPC UA server: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from OPC UA server"""
        try:
            if self.subscription:
                await self.subscription.delete()
            
            if self.client:
                await self.client.disconnect()
            
            self.connected = False
            logger.info("Disconnected from OPC UA server")
            
        except Exception as e:
            logger.error(f"Error disconnecting from OPC UA server: {e}")
    
    async def subscribe_to_nodes(self, callback: Callable = None):
        """Subscribe to all PLC nodes for real-time monitoring"""
        if not self.connected or not self.subscription:
            logger.error("Not connected to OPC UA server")
            return False
        
        try:
            if callback:
                self.data_handler = PLCDataHandler(callback)
                
            # Subscribe to all defined PLC nodes
            for node_name, node_id in self.plc_nodes.items():
                try:
                    node = self.client.get_node(node_id)
                    handle = await self.subscription.subscribe_data_change(node)
                    self.monitored_nodes[node_name] = {
                        'node': node,
                        'handle': handle,
                        'node_id': node_id
                    }
                    logger.debug(f"Subscribed to node: {node_name} ({node_id})")
                    
                except Exception as e:
                    logger.warning(f"Failed to subscribe to node {node_name}: {e}")
            
            logger.info(f"Subscribed to {len(self.monitored_nodes)} PLC nodes")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to nodes: {e}")
            return False
    
    async def read_node(self, node_name: str):
        """Read a specific node value"""
        if not self.connected:
            logger.error("Not connected to OPC UA server")
            return None
        
        try:
            if node_name in self.plc_nodes:
                node_id = self.plc_nodes[node_name]
                node = self.client.get_node(node_id)
                value = await node.read_value()
                return value
            else:
                logger.error(f"Unknown node name: {node_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading node {node_name}: {e}")
            return None
    
    async def write_node(self, node_name: str, value):
        """Write a value to a specific node"""
        if not self.connected:
            logger.error("Not connected to OPC UA server")
            return False
        
        try:
            if node_name in self.plc_nodes:
                node_id = self.plc_nodes[node_name]
                node = self.client.get_node(node_id)
                await node.write_value(value)
                logger.info(f"Wrote value {value} to node {node_name}")
                return True
            else:
                logger.error(f"Unknown node name: {node_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error writing to node {node_name}: {e}")
            return False
    
    async def read_all_nodes(self) -> Dict:
        """Read all monitored node values"""
        if not self.connected:
            return {}
        
        data = {}
        for node_name in self.plc_nodes.keys():
            value = await self.read_node(node_name)
            if value is not None:
                data[node_name] = {
                    'value': value,
                    'timestamp': datetime.now().isoformat()
                }
        
        return data
    
    async def call_method(self, object_node: str, method_name: str, *args):
        """Call a method on the OPC UA server"""
        if not self.connected:
            logger.error("Not connected to OPC UA server")
            return None
        
        try:
            obj_node = self.client.get_node(object_node)
            method_node = obj_node.get_child(method_name)
            result = await obj_node.call_method(method_node, *args)
            return result
            
        except Exception as e:
            logger.error(f"Error calling method {method_name}: {e}")
            return None
    
    def get_connection_status(self) -> Dict:
        """Get current connection status"""
        return {
            'connected': self.connected,
            'endpoint': self.endpoint,
            'namespace': self.namespace,
            'monitored_nodes': len(self.monitored_nodes),
            'last_check': datetime.now().isoformat()
        }

# Utility functions for PLC operations
async def start_conveyor(opcua_client: OPCUAClient, conveyor_id: str) -> bool:
    """Start a specific conveyor"""
    node_name = f"conveyor_{conveyor_id.lower()}_running"
    return await opcua_client.write_node(node_name, True)

async def stop_conveyor(opcua_client: OPCUAClient, conveyor_id: str) -> bool:
    """Stop a specific conveyor"""
    node_name = f"conveyor_{conveyor_id.lower()}_running"
    return await opcua_client.write_node(node_name, False)

async def set_conveyor_speed(opcua_client: OPCUAClient, conveyor_id: str, speed: float) -> bool:
    """Set conveyor speed (0.0 - 100.0)"""
    node_name = f"conveyor_{conveyor_id.lower()}_speed"
    return await opcua_client.write_node(node_name, speed)

async def trigger_emergency_stop(opcua_client: OPCUAClient) -> bool:
    """Trigger emergency stop for entire system"""
    return await opcua_client.write_node("emergency_stop", True)

async def reset_emergency_stop(opcua_client: OPCUAClient) -> bool:
    """Reset emergency stop"""
    return await opcua_client.write_node("emergency_stop", False)

# Example usage
async def main():
    """Example usage of OPC UA client"""
    opcua_client = OPCUAClient("opc.tcp://localhost:4840")
    
    # Connect to server
    if await opcua_client.connect():
        
        # Subscribe to all nodes with callback
        def data_callback(data_point):
            print(f"Data received: {data_point}")
        
        await opcua_client.subscribe_to_nodes(callback=data_callback)
        
        # Read some specific values
        c1_running = await opcua_client.read_node("conveyor_c1_running")
        print(f"Conveyor C1 Running: {c1_running}")
        
        # Control operations
        await start_conveyor(opcua_client, "C1")
        await set_conveyor_speed(opcua_client, "C1", 75.0)
        
        # Keep running for a while
        await asyncio.sleep(10)
        
        # Disconnect
        await opcua_client.disconnect()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
