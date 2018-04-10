import machine, ssd1306
import network
from umqtt.robust import MQTTClient
import utime as time
import ntptime
import gc


class main_app:
    def __init__(self):
        self.ssid_ = ""
        self.wp2_pass = ""

        self.tExt="N/A"
        self.pExt="N/A"
        self.tInt="N/A"
        self.pSolar="N/A"
        self.pUsed="N/A"

        self.heartbeat=1

        self.i2c = machine.I2C(scl=machine.Pin(4), sda=machine.Pin(5))

        self.oled = ssd1306.SSD1306_I2C(128, 64, self.i2c)


    def checkwifi(self):
        while not self.sta_if.isconnected():
            time.sleep_ms(500)
            print(".")
            self.oled.fill(0) 
            self.oled.text('Connecting', 0, 0)
            self.oled.text('SSID', 0, 10)
            self.oled.text('%s' % (self.ssid_,), 0, 20)
            self.oled.show()
            self.sta_if.connect()

    def do_connect(self):
        self.oled.fill(0) 
        self.oled.text('Connecting', 0, 0)
        self.oled.text('SSID', 0, 10)
        self.oled.text('%s' % (self.ssid_,), 0, 20)
        self.oled.show()

        self.sta_if = network.WLAN(network.STA_IF)
        if not self.sta_if.isconnected():
            print('connecting to network...')
            self.sta_if.active(True)
            self.sta_if.connect(self.ssid_, self.wp2_pass)
            while not self.sta_if.isconnected():
                time.sleep(0.5)

    def showData(self):
        now=time.localtime()
        strnow='%02d:%02d:%02d UTC' % (now[3],now[4],now[5])
        if self.heartbeat:
            strnow += '.'
            self.heartbeat = 0
        else:
            self.heartbeat = 1
        self.oled.fill(0) 
        self.oled.text(strnow, 0, 0)  
        self.oled.text('tI %s tO %s' % (self.tInt,self.tExt), 0, 10)
        self.oled.text('p %s' % (self.pExt,), 0, 20)
        self.oled.text('S %s U %s' % (self.pSolar,self.pUsed), 0, 30)
        self.oled.show()

    def sub_cb(self,topic, msg):
        if   topic==b'/caldaia/tExt/t':
            try:
                self.tExt="%.1f" % round(float(msg),1) 
            except:
                pass
        elif topic==b'/caldaia/barometer/p':
            try:
                self.pExt="%.1f mmHg" % round(float(msg),1) 
            except:
                pass
        elif topic==b'emon/emonpi/power1':
            self.pUsed="%4dW" % max(0,int(msg))
        elif topic==b'emon/emonpi/power2':
            self.pSolar="%4dW" % max(0,int(msg))
        elif topic==b'emon/emonpi/t1':
            try:
                self.tInt="%.1f" % round(float(msg),1) 
            except:
                pass
        else:
            print ((topic,msg))

    def set_ntp_time(self):
        self.oled.fill(0) 
        self.oled.text('Set NTP time...', 0, 0)
        self.oled.show()
        ntptime.settime()

    def run(self):
        self.do_connect()
        self.set_ntp_time()

        self.c = MQTTClient("esp32-01", "emonpi", user='emonpi', password='emonpimqtt2016')
        self.c.set_callback(self.sub_cb)
        self.c.connect()
        self.c.subscribe(b"/caldaia/tExt/t")
        self.c.subscribe(b"/caldaia/barometer/p")
        self.c.subscribe(b"emon/emonpi/power1")
        self.c.subscribe(b"emon/emonpi/power2")
        self.c.subscribe(b"emon/emonpi/t1")

        while True:
            # Non-blocking wait for message
            self.c.check_msg()
            # Then need to sleep to avoid 100% CPU usage (in a real
            # app other useful actions would be performed instead)
            self.showData()

            self.checkwifi()
            time.sleep(0.5)

        self.c.disconnect()

app=main_app()

app.run()
