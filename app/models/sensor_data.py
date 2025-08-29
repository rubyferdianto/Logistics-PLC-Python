"""
Sensor Data Model
Stores real-time data from various sensors in the logistics system.
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from config.database_config import Base

class SensorData(Base):
    """Model for storing sensor readings"""
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), nullable=False, index=True)
    sensor_type = Column(String(50), nullable=False)  # RFID, proximity, temperature, etc.
    location = Column(String(100), nullable=False)  # Conveyor belt section, scanner station, etc.
    
    # Sensor readings
    value = Column(Float, nullable=True)  # Numeric sensor value
    status = Column(String(20), default="active")  # active, inactive, error
    unit = Column(String(20), nullable=True)  # °C, rpm, g-force, etc.
    
    # Additional data
    raw_data = Column(Text, nullable=True)  # JSON string for complex data
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<SensorData(id={self.id}, sensor_id='{self.sensor_id}', type='{self.sensor_type}', value={self.value})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type,
            'location': self.location,
            'value': self.value,
            'status': self.status,
            'unit': self.unit,
            'raw_data': self.raw_data,
            'error_message': self.error_message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ActuatorData(Base):
    """Model for storing actuator states and commands"""
    __tablename__ = "actuator_data"
    
    id = Column(Integer, primary_key=True, index=True)
    actuator_id = Column(String(50), nullable=False, index=True)
    actuator_type = Column(String(50), nullable=False)  # motor, conveyor, valve, etc.
    location = Column(String(100), nullable=False)
    
    # Actuator states
    command = Column(String(50), nullable=False)  # start, stop, speed_change, etc.
    current_state = Column(String(20), nullable=False)  # running, stopped, error
    target_value = Column(Float, nullable=True)  # target speed, position, etc.
    actual_value = Column(Float, nullable=True)  # actual speed, position, etc.
    
    # Status and error tracking
    is_healthy = Column(Boolean, default=True)
    error_code = Column(String(20), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    command_sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    response_received_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ActuatorData(id={self.id}, actuator_id='{self.actuator_id}', command='{self.command}', state='{self.current_state}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'actuator_id': self.actuator_id,
            'actuator_type': self.actuator_type,
            'location': self.location,
            'command': self.command,
            'current_state': self.current_state,
            'target_value': self.target_value,
            'actual_value': self.actual_value,
            'is_healthy': self.is_healthy,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'command_sent_at': self.command_sent_at.isoformat() if self.command_sent_at else None,
            'response_received_at': self.response_received_at.isoformat() if self.response_received_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
