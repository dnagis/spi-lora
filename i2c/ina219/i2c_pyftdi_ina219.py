#!/usr/bin/python3
# -*-coding:Latin-1 -*

#ina219
#https://github.com/chrisb2/pi_ina219/
#"PGA" = Programmable Gain Amplifier

from pyftdi.i2c import I2cController, I2cNackError
from binascii import hexlify
from math import trunc
import time
import sys



def twos_comp(val):
    if (val & (1 << (16 - 1))) != 0: 
        val = val - (1 << 16)        
    return val                         


CONFIG_ADDR 	 = 0x00 
SHUNT_VOLT_ADDR	 = 0x01
BUS_VOLT_ADDR 	 = 0x02 
CURRENT_ADDR 	 = 0x04 
CALIBRATION_ADDR = 0x05


#initialisation du bus, de la puce FTDI
ctrl = I2cController()
ctrl.configure('ftdi://ftdi:2232h/1')

#https://eblot.github.io/pyftdi/api/i2c.html

slave = ctrl.get_port(0x40) #l'adresse sur le bus, i2cdetect (i2c-tools) ou i2cscan.py (pyftdi) -> voir le README.md 

#http://henrysbench.capnfatz.com/henrys-bench/arduino-current-measurements/ina219-arduino-current-sensor-voltmeter-tutorial-quick-start/

data = slave.read_from(CONFIG_ADDR,2)
CONFIG = data[0] << 8 | data[1] 
print("config = {:#010b} {:#010b} ({:x})".format(data[0], data[1], CONFIG)) #pour contrôle: au reset doit être à 399f

#print(twos_comp(int('1000001100000000',2)))


#slave.write_to(CONFIG_ADDR, b'\x00\x00') 


#Piste calibration
#J'ai du courant toujours à zero, normal selon DS: il faut remplir calibration register
#Logique: la resistance sur le breakout vient d'adafruit. Texas Instrument ne fabrique que l'ina219. Il faut dire à l'ina
#quelle est la valeur de la résistance.
#Programming page 5
#La map du register calibration est page 24

#max_possible_amps = shunt_volts_max / self._shunt_ohms ina219.py li 283
max_possible_amps = 32 / 100 #j'adapte. -> 32V de range
current_lsb = max_possible_amps / 32767
calibration = trunc(0.04096 / (current_lsb * 100)) #DS p.12 + ina219.py li 302

print("calibration= 0x{:x} decimal {:d}".format(calibration, calibration))







#c'est pas possible de laisser comme ça il faut créer un bytearray de size 2 mais le remplir correctement 
#	(quand ta calibration dépassera un byte)


cal_to_write = bytearray(2)
cal_to_write[1] = calibration


#Ensuite faut vérifier que la calibration est OK.




slave.write_to(CALIBRATION_ADDR, cal_to_write)
time.sleep(0.1)
calib_reg = slave.read_from(CALIBRATION_ADDR,2)
CALIB_REG = calib_reg[0] << 8 | calib_reg[1]
print("calibration reg = {:#010b} {:#010b} ({:x})".format(calib_reg[0], calib_reg[1], CALIB_REG)) 



while(True):
	data = slave.read_from(CURRENT_ADDR,2)
	RAW_DATA = data[0] << 8 | data[1]
	#print("{:#010b} {:#010b}".format(data[0], data[1]))
	sys.stdout.write("current = {:#010b} {:#010b}   \r".format( data[0], data[1]))
	#RESULT = twos_comp(RAW_DATA) * .01 #LSB = 4 mv pour le bus, 10 µV pour le shunt. Datasheet p.23
	#print("{:.2f}".format(RESULT))
	time.sleep(0.1)
	

#Le voltage du BUS a les 3 LSB qui ne holdent pas de value: DS p 12 le dit en bas + p.23 il faut shifter pour avoir valeurs
