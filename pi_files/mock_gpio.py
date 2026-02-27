class MockPWM:
    def __init__(self, pin, freq):
        self.pin = pin
        self.freq = freq

    def start(self, duty):
        pass

    def ChangeDutyCycle(self, duty):
        pass

    def stop(self):
        pass

class MockGPIO:
    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"
    HIGH = 1
    LOW = 0
    PUD_UP = "PUD_UP"
    PUD_DOWN = "PUD_DOWN"
    BOTH = "BOTH"
    RISING = "RISING"
    FALLING = "FALLING"

    def setwarnings(self, flag):
        pass

    def setmode(self, mode):
        pass

    def setup(self, pin, mode, pull_up_down=None):
        pass

    def output(self, pin, value):
        pass

    def input(self, pin):
        return 0  # default "LOW"

    def cleanup(self):
        pass

    def add_event_detect(self, pin, edge, callback=None, bouncetime=0):
        pass

    def PWM(self, pin, freq):
        return MockPWM(pin, freq)

GPIO = MockGPIO()