"""
Package Model
Stores information about packages moving through the logistics system.
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database_config import Base

class Package(Base):
    """Model for tracking packages through the system"""
    __tablename__ = "packages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Package identification
    package_id = Column(String(100), unique=True, nullable=False, index=True)
    barcode = Column(String(100), nullable=True, index=True)
    rfid_tag = Column(String(100), nullable=True, index=True)
    
    # Package details
    weight = Column(Float, nullable=True)  # kg
    dimensions_length = Column(Float, nullable=True)  # cm
    dimensions_width = Column(Float, nullable=True)  # cm
    dimensions_height = Column(Float, nullable=True)  # cm
    
    # Destination and routing
    destination = Column(String(100), nullable=True)
    priority = Column(String(20), default="normal")  # high, normal, low
    customer_id = Column(String(50), nullable=True)
    
    # Current status
    current_location = Column(String(100), nullable=True)
    status = Column(String(50), default="in_transit")  # received, in_transit, sorting, delivered, error
    is_damaged = Column(Boolean, default=False)
    
    # Timestamps
    received_at = Column(DateTime(timezone=True), nullable=True)
    sorted_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional data
    notes = Column(Text, nullable=True)
    special_handling = Column(String(100), nullable=True)  # fragile, hazardous, etc.
    
    def __repr__(self):
        return f"<Package(id={self.id}, package_id='{self.package_id}', status='{self.status}', destination='{self.destination}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'package_id': self.package_id,
            'barcode': self.barcode,
            'rfid_tag': self.rfid_tag,
            'weight': self.weight,
            'dimensions': {
                'length': self.dimensions_length,
                'width': self.dimensions_width,
                'height': self.dimensions_height
            },
            'destination': self.destination,
            'priority': self.priority,
            'customer_id': self.customer_id,
            'current_location': self.current_location,
            'status': self.status,
            'is_damaged': self.is_damaged,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'sorted_at': self.sorted_at.isoformat() if self.sorted_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'notes': self.notes,
            'special_handling': self.special_handling
        }

class PackageEvent(Base):
    """Model for tracking package movement events"""
    __tablename__ = "package_events"
    
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(String(100), ForeignKey('packages.package_id'), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # scanned, moved, sorted, error, etc.
    location = Column(String(100), nullable=False)
    sensor_id = Column(String(50), nullable=True)  # Which sensor detected this event
    
    # Event data
    previous_location = Column(String(100), nullable=True)
    duration_at_location = Column(Float, nullable=True)  # seconds
    
    # Status and error tracking
    success = Column(Boolean, default=True)
    error_code = Column(String(20), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    event_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Additional data
    additional_data = Column(Text, nullable=True)  # JSON string for extra event data
    
    def __repr__(self):
        return f"<PackageEvent(id={self.id}, package_id='{self.package_id}', event='{self.event_type}', location='{self.location}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'package_id': self.package_id,
            'event_type': self.event_type,
            'location': self.location,
            'sensor_id': self.sensor_id,
            'previous_location': self.previous_location,
            'duration_at_location': self.duration_at_location,
            'success': self.success,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'event_timestamp': self.event_timestamp.isoformat() if self.event_timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'additional_data': self.additional_data
        }

class SystemAlert(Base):
    """Model for system alerts and notifications"""
    __tablename__ = "system_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # jam, error, maintenance, etc.
    severity = Column(String(20), nullable=False)  # critical, warning, info
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Location and source
    location = Column(String(100), nullable=True)
    sensor_id = Column(String(50), nullable=True)
    actuator_id = Column(String(50), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Resolution
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemAlert(id={self.id}, type='{self.alert_type}', severity='{self.severity}', active={self.is_active})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'sensor_id': self.sensor_id,
            'actuator_id': self.actuator_id,
            'is_active': self.is_active,
            'is_acknowledged': self.is_acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'is_resolved': self.is_resolved,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
