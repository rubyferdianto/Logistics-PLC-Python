"""
Modbus TCP Client for PLC Communication
Handles reading sensor data and writing actuator commands via Modbus protocol.
"""
import logging
import time
from typing import Dict, List, Optional, Union, Any
from pymodbus.client.tcp import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import json
from config.settings import settings

class ModbusClient:
    """Modbus TCP client for PLC communication"""
    
    def __init__(self, host: str = None, port: int = None, unit_id: int = None):
        self.host = host or settings.PLC_HOST
        self.port = port or settings.PLC_PORT
        self.unit_id = unit_id or settings.PLC_UNIT_ID
        self.timeout = settings.PLC_TIMEOUT
        
        self.client = None
        self.is_connected = False
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
        # Modbus register mappings (customize based on your PLC configuration)
        self.sensor_registers = {
            'conveyor_speed_1': {'address': 40001, 'type': 'input', 'unit': 'rpm'},
            'conveyor_speed_2': {'address': 40002, 'type': 'input', 'unit': 'rpm'},
            'temperature_1': {'address': 40003, 'type': 'input', 'unit': '°C'},
            'vibration_1': {'address': 40004, 'type': 'input', 'unit': 'g'},
            'package_count': {'address': 40005, 'type': 'input', 'unit': 'count'},
            'proximity_sensor_1': {'address': 10001, 'type': 'discrete', 'unit': 'boolean'},
            'proximity_sensor_2': {'address': 10002, 'type': 'discrete', 'unit': 'boolean'},
            'emergency_stop': {'address': 10003, 'type': 'discrete', 'unit': 'boolean'},
        }
        
        self.actuator_registers = {
            'conveyor_start_1': {'address': 1, 'type': 'coil'},
            'conveyor_start_2': {'address': 2, 'type': 'coil'},
            'diverter_1': {'address': 3, 'type': 'coil'},
            'speed_setpoint_1': {'address': 40101, 'type': 'holding', 'unit': 'rpm'},
            'speed_setpoint_2': {'address': 40102, 'type': 'holding', 'unit': 'rpm'},
        }
    
    def connect(self) -> bool:
        """Establish connection to PLC"""
        try:
            self.client = ModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=self.timeout
            )
            
            if self.client.connect():
                self.is_connected = True
                self.logger.info(f"Connected to PLC at {self.host}:{self.port}")
                return True
            else:
                self.logger.error(f"Failed to connect to PLC at {self.host}:{self.port}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to PLC: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from PLC"""
        if self.client and self.is_connected:
            self.client.close()
            self.is_connected = False
            self.logger.info("Disconnected from PLC")
    
    def read_sensor_data(self, sensor_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Read sensor data from PLC
        
        Args:
            sensor_ids: List of sensor IDs to read. If None, reads all sensors.
            
        Returns:
            Dictionary with sensor data
        """
        if not self.is_connected:
            if not self.connect():
                return {}
        
        sensor_data = {}
        sensors_to_read = sensor_ids or list(self.sensor_registers.keys())
        
        for sensor_id in sensors_to_read:
            if sensor_id not in self.sensor_registers:
                self.logger.warning(f"Unknown sensor ID: {sensor_id}")
                continue
            
            register_info = self.sensor_registers[sensor_id]
            try:
                value = self._read_register(register_info)
                
                sensor_data[sensor_id] = {
                    'value': value,
                    'unit': register_info.get('unit', ''),
                    'timestamp': time.time(),
                    'status': 'ok' if value is not None else 'error'
                }
                
            except Exception as e:
                self.logger.error(f"Error reading sensor {sensor_id}: {e}")
                sensor_data[sensor_id] = {
                    'value': None,
                    'unit': register_info.get('unit', ''),
                    'timestamp': time.time(),
                    'status': 'error',
                    'error': str(e)
                }
        
        return sensor_data
    
    def write_actuator_command(self, actuator_id: str, value: Union[bool, int, float]) -> bool:
        """
        Write command to actuator
        
        Args:
            actuator_id: ID of the actuator
            value: Value to write (bool for coils, int/float for registers)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            if not self.connect():
                return False
        
        if actuator_id not in self.actuator_registers:
            self.logger.error(f"Unknown actuator ID: {actuator_id}")
            return False
        
        register_info = self.actuator_registers[actuator_id]
        
        try:
            success = self._write_register(register_info, value)
            if success:
                self.logger.info(f"Successfully wrote {value} to actuator {actuator_id}")
            else:
                self.logger.error(f"Failed to write to actuator {actuator_id}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error writing to actuator {actuator_id}: {e}")
            return False
    
    def _read_register(self, register_info: Dict) -> Optional[Union[bool, int, float]]:
        """Read a single register based on its type"""
        address = register_info['address']
        reg_type = register_info['type']
        
        try:
            if reg_type == 'input':
                # Input registers (30000 series)
                result = self.client.read_input_registers(address - 30001, 1, unit=self.unit_id)
                if result.isError():
                    raise ModbusException(f"Modbus error reading input register {address}")
                return result.registers[0]
                
            elif reg_type == 'holding':
                # Holding registers (40000 series)
                result = self.client.read_holding_registers(address - 40001, 1, unit=self.unit_id)
                if result.isError():
                    raise ModbusException(f"Modbus error reading holding register {address}")
                return result.registers[0]
                
            elif reg_type == 'discrete':
                # Discrete inputs (10000 series)
                result = self.client.read_discrete_inputs(address - 10001, 1, unit=self.unit_id)
                if result.isError():
                    raise ModbusException(f"Modbus error reading discrete input {address}")
                return result.bits[0]
                
            elif reg_type == 'coil':
                # Coils (00000 series)
                result = self.client.read_coils(address - 1, 1, unit=self.unit_id)
                if result.isError():
                    raise ModbusException(f"Modbus error reading coil {address}")
                return result.bits[0]
                
        except Exception as e:
            self.logger.error(f"Error reading register {address} of type {reg_type}: {e}")
            return None
    
    def _write_register(self, register_info: Dict, value: Union[bool, int, float]) -> bool:
        """Write a single register based on its type"""
        address = register_info['address']
        reg_type = register_info['type']
        
        try:
            if reg_type == 'holding':
                # Holding registers (40000 series)
                result = self.client.write_register(address - 40001, int(value), unit=self.unit_id)
                return not result.isError()
                
            elif reg_type == 'coil':
                # Coils (00000 series)
                result = self.client.write_coil(address - 1, bool(value), unit=self.unit_id)
                return not result.isError()
                
            else:
                self.logger.error(f"Cannot write to register type {reg_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error writing register {address} of type {reg_type}: {e}")
            return False
    
    def read_all_sensors(self) -> Dict[str, Any]:
        """Read all configured sensors"""
        return self.read_sensor_data()
    
    def test_connection(self) -> bool:
        """Test PLC connection"""
        try:
            if not self.is_connected:
                if not self.connect():
                    return False
            
            # Try to read a simple register to test connection
            result = self.client.read_holding_registers(0, 1, unit=self.unit_id)
            return not result.isError()
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        return {
            'connected': self.is_connected,
            'host': self.host,
            'port': self.port,
            'unit_id': self.unit_id,
            'timeout': self.timeout
        }

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create Modbus client
    modbus_client = ModbusClient()
    
    # Test connection
    if modbus_client.connect():
        print("Connected to PLC successfully!")
        
        # Read sensor data
        sensor_data = modbus_client.read_all_sensors()
        print("Sensor data:", json.dumps(sensor_data, indent=2))
        
        # Write to actuator (example: start conveyor 1)
        success = modbus_client.write_actuator_command('conveyor_start_1', True)
        print(f"Start conveyor command sent: {success}")
        
        # Disconnect
        modbus_client.disconnect()
    else:
        print("Failed to connect to PLC")
