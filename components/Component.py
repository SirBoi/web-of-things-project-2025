import threading

class Component:
    _id_counter = 1
    _lock = threading.Lock()

    def __init__(self, simulated):
        with Component._lock:
            self.id = Component._id_counter
            Component._id_counter += 1
            self.simulated = simulated
    
    #abstractmethod
    def run(self, break_event):
        pass

    #abstractmethod
    def run_simulated(self, break_event):
        pass

    #abstractmethod
    def execute(self, command_code):
        pass
    
    #abstractmethod
    def execute_simulated(self, command_code):
        pass