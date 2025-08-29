"""
Flask Web Application for Logistics Dashboard
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import logging
from datetime import datetime, timedelta
import json
from app.data_processing.live_simulator import get_simulator

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    
    # Enable CORS for API endpoints
    CORS(app)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize the simulator
    simulator = get_simulator()
    
    @app.route('/')
    def dashboard():
        """Main dashboard page"""
        return render_template('live_dashboard.html')
    
    @app.route('/api/system/status')
    def system_status():
        """Get system status information"""
        return jsonify(simulator.get_system_status())
    
    @app.route('/api/sensors/data')
    def sensor_data():
        """Get current sensor readings"""
        return jsonify(simulator.get_sensor_data())
    
    @app.route('/api/packages/active')
    def active_packages():
        """Get packages currently in the system"""
        return jsonify(simulator.get_active_packages())
    
    @app.route('/api/alerts/active')
    def active_alerts():
        """Get active system alerts"""
        return jsonify(simulator.get_active_alerts())
    
    @app.route('/api/analytics/throughput')
    def throughput_analytics():
        """Get package throughput analytics"""
        return jsonify(simulator.get_throughput_analytics())
    
    @app.route('/api/control/actuator', methods=['POST'])
    def control_actuator():
        """Control an actuator"""
        data = request.get_json()
        actuator_id = data.get('actuator_id')
        command = data.get('command')
        value = data.get('value')
        
        logger.info(f"🎮 Actuator control: {actuator_id} -> {command} = {value}")
        
        # Simulate actuator response
        response = {
            'success': True,
            'message': f'Command sent to {actuator_id}',
            'actuator_id': actuator_id,
            'command': command,
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'simulation': True
        }
        
        return jsonify(response)
    
    @app.route('/api/system/inject_package', methods=['POST'])
    def inject_package():
        """Manually inject a new package for testing"""
        new_package = simulator._generate_package()
        simulator.packages[new_package.id] = new_package
        
        logger.info(f"📦 Manual package injection: {new_package.id}")
        
        return jsonify({
            'success': True,
            'message': f'Package {new_package.id} injected into system',
            'package': new_package.__dict__
        })
    
    @app.route('/api/system/trigger_alert', methods=['POST'])
    def trigger_alert():
        """Manually trigger an alert for testing"""
        data = request.get_json()
        title = data.get('title', 'Test Alert')
        description = data.get('description', 'This is a test alert')
        location = data.get('location', 'Test Location')
        severity = data.get('severity', 'warning')
        
        simulator._generate_alert(title, description, location, severity)
        
        logger.info(f"⚠️ Manual alert triggered: {title}")
        
        return jsonify({
            'success': True,
            'message': f'Alert "{title}" triggered',
            'alert': {
                'title': title,
                'description': description,
                'location': location,
                'severity': severity
            }
        })
    
    @app.route('/api/system/emergency_stop', methods=['POST'])
    def emergency_stop():
        """Emergency stop simulation"""
        simulator._generate_alert(
            "EMERGENCY STOP ACTIVATED",
            "Emergency stop button pressed - All conveyors stopped",
            "Main Control Panel",
            "error"
        )
        
        logger.warning("🚨 EMERGENCY STOP ACTIVATED")
        
        return jsonify({
            'success': True,
            'message': 'Emergency stop activated',
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/monitoring')
    def monitoring():
        """Real-time monitoring page"""
        return render_template('monitoring.html')
    
    @app.route('/analytics')
    def analytics():
        """Analytics and reports page"""
        return render_template('analytics.html')
    
    @app.route('/settings')
    def settings():
        """System settings page"""
        return render_template('settings.html')
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
