import time
import json
import random
import threading
import logging
import signal
import sys
import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
PORT = 1883

TOPIC_PREFIX = "evfactory"
TOPIC_CONVEYOR = f"{TOPIC_PREFIX}/conveyor"      # publish per-conveyor updates to evfactory/conveyor/<id>
TOPIC_WAREHOUSE = f"{TOPIC_PREFIX}/warehouse"    # warehouse notifications
TOPIC_COMMANDS = f"{TOPIC_PREFIX}/commands"      # listen for operator commands

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("simulator")

client = mqtt.Client(client_id=f"sim-srv-{random.randint(1000,9999)}")

# Multiple warehouse locations with material stock
warehouses = {
    "WH_A": {  # Main warehouse
        "location": "Building A - Floor 1", 
        "anode": 30, 
        "cathode": 25, 
        "electrolyte": 35,
        "priority": 1
    },
    "WH_B": {  # Secondary warehouse
        "location": "Building B - Floor 2", 
        "anode": 20, 
        "cathode": 25, 
        "electrolyte": 15,
        "priority": 2
    },
    "WH_C": {  # Emergency stock
        "location": "Building C - Emergency Store", 
        "anode": 10, 
        "cathode": 15, 
        "electrolyte": 20,
        "priority": 3
    }
}

# Each conveyor has its own local buffer with assigned warehouse
conveyors = {
    "C1": {
        "anode": 5, "cathode": 5, "electrolyte": 5, 
        "status": "idle", 
        "assigned_warehouse": "WH_A",
        "location": "Production Line 1"
    },
    "C2": {
        "anode": 5, "cathode": 5, "electrolyte": 5, 
        "status": "idle", 
        "assigned_warehouse": "WH_B",
        "location": "Production Line 2"
    },
    "C3": {
        "anode": 5, "cathode": 5, "electrolyte": 5, 
        "status": "idle", 
        "assigned_warehouse": "WH_A",
        "location": "Production Line 3"
    },
}

running = True
lock = threading.Lock()

def publish(topic, payload):
    client.publish(topic, json.dumps(payload))
    logger.debug("Published %s -> %s", topic, payload)

def try_consume(conveyor_id):
    with lock:
        conv = conveyors[conveyor_id]
        # need 1 unit of each to process one battery
        if all(conv[m] >= 1 for m in ("anode", "cathode", "electrolyte")):
            for m in ("anode", "cathode", "electrolyte"):
                conv[m] -= 1
            conv["status"] = "processing"
            payload = {
                "conveyor": conveyor_id,
                "status": "processing",
                "materials_left": {k: conv[k] for k in ("anode","cathode","electrolyte")},
                "timestamp": time.time()
            }
            publish(f"{TOPIC_CONVEYOR}/{conveyor_id}", payload)
            logger.info("%s processed 1 battery. left=%s", conveyor_id, payload["materials_left"])
            return True
        else:
            # missing items -> request refill
            missing = [m for m in ("anode","cathode","electrolyte") if conv[m] <= 0]
            conv["status"] = "waiting"
            msg = {
                "conveyor": conveyor_id,
                "status": "waiting",
                "missing": missing,
                "timestamp": time.time()
            }
            publish(f"{TOPIC_CONVEYOR}/{conveyor_id}", msg)
            publish(TOPIC_WAREHOUSE, {"request_from": conveyor_id, "missing": missing})
            logger.info("%s waiting for materials: %s", conveyor_id, missing)
            return False

def get_total_warehouse_stock():
    """Get total stock across all warehouses"""
    total = {"anode": 0, "cathode": 0, "electrolyte": 0}
    for wh in warehouses.values():
        for material in total:
            total[material] += wh.get(material, 0)
    return total

def find_warehouse_for_material(material, amount, preferred_warehouse=None):
    """Find best warehouse for sourcing material"""
    # Try preferred warehouse first
    if preferred_warehouse and preferred_warehouse in warehouses:
        if warehouses[preferred_warehouse].get(material, 0) >= amount:
            return preferred_warehouse
    
    # Find warehouse with enough stock, sorted by priority
    available_warehouses = []
    for wh_id, wh_data in warehouses.items():
        if wh_data.get(material, 0) >= amount:
            available_warehouses.append((wh_id, wh_data.get('priority', 999)))
    
    if available_warehouses:
        available_warehouses.sort(key=lambda x: x[1])  # Sort by priority
        return available_warehouses[0][0]
    
    # If no warehouse has full amount, find one with partial stock
    for wh_id, wh_data in warehouses.items():
        if wh_data.get(material, 0) > 0:
            return wh_id
    
    return None

