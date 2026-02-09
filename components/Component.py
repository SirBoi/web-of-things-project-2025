import threading
import time
import json

class Component:
    _id_counter = 1
    _lock = threading.Lock()

    def __init__(self, name, simulated):
        with Component._lock:
            self.id = Component._id_counter
            Component._id_counter += 1
            self.name = name
            self.simulated = simulated

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        0 # Implement later

    def run_simulated(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        while not break_event.is_set():
            with counter_lock:
                dht_batch.append((self.name, json.dumps(self.get_reading_simulated()), 0, True))
                publish_data_counter["value"] += 1
                
                if publish_data_counter["value"] >= publish_data_limit["value"]:
                    publish_event.set()

            time.sleep(self.delay)
        
        print(f"> [SIMULATED] Component {self.id} turned off")

    #abstractmethod
    def execute(self, command_code):
        pass
    
    #abstractmethod
    def execute_simulated(self, command_code):
        pass

    #abstractmethod
    def get_reading(self):
        pass

    #abstractmethod
    def get_reading_simulated(self):
        pass