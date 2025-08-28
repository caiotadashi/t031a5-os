from flask import Flask, render_template, jsonify, request
from movements.unitree_g1 import UnitreeG1Movement
import threading
import os

app = Flask(__name__)
movement_handler = None

def initialize_movement_handler():
    global movement_handler
    try:
        network_interface = os.getenv('NETWORK_INTERFACE', 'eth0')
        movement_handler = UnitreeG1Movement(network_interface)
        print("Movement handler initialized successfully")
    except Exception as e:
        print(f"Failed to initialize movement handler: {e}")

# Initialize in a separate thread to prevent blocking
threading.Thread(target=initialize_movement_handler).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute_movement():
    if not movement_handler:
        return jsonify({'success': False, 'error': 'Movement handler not initialized'})
    
    data = request.get_json()
    movement = data.get('movement')
    
    if not movement:
        return jsonify({'success': False, 'error': 'No movement specified'})
    
    try:
        success = movement_handler.execute_movement(movement)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)