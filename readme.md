# 🏭 EV Manufacturing Simulation with Industrial Integration

## 🌟 Overview

This project implements a comprehensive **Electric Vehicle (EV) Manufacturing Simulation** with full industrial integration following the **PLC → OPC UA → MES → DATABASE** architecture. The system provides real-time monitoring, production control, quality management, and data analytics for EV battery manufacturing.

## 🏗️ System Architecture

### Integration Flow
```
┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐
│   PLC   │───▶│  OPC UA  │───▶│   MES   │───▶│ DATABASE │
└─────────┘    └──────────┘    └─────────┘    └──────────┘
     │              │              │              │
     ▼              ▼              ▼              ▼
• Conveyor Control  • Real-time     • Production   • Analytics
• Sensors           • Data Exchange • Scheduling   • Reporting
• Actuators         • Subscriptions • Quality      • Storage
• I/O Modules       • Commands      • Inventory    • History
```

### Components

#### 🔌 **PLC Layer** (Programmable Logic Controller)
- **Conveyor Control**: 3 production lines (C1, C2, C3)
- **Sensor Integration**: Speed, position, quality sensors
- **Material Handling**: Automated warehouse management
- **Safety Systems**: Emergency stops, fault detection

#### 📡 **OPC UA Layer** (Industrial Communication)
- **Real-time Data Exchange**: Standardized industrial protocol
- **Node Subscriptions**: Live monitoring of PLC variables
- **Bidirectional Communication**: Read/write operations
- **Security**: Authentication and encryption support

#### 🏭 **MES Layer** (Manufacturing Execution System)
- **Production Planning**: Order scheduling and management
- **Quality Control**: Real-time testing and validation
- **Resource Management**: Material and equipment tracking
- **Performance Monitoring**: KPIs and efficiency metrics

#### 📊 **Database Layer** (Data Management)
- **Real-time Storage**: Live production data
- **Historical Analytics**: Trends and reporting
- **Quality Records**: Test results and compliance
- **Inventory Tracking**: Material movements and levels

## 🚀 Quick Start

### 🎯 **Visualization Options**

**Option 1: Interactive HTML Dashboard (Recommended)**
```bash
# Standalone demo - No dependencies required!
open standalone_integration_demo.html

# Or run the web server for real-time data streaming
python launch_dashboard.py
```

**Option 2: Command Line Demo**
```bash
# Quick demo showing complete PLC→OPC UA→SCADA→MES→DATABASE flow
python demo_integration.py --cycles 5 --interval 2
```

### ⚙️ **System Operational Modes**

**Option 3: Full Integration System (Production)**
```bash
# Install dependencies
pip install -r requirements_integration.txt

# Setup database
python start_integration.py --setup-db

# Run full integration system
python start_integration.py

# Or run with debug logging
python start_integration.py --debug
```

### Option 2: Simulation Mode Only
```bash
# Run MQTT-based simulation
python start_integration.py --simulator

# Or directly run advanced simulator
python scripts/mqtt_simulator_advanced.py
```

### Option 3: MQTT Simulation Mode
```bash
# For development/testing with MQTT simulation
python start_integration.py --simulator

# Or run standalone MQTT simulator  
python scripts/mqtt_simulator_advanced.py
```

## 🎨 **Visualization Features**

### 📊 **Interactive HTML Dashboard**
- **Real-time Data Flow Animation**: Visual representation of PLC→OPC UA→SCADA→MES→DATABASE
- **Live Production Monitoring**: Conveyor status, production metrics, efficiency KPIs
- **System Health Dashboard**: Component status, alerts, performance metrics
- **Interactive Controls**: Start/stop production, emergency controls, speed adjustment
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### 🏭 **Industrial-Grade Monitoring**
- **SCADA-style Interface**: Professional industrial control aesthetics
- **Real-time Data Logs**: Live system events and data processing logs
- **Alarm Management**: Visual and text-based alert system
- **Inventory Tracking**: Live material consumption and warehouse levels
- **Performance Analytics**: OEE, quality rates, production forecasting

### 🎯 **Demo Capabilities**
- **Simulation Modes**: Standalone HTML demo or Python-driven real-time data
- **Configurable Speed**: Adjustable simulation speed (1x to 10x)
- **System Integration**: Shows complete data flow through all 5 layers
- **Educational Tool**: Perfect for understanding industrial automation concepts

## 🛠️ Installation

### Prerequisites
- **Python 3.8+**
- **OPC UA Server** (optional, for full integration)
- **MQTT Broker** (test.mosquitto.org used by default)

### Dependencies Installation
```bash
# Core integration dependencies
pip install -r requirements_integration.txt

# Alternative: Install individually
pip install asyncua pandas flask paho-mqtt sqlite3
```

### System Setup
```bash
# Check dependencies
python start_integration.py --check-deps

# Initialize database
python start_integration.py --setup-db

# Show configuration
python start_integration.py --show-config
```

## 📋 Integration Features

### 🔄 **Real-time Data Flow**
1. **PLC Data Collection**: Sensors and actuators send data via OPC UA
2. **Data Processing**: MES system processes and validates data
3. **Database Storage**: Historical and real-time data storage
4. **Analytics & Reporting**: KPIs, trends, and performance metrics

### 🏭 **Production Management**
- **Automated Scheduling**: Order creation and conveyor assignment
- **Real-time Monitoring**: Live production status and metrics
- **Quality Control**: Automated testing and validation
- **Inventory Management**: Material tracking and auto-restocking

### 📊 **Analytics & Monitoring**
- **Production KPIs**: OEE, efficiency, throughput
- **Quality Metrics**: Pass rates, defect analysis
- **System Health**: Component status and alarms
- **Historical Trends**: Long-term performance analysis
