import random
import time
import json
import RPi.GPIO as GPIO
# import helper_files.LA_DHT as DHT
# import LA_DHT as DHT


class HumidityAndTemperatureSensor():
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated
        self.delay = 0.1
        self.PIN_NUMBER = 17

        self.dht = None
        self.sumCnt = None
        self.okCnt = None
        self.value = False

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        if (not self.simulated):
            self.dht = self.DHT(self.PIN_NUMBER)
            self.sumCnt = 0
            self.okCnt = 0

        while not break_event.is_set():
            with counter_lock:
                if (self.simulated):
                    dht_batch.append((self.name, json.dumps(self.get_reading_simulated()), 0, True))
                else:
                    dht_batch.append((self.name, json.dumps(self.get_reading()), 0, True))

                publish_data_counter["value"] += 1
                
                if publish_data_counter["value"] >= publish_data_limit["value"]:
                    publish_event.set()

            time.sleep(self.delay)
        
        try:
            GPIO.cleanup()
        finally:
            print(f"> {'SIMULATED ' if self.simulated else ''}Component {self.name} ({self.__class__.__name__}) turned off.")

    def get_reading(self):
        if (self.dht != None and self.sumCnt != None and self.okCnt != None):
            self.sumCnt += 1
            chk = self.dht.readDHT11()

            if (chk is 0):
                self.okCnt += 1	

            self.value = self.dht.humidity

        return self.formated_data()
    
    def get_reading_simulated(self):
        if random.randrange(50) == 0:
            self.value = not self.value

        return self.formated_data()
    
    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "value": float(self.value)
        }
    
    class DHT(object):
        DHTLIB_OK = 0
        DHTLIB_ERROR_CHECKSUM = -1
        DHTLIB_ERROR_TIMEOUT = -2
        DHTLIB_INVALID_VALUE = -999
        
        DHTLIB_DHT11_WAKEUP = 0.020#0.018		#18ms
        DHTLIB_TIMEOUT = 0.0001			#100us
        
        humidity = 0
        temperature = 0
        
        def __init__(self,pin):
            self.pin = pin
            self.bits = [0,0,0,0,0]
            GPIO.setmode(GPIO.BCM)
        #Read DHT sensor, store the original data in bits[]	
        def readSensor(self,pin,wakeupDelay):
            mask = 0x80
            idx = 0
            self.bits = [0,0,0,0,0]
            GPIO.setup(pin,GPIO.OUT)
            GPIO.output(pin,GPIO.LOW)
            time.sleep(wakeupDelay)
            GPIO.output(pin,GPIO.HIGH)
            #time.sleep(40*0.000001)
            GPIO.setup(pin,GPIO.IN)
            
            loopCnt = self.DHTLIB_TIMEOUT
            t = time.time()
            while(GPIO.input(pin) == GPIO.LOW):
                if((time.time() - t) > loopCnt):
                    #print ("Echo LOW")
                    return self.DHTLIB_ERROR_TIMEOUT
            t = time.time()
            while(GPIO.input(pin) == GPIO.HIGH):
                if((time.time() - t) > loopCnt):
                    #print ("Echo HIGH")
                    return self.DHTLIB_ERROR_TIMEOUT
            for i in range(0,40,1):
                t = time.time()
                while(GPIO.input(pin) == GPIO.LOW):
                    if((time.time() - t) > loopCnt):
                        #print ("Data Low %d"%(i))
                        return self.DHTLIB_ERROR_TIMEOUT
                t = time.time()
                while(GPIO.input(pin) == GPIO.HIGH):
                    if((time.time() - t) > loopCnt):
                        #print ("Data HIGH %d"%(i))
                        return self.DHTLIB_ERROR_TIMEOUT		
                if((time.time() - t) > 0.00005):	
                    self.bits[idx] |= mask
                #print("t : %f"%(time.time()-t))
                mask >>= 1
                if(mask == 0):
                    mask = 0x80
                    idx += 1	
            #print (self.bits)
            GPIO.setup(pin,GPIO.OUT)
            GPIO.output(pin,GPIO.HIGH)
            return self.DHTLIB_OK
        #Read DHT sensor, analyze the data of temperature and humidity
        def readDHT11(self):
            rv = self.readSensor(self.pin,self.DHTLIB_DHT11_WAKEUP)
            if (rv is not self.DHTLIB_OK):
                self.humidity = self.DHTLIB_INVALID_VALUE
                self.temperature = self.DHTLIB_INVALID_VALUE
                return rv
            self.humidity = self.bits[0]
            self.temperature = self.bits[2] + self.bits[3]*0.1
            sumChk = ((self.bits[0] + self.bits[1] + self.bits[2] + self.bits[3]) & 0xFF)
            if(self.bits[4] is not sumChk):
                return self.DHTLIB_ERROR_CHECKSUM
            return self.DHTLIB_OK
            
    def loop():
        dht = DHT(11)
        sumCnt = 0
        okCnt = 0
        while(True):
            sumCnt += 1
            chk = dht.readDHT11()	
            if (chk is 0):
                okCnt += 1		
            okRate = 100.0*okCnt/sumCnt
            print("sumCnt : %d, \t okRate : %.2f%% "%(sumCnt,okRate))
            print("chk : %d, \t Humidity : %.2f, \t Temperature : %.2f "%(chk,dht.humidity,dht.temperature))
            time.sleep(3)