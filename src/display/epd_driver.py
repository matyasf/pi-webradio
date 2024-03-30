# 5.81" Pervasive Displays EPC with EXT3 board
# Fast update and fast global update functions using LUTs

import spidev  # SPI library
import time
from src.gpio_handler import InputPin, OutputPin
from src.display.pervasive_luts import fastLUT, globalLUT

# Raspberry Pi Zero, 2B, 3B, 4B configuration
class Ext3Board:
    def __init__(self) -> None:
        # EXT3 pin 1 Black -> +3.3V
        # EXT3 pin 2 Brown -> GPIO 11 SPI0 SCLK
        self.panelBusy = InputPin(7) # EXT3 pin 3 Red -> GPIO7 pin 26 (SPI chip select 1 / CE1)
        self.panelDC = OutputPin(8) # EXT3 pin 4 Orange -> GPIO8 pin 24 (SPI chip select 0 / CE0)
        self.panelReset = OutputPin(25) # EXT3 pin 5 Yellow -> GPIO25 pin 22
        # EXT3 pin 6 Green -> SPI MISO
        # EXT3 pin 7 Blue -> SPI MOSI
        self.panelCS = OutputPin(27) # EXT3 pin 9 Grey -> GPIO27 pin 13
        # EXT3 pin 6 Green -> GPIO9 SPI0 MISO
        # EXT3 pin 7 Blue -> GPIO10 SPI0 MOSI
        # flashCS = 22 # EXT3 pin 8 Violet -> GPIO22 pin 15
        # EXT3 pin 10 White -> GROUND  

