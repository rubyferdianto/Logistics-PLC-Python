"""
Configuration settings for the Logistics PLC Python application.
"""
import os
from pathlib import Path
from typing import Optional

class Settings:
    """Application settings"""
    
    def __init__(self):
        # Application
        self.APP_NAME = os.getenv("APP_NAME", "Logistics PLC System")
        self.APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
        self.DEBUG = os.getenv("DEBUG", "True").lower() == "true"
        self.SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        
        # Database
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///logistics_plc.db")
        self.DATABASE_ECHO = os.getenv("DATABASE_ECHO", "False").lower() == "true"
        
        # PLC / MQTT / Broker
        self.MQTT_BROKER = os.getenv("MQTT_BROKER", "test.mosquitto.org")
        self.MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
        self.MQTT_WS_PORT = int(os.getenv("MQTT_WS_PORT", "8081"))
        self.MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "evfactory")
        self.PLC_HOST = os.getenv("PLC_HOST", "192.168.1.100")
        self.PLC_PORT = int(os.getenv("PLC_PORT", "502"))
        self.PLC_UNIT_ID = int(os.getenv("PLC_UNIT_ID", "1"))
        self.PLC_TIMEOUT = int(os.getenv("PLC_TIMEOUT", "10"))
        
        # OPC UA Settings
        self.OPCUA_ENDPOINT = os.getenv("OPCUA_ENDPOINT", "opc.tcp://192.168.1.100:4840")
        self.OPCUA_NAMESPACE = int(os.getenv("OPCUA_NAMESPACE", "2"))
        self.OPCUA_SECURITY_MODE = os.getenv("OPCUA_SECURITY_MODE", "None")
        self.OPCUA_SECURITY_POLICY = os.getenv("OPCUA_SECURITY_POLICY", "None")
        self.OPCUA_USERNAME = os.getenv("OPCUA_USERNAME", "")
        self.OPCUA_PASSWORD = os.getenv("OPCUA_PASSWORD", "")
        self.OPCUA_TIMEOUT = int(os.getenv("OPCUA_TIMEOUT", "30"))
        
        # MES System Settings
        self.MES_DATABASE_PATH = os.getenv("MES_DATABASE_PATH", "manufacturing.db")
        self.MES_UPDATE_INTERVAL = int(os.getenv("MES_UPDATE_INTERVAL", "5"))
        self.MES_AUTO_SCHEDULING = os.getenv("MES_AUTO_SCHEDULING", "true").lower() == "true"
        self.MES_QUALITY_THRESHOLD = float(os.getenv("MES_QUALITY_THRESHOLD", "95.0"))
        
        # Production Settings
        self.PRODUCTION_SCHEDULE_INTERVAL = int(os.getenv("PRODUCTION_SCHEDULE_INTERVAL", "3600"))  # 1 hour
        self.INVENTORY_CHECK_INTERVAL = int(os.getenv("INVENTORY_CHECK_INTERVAL", "300"))  # 5 minutes
        self.QUALITY_CHECK_INTERVAL = int(os.getenv("QUALITY_CHECK_INTERVAL", "60"))  # 1 minute
        self.LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "10"))
        self.AUTO_RESTOCK_AMOUNT = int(os.getenv("AUTO_RESTOCK_AMOUNT", "30"))
        
        # System Monitoring
        self.HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
        self.LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "30"))
        self.METRICS_RETENTION_DAYS = int(os.getenv("METRICS_RETENTION_DAYS", "90"))
        self.ENABLE_PERFORMANCE_MONITORING = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
        
        # Web Dashboard
        self.FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
        self.FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))
        
        # Data Processing
        self.DATA_COLLECTION_INTERVAL = int(os.getenv("DATA_COLLECTION_INTERVAL", "5"))
        self.ANALYTICS_INTERVAL = int(os.getenv("ANALYTICS_INTERVAL", "60"))
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "logs/logistics_plc.log")
        
        # Alert Thresholds
        self.JAM_DETECTION_THRESHOLD = float(os.getenv("JAM_DETECTION_THRESHOLD", "30.0"))
        self.TEMPERATURE_WARNING_THRESHOLD = float(os.getenv("TEMPERATURE_WARNING_THRESHOLD", "75.0"))
        self.VIBRATION_WARNING_THRESHOLD = float(os.getenv("VIBRATION_WARNING_THRESHOLD", "5.0"))

# Create settings instance
settings = Settings()

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