def robot_refill(conveyor_id, refill_amount=5):
    with lock:
        conv = conveyors[conveyor_id]
        preferred_wh = conv.get("assigned_warehouse")
        
        for m in ("anode","cathode","electrolyte"):
            # Find best warehouse for this material
            source_wh = find_warehouse_for_material(m, refill_amount, preferred_wh)
            
            if source_wh and warehouses[source_wh].get(m, 0) >= refill_amount:
                # Full transfer
                warehouses[source_wh][m] -= refill_amount
                conv[m] += refill_amount
                publish(f"{TOPIC_CONVEYOR}/{conveyor_id}", {
                    "conveyor": conveyor_id, 
                    "refilled": m, 
                    "amount": refill_amount, 
                    "source_warehouse": source_wh,
                    "warehouse_location": warehouses[source_wh]["location"],
                    "timestamp": time.time()
                })
                logger.info("Robot refilled %s for %s (+%d) from %s. remaining=%d", 
                           m, conveyor_id, refill_amount, source_wh, warehouses[source_wh][m])
            elif source_wh and warehouses[source_wh].get(m, 0) > 0:
                # Partial transfer
                available = warehouses[source_wh][m]
                warehouses[source_wh][m] = 0
                conv[m] += available
                publish(f"{TOPIC_CONVEYOR}/{conveyor_id}", {
                    "conveyor": conveyor_id, 
                    "refilled": m, 
                    "amount": available,
                    "source_warehouse": source_wh,
                    "warehouse_location": warehouses[source_wh]["location"], 
                    "timestamp": time.time()
                })
                logger.warning("Robot partially refilled %s for %s (+%d) from %s. warehouse empty", 
                              m, conveyor_id, available, source_wh)
                publish(TOPIC_WAREHOUSE, {
                    "warehouse_status": "low_stock", 
                    "material": m, 
                    "warehouse_id": source_wh,
                    "available": 0,
                    "total_stock": get_total_warehouse_stock()
                })
            else:
                # No stock available anywhere
                publish(TOPIC_WAREHOUSE, {
                    "warehouse_status": "out_of_stock", 
                    "material": m,
                    "total_stock": get_total_warehouse_stock()
                })
                logger.error("No %s available in any warehouse for %s", m, conveyor_id)
    
    # Notify conveyor status after refill
    publish(f"{TOPIC_CONVEYOR}/{conveyor_id}", {
        "conveyor": conveyor_id, 
        "status": "refilled", 
        "materials_left": {k: conv[k] for k in ("anode","cathode","electrolyte")},
        "assigned_warehouse": conv.get("assigned_warehouse"),
        "conveyor_location": conv.get("location"),
        "timestamp": time.time()
    })

def conveyor_worker(conveyor_id):
    while running:
        processed = try_consume(conveyor_id)
        if processed:
            # simulate processing time
            time.sleep(random.uniform(1.5, 3.0))
            # after processing set to idle and publish completion
            with lock:
                conveyors[conveyor_id]["status"] = "idle"
            publish(f"{TOPIC_CONVEYOR}/{conveyor_id}", {"conveyor": conveyor_id, "status": "idle", "timestamp": time.time()})
            time.sleep(0.5)
        else:
            # waiting: simulate robot fetch after short delay
            time.sleep(2.0)
            # robot performs refill
            robot_refill(conveyor_id, refill_amount=5)
            time.sleep(1.0)