class DisplayDriver:
    """Low level driver code for a 720x256 Pervasive displays ePaper connected via GPIO"""

    ext3Board: Ext3Board = None

    # CoG initialization function
    #   Implements Tcon (COG) power-on and temperature input to COG
    def COG_initial():
        DisplayDriver.ext3Board = Ext3Board()
        DisplayDriver.ext3Board.panelDC.on()
        DisplayDriver.ext3Board.panelReset.on()
        DisplayDriver.ext3Board.panelCS.on()

        global spi
        spi = spidev.SpiDev()
        spi.close()
        spi.open(0, 0)  # device 0 (SPI_CE0_N)
        spi.max_speed_hz = 8000000  # bit rate, 122000 works for sure
        spi.lsbfirst = False
        spi.mode = 0b00  # polarity CPOL=0 CPHA=0, bits
        spi.bits_per_word = 8 # read only on the Pi
        spi.no_cs = True

    # CoG shutdown function
    # Shuts down the CoG and DC/DC circuit after all update functions
    # TODO Buggy gets stuck waiting for BUSY to be low
    def COG_powerOff():
        register_turnOff = [0x7f, 0x7d, 0x00]
        DisplayDriver._sendIndexData(0x09, register_turnOff, 3)
        time.sleep(0.2)
        while DisplayDriver.ext3Board.panelBusy.is_active == False:
            time.sleep(0.05)
        DisplayDriver.ext3Board.panelDC.off()
        DisplayDriver.ext3Board.panelCS.off()
        DisplayDriver.ext3Board.panelBusy.off()# ??? looks wrong!
        time.sleep(0.15)
        DisplayDriver.ext3Board.panelReset.off()

    # Global update function
    def globalUpdate(data1s: list[int], data2s: list[int]):
        '''
        Global update command. Slower than fast update, but needs to be done sometimes.
        Parameters:
        - data1s: The new data to display
        - data2s: The data currently on the display
        '''
        #Utils.log("global update")
        DisplayDriver._reset()
        
        dtcl = [0x08] # 0=IST7232, 8=IST7236
        DisplayDriver._sendIndexData(0x01, dtcl, 1) #DCTL 0x10 of MTP
        
        # Send image data
        data1 = [0x00, 0x1f, 0x50, 0x00, 0x1f, 0x03] # DUW
        DisplayDriver._sendIndexData(0x13, data1, 6) # DUW
        data2 = [0x00, 0x1f, 0x00, 0xc9] # DRFW
        DisplayDriver._sendIndexData(0x90, data2, 4) # DRFW
        data3 = [0x1f, 0x50, 0x14] # RAM_RW
        DisplayDriver._sendIndexData(0x12, data3, 3) # RAM_RW

        # send first frame
        DisplayDriver._sendIndexData(0x10, data1s, 23040) # First frame

        data33 = [0x1f, 0x50, 0x14] # RAM_RW
        DisplayDriver._sendIndexData(0x12, data33, 3) # RAM_RW

        # send second frame
        DisplayDriver._sendIndexData(0x11, data2s, 23040) # Second frame
        DisplayDriver._DCDC_softStart_Mid(1)
        DisplayDriver.sendLUT(1)
        DisplayDriver._displayRefresh() # needed for min
        DisplayDriver._DCDC_softShutdown_Mid()

    def fastUpdate(data1s: list[int], data2s: list[int]):
        '''
        Fast update command. Can be called at most 15 times, then a global update
        is needed. Parameters:
        - data1s: The new data to display
        - data2s: The data currently on the display
        '''
        #Utils.log("Doing a fast update")
        DisplayDriver._reset()

        dtcl = [0x08] #  0=IST7232, 8=IST7236
        DisplayDriver._sendIndexData(0x01, dtcl, 1) # DCTL 0x10 of MTP

        # Send image data
        data1 = [0x00, 0x1f, 0x50, 0x00, 0x1f, 0x03] # DUW
        DisplayDriver._sendIndexData(0x13, data1, 6) # DUW
        data2 = [0x00, 0x1f, 0x00, 0xc9] # DRFW
        DisplayDriver._sendIndexData(0x90, data2, 4) # DRFW
        data3 = [0x1f, 0x50, 0x14] # RAM_RW
        DisplayDriver._sendIndexData(0x12, data3, 3) # RAM_RW

        # send first frame
        DisplayDriver._sendIndexData(0x10, data1s, 23040) # First frame

        data33 = [0x1f, 0x50, 0x14] # RAM_RW
        DisplayDriver._sendIndexData(0x12, data33, 3) # RAM_RW

        # send second frame
        DisplayDriver._sendIndexData(0x11, data2s, 23040) # Second frame
        
        DisplayDriver._DCDC_softStart_Mid(0)# the param here and below are the only diff
        DisplayDriver.sendLUT(0)
        DisplayDriver._displayRefresh()
        DisplayDriver._DCDC_softShutdown_Mid()

    def sendLUT(mode: int):
        '''mode can be `0` for global update, `1` for fast global update.'''
        IndexB1_data = [0x00]
        DisplayDriver._sendIndexData(0xB1, IndexB1_data, 1)

        if (mode == 1):
            DisplayDriver._sendIndexData(0xB0, globalLUT, 400)
        elif (mode == 0):
            DisplayDriver._sendIndexData(0xB0, fastLUT, 400)

    def _sendIndexData(index: int, data: list[int], size: int):
        DisplayDriver.ext3Board.panelDC.off()
        DisplayDriver.ext3Board.panelCS.off()
        time.sleep(0.00005)
        spi.writebytes2([index]) # SPI.transfer(index)
        time.sleep(0.00005)
        DisplayDriver.ext3Board.panelCS.on()
        DisplayDriver.ext3Board.panelDC.on()
        DisplayDriver.ext3Board.panelCS.off()
        time.sleep(0.00005)
        spi.writebytes2(data[:size])
        time.sleep(0.00005)
        DisplayDriver.ext3Board.panelCS.on()

    # EPD Screen refresh function
    def _displayRefresh():
        while DisplayDriver.ext3Board.panelBusy.is_active == False:
            time.sleep(0.1)
        DisplayDriver._sendIndexData(0x15, [0x3c], 1) # Display Refresh
        time.sleep(0.005)

    # CoG driver power-on hard reset
    def _reset():
        time.sleep(0.2)
        DisplayDriver.ext3Board.panelReset.on()
        time.sleep(0.02)
        DisplayDriver.ext3Board.panelReset.off()
        time.sleep(0.2)
        DisplayDriver.ext3Board.panelReset.on()
        time.sleep(0.05)
        DisplayDriver.ext3Board.panelCS.on() # CS# = 1 -- not in the manual
        time.sleep(0.005)

    # DC-DC soft-start command
    # Implemented after image data are uploaded to CoG
    # mode: 0: fast, 1: global
    def _DCDC_softStart_Mid(mode: int):
        # Initialize COG Driver
        data4 = [0x7d]
        DisplayDriver._sendIndexData(0x05, data4, 1)
        time.sleep(0.2)
        data5 = [0x00]
        DisplayDriver._sendIndexData(0x05, data5, 1)
        time.sleep(0.01)
        data7 = [0x00]
        DisplayDriver._sendIndexData(0xd8, data7, 1) # MS_SYNC mtp_0x1d
        data8 = [0x00]
        DisplayDriver._sendIndexData(0xd6, data8, 1) # BVSS mtp_0x1e
        data9 = [0x10]
        DisplayDriver._sendIndexData(0xa7, data9, 1)
        time.sleep(0.1)
        DisplayDriver._sendIndexData(0xa7, data5, 1)
        time.sleep(0.1)
        DisplayDriver._sendIndexData(0x44, data5, 1)
        data11 = [0x80]
        DisplayDriver._sendIndexData(0x45, data11, 1)
        DisplayDriver._sendIndexData(0xa7, data9, 1)
        time.sleep(0.1)
        DisplayDriver._sendIndexData(0xa7, data7, 1)
        time.sleep(0.1)
        data12 = [0x06]
        DisplayDriver._sendIndexData(0x44, data12, 1)
        data13 = [0x82]
        DisplayDriver._sendIndexData(0x45, data13, 1) # Temperature 0x82@25C
        DisplayDriver._sendIndexData(0xa7, data9, 1)
        time.sleep(0.1)
        DisplayDriver._sendIndexData(0xa7, data7, 1)
        time.sleep(0.1)
        data14 = [0x25]
        DisplayDriver._sendIndexData(0x60, data14, 1) # TCON mtp_0x0b
        data15 = [0x00] # STV_DIR
        DisplayDriver._sendIndexData(0x61, data15, 1) # STV_DIR mtp_0x1c
        data16 = [0x00]
        DisplayDriver._sendIndexData(0x01, data16, 1) # DCTL mtp_0x10
        data17 = [0x00]
        DisplayDriver._sendIndexData(0x02, data17, 1) # VCOM mtp_0x11
        
        IndexB2_fastUpdate = [0xe0, 0x2a, 0x39, 0x00, 0x39, 0x10, 0x10, 0x10]
        IndexB2_globalUpdate = [0xe0, 0x2d, 0x34, 0x00, 0x34, 0x30, 0x10, 0x10]
        if (mode == 1): # global
            DisplayDriver._sendIndexData(0xb2, IndexB2_globalUpdate, 8)
        elif (mode == 0): # fast
            DisplayDriver._sendIndexData(0xb2, IndexB2_fastUpdate, 8)

        # DC-DC soft start
        index51 = [0x50, 0x01, 0x0a, 0x01]
        DisplayDriver._sendIndexData(0x51, index51, 2)
        index09 = [0x1f, 0x9f, 0x7f, 0xff]

        for value in range(1, 5): # 1,2,3,4
            DisplayDriver._sendIndexData(0x09, index09, 1)
            index51[1] = value
            DisplayDriver._sendIndexData(0x51, index51, 2)
            DisplayDriver._sendIndexData(0x09, index09[1:], 1)
            time.sleep(0.002)
        for value in range(1, 11):
            DisplayDriver._sendIndexData(0x09, index09, 1)
            index51[3] = value
            DisplayDriver._sendIndexData(0x51, index51[2:], 2)
            DisplayDriver._sendIndexData(0x09, index09[1:], 1)
            time.sleep(0.002)
        for value in range(3, 11):
            DisplayDriver._sendIndexData(0x09, index09[2:], 1)
            index51[3] = value
            DisplayDriver._sendIndexData(0x51, index51[2:], 2)
            DisplayDriver._sendIndexData(0x09, index09[3:], 1)
            time.sleep(0.002)
        for value in range(9, 1, -1): # 9,8,7,...2
            DisplayDriver._sendIndexData(0x09, index09[2:], 1)
            index51[2] = value
            DisplayDriver._sendIndexData(0x51, index51[2:], 2)
            DisplayDriver._sendIndexData(0x09, index09[3:], 1)
            time.sleep(0.002)
        DisplayDriver._sendIndexData(0x09, index09[3:], 1)
        time.sleep(0.01)

    # DC-DC soft-shutdown command
    # Implemented after image data are uploaded to CoG
    def _DCDC_softShutdown_Mid():
        while DisplayDriver.ext3Board.panelBusy.is_active == False:
            time.sleep(0.1)
        data19 = [0x7f]
        DisplayDriver._sendIndexData(0x09, data19, 1)
        data20 = [0x7d]
        DisplayDriver._sendIndexData(0x05, data20, 1)
        data55 = [0x00]
        DisplayDriver._sendIndexData(0x09, data55, 1)
        time.sleep(0.2)
        while DisplayDriver.ext3Board.panelBusy.is_active == False:
            time.sleep(0.1)
        DisplayDriver.ext3Board.panelDC.off()
        DisplayDriver.ext3Board.panelCS.off()
        DisplayDriver.ext3Board.panelReset.off()
        DisplayDriver.ext3Board.panelCS.on()