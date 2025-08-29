"""
Test script for the Logistics PLC System
Run this to test different components of the system.
"""
import sys
import asyncio
from pathlib import Path

# Add app directory to Python path
sys.path.append(str(Path(__file__).parent))

from config.settings import settings
from config.database_config import test_connection, init_database

def test_database():
    """Test database connection and initialization"""
    print("🗃️  Testing database connection...")
    
    if test_connection():
        print("✅ Database connection successful")
        try:
            init_database()
            print("✅ Database tables created/verified")
            return True
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False
    else:
        print("❌ Database connection failed")
        return False

def test_modbus_connection():
    """Test Modbus PLC connection"""
    print("🏭 Testing Modbus PLC connection...")
    
    try:
        from app.plc_connection.modbus_client import ModbusClient
        
        client = ModbusClient()
        if client.test_connection():
            print("✅ Modbus PLC connection successful")
            client.disconnect()
            return True
        else:
            print("⚠️  Modbus PLC connection failed (this is normal if no PLC is connected)")
            return False
    except Exception as e:
        print(f"⚠️  Modbus test error: {e} (dependencies may not be installed)")
        return False

def test_web_app():
    """Test web application startup"""
    print("🌐 Testing web application...")
    
    try:
        from app.web_dashboard.app import create_app
        
        app = create_app()
        print("✅ Web application created successfully")
        print(f"🌐 Ready to serve on http://{settings.FLASK_HOST}:{settings.FLASK_PORT}")
        return True
    except Exception as e:
        print(f"❌ Web application test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("⚙️  Testing configuration...")
    
    try:
        print(f"  App Name: {settings.APP_NAME}")
        print(f"  Version: {settings.APP_VERSION}")
        print(f"  Debug Mode: {settings.DEBUG}")
        print(f"  PLC Host: {settings.PLC_HOST}:{settings.PLC_PORT}")
        print(f"  Database: {settings.DATABASE_URL}")
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def run_all_tests():
    """Run all system tests"""
    print("🧪 Running Logistics PLC System Tests")
    print("="*50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Database", test_database),
        ("Modbus PLC", test_modbus_connection),
        ("Web Application", test_web_app)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name} Test:")
        print("-" * 20)
        results[test_name] = test_func()
    
    print("\n" + "="*50)
    print("📊 Test Results Summary:")
    print("="*50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Your system is ready to use.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n💡 Tips:")
    print("  - If Modbus test fails, ensure your PLC is connected and configured correctly")
    print("  - If Database test fails, check your DATABASE_URL in .env file")
    print("  - Run 'python main.py' to start the full application")

if __name__ == "__main__":
    run_all_tests()