def on_connect(client, userdata, flags, rc):
    logger.info("Connected to broker %s:%s rc=%s", BROKER, PORT, rc)
    client.subscribe(TOPIC_COMMANDS)
    # publish initial state
    with lock:
        for c in conveyors:
            publish(f"{TOPIC_CONVEYOR}/{c}", {
                "conveyor": c, 
                "status": conveyors[c]["status"], 
                "materials_left": {k: conveyors[c][k] for k in ("anode","cathode","electrolyte")},
                "assigned_warehouse": conveyors[c].get("assigned_warehouse"),
                "conveyor_location": conveyors[c].get("location"),
                "timestamp": time.time()
            })
    
    # Publish all warehouse states
    publish(TOPIC_WAREHOUSE, {
        "warehouses": warehouses, 
        "total_stock": get_total_warehouse_stock(),
        "timestamp": time.time()
    })

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        logger.exception("Invalid JSON on %s: %s", msg.topic, msg.payload)
        return
    logger.info("Command received on %s : %s", msg.topic, payload)
    
    cmd = payload.get("cmd")
    
    if cmd == "move_from_warehouse":
        # Enhanced manual material transfer: {"cmd":"move_from_warehouse","conveyor":"C1","material":"anode","amount":5,"warehouse":"WH_A"}
        conv_id = payload.get("conveyor")
        mat = payload.get("material")
        amt = int(payload.get("amount", 5))
        source_wh = payload.get("warehouse")  # Optional specific warehouse
        
        if conv_id in conveyors:
            # Find appropriate warehouse if not specified
            if not source_wh:
                source_wh = find_warehouse_for_material(mat, amt, conveyors[conv_id].get("assigned_warehouse"))
            
            if source_wh and source_wh in warehouses and mat in warehouses[source_wh]:
                with lock:
                    available = warehouses[source_wh].get(mat, 0)
                    transfer = min(amt, available)
                    if transfer > 0:
                        warehouses[source_wh][mat] -= transfer
                        conveyors[conv_id][mat] += transfer
                        
                        publish(TOPIC_WAREHOUSE, {
                            "manual_move": True, 
                            "conveyor": conv_id, 
                            "material": mat, 
                            "amount": transfer,
                            "source_warehouse": source_wh,
                            "warehouse_location": warehouses[source_wh]["location"],
                            "warehouses": warehouses,
                            "total_stock": get_total_warehouse_stock()
                        })
                        publish(f"{TOPIC_CONVEYOR}/{conv_id}", {
                            "conveyor": conv_id, 
                            "refilled": mat, 
                            "amount": transfer,
                            "source_warehouse": source_wh,
                            "warehouse_location": warehouses[source_wh]["location"], 
                            "timestamp": time.time()
                        })
                        logger.info("Manual transfer: %d %s from %s to %s", transfer, mat, source_wh, conv_id)
    
    elif cmd == "assign_warehouse":
        # Assign conveyor to different warehouse: {"cmd":"assign_warehouse","conveyor":"C1","warehouse":"WH_B"}
        conv_id = payload.get("conveyor")
        new_wh = payload.get("warehouse")
        
        if conv_id in conveyors and new_wh in warehouses:
            with lock:
                old_wh = conveyors[conv_id].get("assigned_warehouse")
                conveyors[conv_id]["assigned_warehouse"] = new_wh
                
                publish(f"{TOPIC_CONVEYOR}/{conv_id}", {
                    "conveyor": conv_id,
                    "warehouse_reassigned": True,
                    "old_warehouse": old_wh,
                    "new_warehouse": new_wh,
                    "new_warehouse_location": warehouses[new_wh]["location"],
                    "timestamp": time.time()
                })
                logger.info("Reassigned %s from %s to %s", conv_id, old_wh, new_wh)
    
    elif cmd == "restock_warehouse":
        # Restock warehouse: {"cmd":"restock_warehouse","warehouse":"WH_A","material":"anode","amount":50}
        wh_id = payload.get("warehouse")
        mat = payload.get("material")
        amt = int(payload.get("amount", 10))
        
        if wh_id in warehouses and mat in warehouses[wh_id]:
            with lock:
                warehouses[wh_id][mat] += amt
                
                publish(TOPIC_WAREHOUSE, {
                    "warehouse_restocked": True,
                    "warehouse_id": wh_id,
                    "material": mat,
                    "amount": amt,
                    "new_stock": warehouses[wh_id][mat],
                    "warehouses": warehouses,
                    "total_stock": get_total_warehouse_stock(),
                    "timestamp": time.time()
                })
                logger.info("Restocked %s: +%d %s (now: %d)", wh_id, amt, mat, warehouses[wh_id][mat])

def start_simulator():
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    threads = []
    for c in conveyors:
        t = threading.Thread(target=conveyor_worker, args=(c,), daemon=True)
        t.start()
        threads.append(t)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping simulator...")
    finally:
        global running
        running = False
        client.loop_stop()
        client.disconnect()
        for t in threads:
            t.join(timeout=1)
        logger.info("Simulator stopped.")

if __name__ == "__main__":
    print("Starting MQTT simulator. Broker:", BROKER)
    start_simulator()