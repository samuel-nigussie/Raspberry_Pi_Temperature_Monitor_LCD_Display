import spidev
import time
import RPi.GPIO as GPIO

LCD_PINS = {
    'RS': 15,  
    'E': 16,    
    'D4': 7,    
    'D5': 11,   
    'D6': 12,  
    'D7': 13    
}
TEMP_CHANNEL = 0
LCD_WIDTH = 16


GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

for pin in LCD_PINS.values():
    GPIO.setup(pin, GPIO.OUT)

spi = spidev.SpiDev()
spi.open(0, 0)  # Bus 0, Device 0 (CE0 = Pin 24)


def lcd_init():
    """Initialize LCD"""
    commands = [0x33, 0x32, 0x06, 0x0C, 0x28, 0x01]
    for cmd in commands:
        lcd_byte(cmd, False)
    time.sleep(0.0005)

def lcd_byte(value, is_char):
    """Send byte in 4-bit mode"""
    GPIO.output(LCD_PINS['RS'], is_char)
    
    for nibble in [value >> 4, value & 0x0F]:
        for i, pin in enumerate(['D4', 'D5', 'D6', 'D7']):
            GPIO.output(LCD_PINS[pin], bool(nibble & (1 << i)))
        lcd_pulse()

def lcd_pulse():
    """Pulse Enable pin"""
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(0.0005)
    GPIO.output(LCD_PINS['E'], False)
    time.sleep(0.0005)

def lcd_print(text, line):
    """Print to LCD line 1 or 2"""
    lcd_byte(0x80 if line == 1 else 0xC0, False)
    for char in text.ljust(LCD_WIDTH)[:LCD_WIDTH]:
        lcd_byte(ord(char), True)


def read_adc(channel):
    """Read from MCP3208 (12-bit ADC)"""
    # MCP3208 protocol: Start bit + SGL/DIFF + D2,D1,D0 + X,X,X,X
    # Byte 1: 0x06 (start + single mode)
    # Byte 2: channel << 6
    
    adc = spi.xfer2([0x06, (channel << 6), 0])
    
    # Combine 12-bit result from bytes 2 and 3
    # adc[1] has B11-B8 in lower nibble, adc[2] has B7-B0
    value = ((adc[1] & 0x0F) << 8) + adc[2]
    return value

def read_temp():
    """Convert LM35 reading to Celsius"""
    adc_value = read_adc(TEMP_CHANNEL)
    
    # LM35: 10mV per °C, 0V at 0°C
    # MCP3208: 12-bit (0-4095), 3.3V reference
    # Voltage = (adc / 4095) * 3.3
    # Temp = Voltage / 0.01 = Voltage * 100
    
    voltage = (adc_value * 3.3) / 4095
    temp = voltage * 100  # 10mV per °C
    
    return round(temp, 2)


def main():
    try:
        lcd_init()
        lcd_print("Temp Monitor", 1)
        time.sleep(1)
        
        while True:
            temp = read_temp()
            lcd_print(f"{temp} C", 2)
            time.sleep(1)
            
    except KeyboardInterrupt:
        pass
    finally:
        lcd_print("Goodbye!", 1)
        time.sleep(0.5)
        GPIO.cleanup()
        spi.close()

if __name__ == '__main__':
    main()
