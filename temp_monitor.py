from machine import Pin, I2C, SPI
from ssd1306 import SSD1306_I2C
import time, onewire, ds18x20, sdcard, uos


def main(
    display_pins={"sda": 0, "scl": 1},
    thermometer_pins=[20, 22],
    sd_pins={"cs": 13, "sck": 14, "mosi": 15, "miso": 12},
    sample_period=30,
):
    display = Display(**display_pins)
    therms = ThermometerArray(*thermometer_pins)
    mount_card(**sd_pins)
    logger = Logger()

    previous_second = 0
    while True:
        therms.convert()
        time.sleep(1)  # must be at least 0.75
        tempA, tempB = [str(t) for t in therms.read()]

        stamp = "{}:{}:{}".format(*time.localtime()[3:6])
        second = time.time()

        if second - previous_second >= sample_period:
            previous_second = second
            logger.log("\t".join([stamp, tempA, tempB]))
            logged = True
        else:
            logged = False

        display.update(stamp, tempA, tempB, logged)


def mount_card(cs, sck, mosi, miso):
    chip_select = Pin(cs, Pin.OUT)
    spi = SPI(
        1,
        baudrate=1000000,
        polarity=0,
        phase=0,
        bits=8,
        firstbit=SPI.MSB,
        sck=Pin(sck),
        mosi=Pin(mosi),
        miso=Pin(miso),
    )
    sd = sdcard.SDCard(spi, chip_select)
    vfs = uos.VfsFat(sd)
    uos.mount(vfs, "/sd")


class Logger:
    def __init__(self):
        self.filename = "/sd/" + "_".join(str(t) for t in time.localtime()[:5]) + ".txt"
        message = "beginning log {}\n".format(self.filename)
        print(message)
        with open(self.filename, "w") as file:
            file.write(message)

    def log(self, line):
        print(line)
        with open(self.filename, "a") as file:
            file.write(line + "\n")


class ThermometerArray:
    def __init__(self, *pins):
        self.thermometers = [ds18x20.DS18X20(onewire.OneWire(Pin(p))) for p in pins]
        self.therm_ids = [t.scan()[0] for t in self.thermometers]

    def convert(self):
        for t in self.thermometers:
            t.convert_temp()

    def read(self):
        return [t.read_temp(i) for t, i in zip(self.thermometers, self.therm_ids)]


class Display(SSD1306_I2C):
    def __init__(self, sda, scl):
        i2c = I2C(0, sda=Pin(sda), scl=Pin(scl), freq=400_000)
        super().__init__(128, 64, i2c)

        self.text("Time:", 0, 0)
        self.text("TempA:", 0, 20)
        self.text("TempB:", 0, 40)
        self.text("Loading...", 50, 55)
        self.show()

    def update(self, time, tempA, tempB, logged=False):
        self.fill_rect(50, 0, 78, 64, 0)
        self.text(time, 50, 0)
        self.text(tempA, 50, 20)
        self.text(tempB, 50, 40)
        if logged:
            self.text("Logged!", 50, 55)
        self.show()


if __name__ == "__main__":
    main()
