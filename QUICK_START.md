# 🚀 Quick Start Guide - Logistics PLC Python System

## Overview
This system connects industrial PLCs to Python applications for real-time monitoring, data collection, and analytics in logistics automation.

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git (optional)

### Step 1: Setup Environment
```bash
# Run the automated setup script
./setup.sh
```

Or manually:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
```

### Step 2: Configure System
Edit the `.env` file with your specific settings:
```bash
# PLC Connection (Modbus TCP)
PLC_HOST=192.168.1.100
PLC_PORT=502

# Database
DATABASE_URL=sqlite:///logistics_plc.db

# Web Dashboard
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

### Step 3: Test System
```bash
# Run system tests
python test_system.py
```

### Step 4: Start Application
```bash
# Start the full system
python main.py
```

## 🌐 Access Dashboard
Open your web browser and go to: `http://localhost:5000`

## 📋 System Components

### 1. PLC Communication
- **Modbus TCP**: `app/plc_connection/modbus_client.py`
- **OPC UA**: `app/plc_connection/opcua_client.py` (to be implemented)
- **MQTT**: `app/plc_connection/mqtt_client.py` (to be implemented)

### 2. Data Models
- **Sensor Data**: `app/models/sensor_data.py`
- **Package Tracking**: `app/models/package.py`

### 3. Web Dashboard
- **Main App**: `app/web_dashboard/app.py`
- **Templates**: `app/web_dashboard/templates/`
- **API Endpoints**: REST API for real-time data

### 4. Configuration
- **Settings**: `config/settings.py`
- **Database**: `config/database_config.py`

## 🔧 PLC Configuration

### Modbus Register Map (Example)
```
Input Registers (30000 series):
- 40001: Conveyor Speed 1 (RPM)
- 40002: Conveyor Speed 2 (RPM)
- 40003: Temperature Sensor (°C)
- 40004: Vibration Sensor (g-force)

Discrete Inputs (10000 series):
- 10001: Proximity Sensor 1
- 10002: Proximity Sensor 2
- 10003: Emergency Stop

Coils (00000 series):
- 00001: Conveyor 1 Start/Stop
- 00002: Conveyor 2 Start/Stop
- 00003: Diverter Control

Holding Registers (40000 series):
- 40101: Speed Setpoint 1
- 40102: Speed Setpoint 2
```

## 📊 Features

### Real-time Monitoring
- Live sensor readings
- Actuator status
- System alerts
- Package tracking

### Analytics
- Throughput analysis
- Performance metrics
- Predictive maintenance
- Bottleneck detection

### Control Interface
- Manual actuator control
- Emergency stops
- Speed adjustments
- System configuration

## 🔍 Troubleshooting

### Common Issues

1. **PLC Connection Failed**
   - Check network connectivity
   - Verify PLC IP address and port
   - Ensure Modbus TCP is enabled on PLC

2. **Database Errors**
   - Check DATABASE_URL in .env
   - Ensure write permissions for SQLite file
   - Run database initialization

3. **Web Dashboard Not Loading**
   - Check if port 5000 is available
   - Verify Flask dependencies are installed
   - Check firewall settings

### Debug Mode
```bash
# Enable debug logging
export DEBUG=True
python main.py
```

## 📝 Development

### Adding New Sensors
1. Update register map in `modbus_client.py`
2. Add sensor model in `sensor_data.py`
3. Update dashboard template

### Adding New Features
1. Create new modules in appropriate directories
2. Update API endpoints in `app.py`
3. Add frontend components in templates

## 🧪 Testing

### Unit Tests
```bash
# Run specific tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

### System Integration
```bash
# Test all components
python test_system.py

# Test specific component
python -c "from test_system import test_database; test_database()"
```

## 📚 API Documentation

### REST Endpoints
- `GET /api/system/status` - System status
- `GET /api/sensors/data` - Current sensor readings
- `GET /api/packages/active` - Active packages
- `GET /api/alerts/active` - Active alerts
- `POST /api/control/actuator` - Control actuators

### WebSocket (Future)
- Real-time data streaming
- Live notifications
- Interactive control

## 🚀 Production Deployment

### Using Docker (Recommended)
```bash
# Build image
docker build -t logistics-plc .

# Run container
docker run -p 5000:5000 logistics-plc
```

### Using WSGI Server
```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "app.web_dashboard.app:create_app()"
```

## 📞 Support

For questions or issues:
1. Check the troubleshooting section
2. Review system logs in `logs/logistics_plc.log`
3. Run `python test_system.py` for diagnostics

---

**Happy Automating! 🏭**
