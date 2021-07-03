#!/usr/bin/env python3

# A Python Timonel driver
#
# Rob Burbidge
# prandeamus@btinternet.com
# https://www.github.com/prandeamus/timonel-py
#
# Based on timonel bootloader at https://www.github.com/casanovg/timonel and related repositories.
#

import smbus2
import ctypes
import time




class TimonelStatus(ctypes.LittleEndianStructure):
        """ Timonel Status code returned by GETTMLV """
        _pack_ = 1 # Byte packing
        _fields_ = [
                ("signature",          ctypes.c_uint8),     # Bootloader signature
                ("version_major",      ctypes.c_uint8),     # Bootloader major version number
                ("version_minor",      ctypes.c_uint8),     # Bootloader minor version number
                # Bit fields for features_code, MSB first
                ("cmd_readflash",      ctypes.c_uint8, 1),  # Features 8 (128): Read flash command enabled
                ("app_autorun",        ctypes.c_uint8, 1),  # Features 7 (64) : If not initialized, exit to app after timeout
                ("use_wdt_reset",      ctypes.c_uint8, 1),  # Features 6 (32) : Reset by watchdog timer enabled
                ("two_step_init",      ctypes.c_uint8, 1),  # Features 5 (16) : Two-step initialization required
                ("cmd_setpgaddr",      ctypes.c_uint8, 1),  # Features 4 (8)  : Set page address command enabled
                ("app_use_tpl_pg",     ctypes.c_uint8, 1),  # Features 3 (4)  : Application can use trampoline page
                ("auto_page_addr",     ctypes.c_uint8, 1),  # Features 2 (2)  : Automatic trampoline and addr handling
                ("enable_led_ui",      ctypes.c_uint8, 1),  # Features 1 (1)  : LED UI enabled
                # Bit fields for ext_features_code, MSB First
                ("_padbits_",          ctypes.c_uint8, 2),  # Extended features bit 6 and 7 not used.
                ("eeprom_access",      ctypes.c_uint8, 1),  # Ext features 6 (32) : Reading and writing the device EEPROM enabled
                ("cmd_readdevs",       ctypes.c_uint8, 1),  # Ext features 5 (16) : Read device signature, fuse and lock bits command enabled
                ("check_page_ix",      ctypes.c_uint8, 1),  # Ext features 4 (8)  : Check that the page index is < SPM_PAGESIZE
                ("clear_bit_7_R31",    ctypes.c_uint8, 1),  # Ext features 3 (4)  : Prevent code first instruction from being skipped
                ("force_erase_page",   ctypes.c_uint8, 1),  # Ext features 2 (2)  : Erase each page before writing new data
                ("auto_clk_tweak",     ctypes.c_uint8, 1),  # Ext features 1 (1)  : Auto clock tweaking by reading low fuse
                #
                ("bootloader_start",   ctypes.c_uint16),    # Bootloader start memory position
                ("application_start",  ctypes.c_uint16),    # Trampoline bytes pointing to application launch, if existing
                ("low_fuse_setting",   ctypes.c_uint8),     # Low fuse bits
                ("oscillator_cal",     ctypes.c_uint8)      # Internal RC oscillator calibration
        ]

        def __repr__(self):
                """ 
                        Printable representation
                """
                return ("TimonelStatus(\n"
                        "Signature:{0:02X},Major:{1:02X},Minor:{2:02X},\n"
                        "Enable LED UI:{3:01b},Auto Page Addr:{4:01b},Use TPL Pg:{5:01b},Set Page Addr:{6:01b},Two Step Init:{7:01b},WDT reset:{8:01b},App Autorun:{9:01b},Read Flash:{10:01b}\n"
                        "Auto clk Tweak:{11:01b},Force Erase Page:{12:01b}, Clear Bit 7 (R31):{13:01b}, Check Page IX:{14:01b}, ReadDevs:{15:01b}, Eeprom:{16:01b}\n"
                        "Bootloader:{17:04X},Appliication:{18:04X},LFuse:{19:02X},Osccal:{20:02X}" 
                        ")").format(
                        self.signature,        self.version_major,    self.version_minor, 
                        # Features
                        self.enable_led_ui,    self.auto_page_addr,   self.app_use_tpl_pg, self.cmd_setpgaddr, 
                        self.two_step_init,    self.use_wdt_reset,    self.app_autorun,    self.cmd_readflash,
                        # Extended features
                        self.auto_clk_tweak,   self.force_erase_page, self.clear_bit_7_R31, self.check_page_ix, 
                        self.cmd_readdevs,     self.eeprom_access,
                        self.bootloader_start, self.application_start, 
                        self.low_fuse_setting, self.oscillator_cal
                )

class TimonelDeviceSettings(ctypes.LittleEndianStructure):
        """ 
                Timonel device settings 
        """
        _pack_ = 1 # Byte packing
        _fields_ = [
                ("low_fuse_bits",      ctypes.c_uint8), # Low fuse bits
                ("high_fuse_bits",     ctypes.c_uint8), # High fuse bits
                ("extended_fuse_bits", ctypes.c_uint8), # Extended fuse bits
                ("lock_bits",          ctypes.c_uint8), # Device lock bits
                ("signature_byte_0",   ctypes.c_uint8), # Device signature byte 0
                ("signature_byte_1",   ctypes.c_uint8), # Device signature byte 1
                ("signature_byte_2",   ctypes.c_uint8), # Device signature byte 2
                ("calibration_0",      ctypes.c_uint8), # Calibration data for internal oscillator at 8.0 MHz
                ("calibration_1",      ctypes.c_uint8), # Calibration data for internal oscillator at 6.4 MHz
        ]

        def __repr__(self):
                """ 
                        Printable representation 
                """
                return ("TimonelDeviceSettings(\n" 
                        "LFuse:{0:02X}, HFuse:{1:02X}, EFuse:{2:02X}, Lock:{3:02X},\n"
                        "Sig: {4:02X}, {5:02X}, {6:02X}, Cal 8MHz:{7:02X}, Cal 6.4MHz:{7:02X})").format(
                                self.low_fuse_bits,    self.high_fuse_bits,   self.extended_fuse_bits, self.lock_bits,
                                self.signature_byte_0, self.signature_byte_1, self.signature_byte_2,
                                self.calibration_0,    self.calibration_1
                )
 
class Timonel:
        """ 
                Timonel bootloader I2C master
        """
        # Timonel commands always form the first byte. A valid response is the 1-complement
        CMD_NO_OP    = 0x00
        CMD_RESETMCU = 0x80
        CMD_INITSOFT = 0x81
        CMD_GETTMNLV = 0x82
        # TODO some codes omitted until I get round to them
        CMD_EXITTIML = 0x86
        CMD_READFLSH = 0x87
        CMD_READDEVS = 0x88
        CMD_WRITEEPR = 0x89
        CMD_READEEPR = 0x8A

        # ATTiny85 Master and Slave packet size
        # MST_PACKET_SIZE = 32
        # SLV_PACKET_SIZE = 32
        # ATTiny85 page size for self-programming mode
        # SPM_PAGESIZE = 64

        # FillSpecialPages
        # RST_PAGE = 1        # Config: 1=Reset page (addr: 0)
        # TPL_PAGE = 2        # Config: 2=Trampoline page (addr: TIMONEL_START - 64)
        # DLY_SET_ADDR = 100  # Delay after setting a memory address
        # DLY_RETURN = 100    # Delay before return control to caller

        # DumpMemory
        # MCU_TOTAL_MEM = 8192   # Config: Microcontroller flash memory size
        #VALUES_PER_LINE = 32   # Config: Memory positions values to display per line
        # DMP_CMD_LENGTH = 4     # Config: READFLSH command lenght (1 cmd byte + 2 addr bytes + 1 rx size byte + 1 checksum byte)
        # DMP_REPLY_OVRHD = 2    # Config: READFLSH reply overhead: extra bytes added to the reply: 1 ack + 1 checksum
        # MAXCKSUMERRORS = 3     # Config: DumpMemory max count of errors accepted
        # ERR_CODES HERE ARE NOT PYTHONIC.
        # ERR_NOT_SUPP = 1       # Error: function not supported in current setup
        # ERR_CMD_PARSE_D = 2    # Error: reply doesn't match DumpMemory command
        # ERR_ADDR_PARSE = 3     # Error: requested address misinterpreted by Timonel device
        # ERR_CHECKSUM_D = 4     # Error: Too much checksum errors
        # 
        # DLY_1_SECOND = 1000    # 1 second delay
        # DLY_PKT_REQUEST = 150  # Delay between data packet requests

        # SendDataPacket
        # ERR_TX_PKT_CHKSUM = 1  # Error: Received checksum doesn't match transmitted packet

        def __init__(self, bus, addr, verbose=0):
                """ 
                        Initialise Timonel device for a given SMBus and address, with option for trace message verbosity
                """
                self.bus     = bus
                self.addr    = addr
                self.verbose = verbose

        def __enter__(self):
                """
                        Enter context manager ("with" statement)
                """
                return self

        def __exit__(self, type, value, traceback):
                """ 
                        Leave context manager ("with" statement) 
                """
                self.bus = None
                self.addr = None

        def __trace(self, vlevel, msg, *args):
                """ 
                        Trace to stdout, if verbose 
                """
                if self.verbose >= vlevel:
                        print(msg.format(*args))

        def __i2cRaw(self, req, reqBytes, respLength):
                """
                        Execute an I2C write followed by a read.
                        Checks on the content that is read are handled by the caller.
                """
                # Create write and read commands
                w = smbus2.i2c_msg.write(self.addr, [req]+reqBytes)
                r = smbus2.i2c_msg.read(self.addr, respLength)
                # Execute I2C commands
                self.bus.i2c_rdwr(w, r)

                # Return bytes
                return bytes(r)

        def __i2c(self, req, reqBytes=[], respLength=1, attempts=1, retryDelay=0):
                """ 
                        Execute a Timonel command, validate the response.
                        Include retry and logic
                """
                attempt = 1
                while attempt <= attempts:
                        try:
                                response = self.__i2cRaw(req, reqBytes, respLength)

                                # Check the first byte read is 1s complement of command
                                if response[0] != (req ^ 0xFF):
                                        raise Exception("ACK Error")

                                # Check correct number of bytes have been returned
                                if len(response) != respLength:
                                        raise Exception("Response length error")

                                # TODO - Optional checksum logic

                                # Success - return data skipping the first byte
                                return response[1:]
                        except:
                                # If the retry limit has been reached, give up
                                if attempt == attempts:
                                        raise
                                else:
                                        # Try again
                                        self.__trace(1, "Retrying")
                                        # Wait a bit
                                        if retryDelay > 0:
                                                time.sleep(retryDelay)
                                        attempt += 1

        @staticmethod
        def __checksum(data1,data2=[]):
                """ 
                        Compute simple byte checksum of iterable set of bytes, optionally followed by a second set.
                        The second set is useful when the two bytes of an address are included in the checksum
                """
                c = 0
                for b in data1:
                        c = (c + b) & 0xFF
                for b in data2:
                        c = (c + b) & 0xFF
                return c

        def NoOp(self):
                """ 
                        Ping the device
                """
                self.__trace(1, "NoOp")
                self.__i2c(self.CMD_NO_OP)

        def ResetMicrocontroller(self):
                """
                        Reset MCU
                """
                self.__trace(1, "ResetMicrocontroller")
                self.__i2c(self.CMD_RESETMCU)

        def InitMicro(self):
                """
                        Initialize firmware
                """
                self.__trace(1, "InitMicro")
                self.__i2c(self.CMD_INITSOFT)

        def GetStatus(self):
                """ 
                        Get Status 
                        Note we don't store the TimonelStatus inside the class. That may change.
                """
                self.__trace(1, "GetStatus")
                r = self.__i2c(self.CMD_GETTMNLV, respLength=12)                
                return TimonelStatus.from_buffer_copy(r)

        # TODO DELETE FLASH
        # TODO SET FLASH BASE PAGE ADDRESS
        # TODO WRITE DATA TO PAGE BUFFER
        # TODO any other command I've not tried to implement yet
        
        def ExitTimonel(self):
                """ 
                        Exit Timonel (jump to app) 
                """
                self.__trace(1, "ExitTimonel")
                self.__i2c(self.CMD_EXITTIML)

        def ReadFlash(self, startAddress, length):
                """ 
                        Read data from flash memory 
                """
                self.__trace(1, "ReadFlash {0:04X}:{1:02X}".format(startAddress, length))
                if startAddress < 0:
                        raise Exception("ReadFlash: Bad start address")
                # TODO - 255 below is optimistic. Needs adjustment to known limit (64 bytes)
                if length < 0 or length > 255:
                        raise Exception("ReadFlash: Bad length")
                
                # 4 bytes in: Command, high byte of address, low byteof adddress, length
                # Response is ack code + data + checksum
                r = self.__i2c(self.CMD_READFLSH, [startAddress>>8, startAddress & 0xFF, length], 2+length)
                byts = r[0:-1]
                chk  = r[-1]
                # The data AND the two address bytes should be included in checksum
                if self.__checksum(byts,[startAddress>>8,startAddress & 0xFF]) != chk:
                        print(r)
                        raise Exception("Readflash: Checksum error")
                return byts

        def ReadDeviceSignatureAndFuses(self):
                """ 
                        Read signature and fuses
                """
                self.__trace(1, "ReadDeviceSignatureAndFuses")
                r = self.__i2c(self.CMD_READDEVS, respLength=10)                
                return TimonelDeviceSettings.from_buffer_copy(r)

        def WriteByteToEEPROM(self, startAddress, byt):
                """
                        Write byte to EEPROM
                """
                self.__trace(1, "WriteByteToEEPROM")
                r = self.__i2c(self.CMD_WRITEEPR, [startAddress>>8, startAddress & 0xFF, byt], 2)
                chk = r[-1]
                if self.__checksum([byt],[startAddress>>8, startAddress & 0xFF]) != chk:
                        raise Exception("Write EEPROM: Checksum error")

        def ReadByteFromEEPROM(self, startAddress):
                """
                        Read byte to EEPROM
                """
                self.__trace(1, "ReadByteFromEEPROM {0:04X}".format(startAddress))
                r = self.__i2c(self.CMD_READEEPR, [startAddress>>8, startAddress & 0xFF], 3)
                byts = r[0:-1]
                chk = r[-1]
                if self.__checksum(byts,[startAddress>>8,startAddress & 0xFF]) != chk:
                        raise Exception("Read EEPROM Checksum error")
                return byts[0]

### Begin ###

bus = 6     # I2C bus. My PC has /dev/i2c-9. Yours may vary. For Raspberry Pi, try /dev/i2c-1 
addr = 0x0B # I2C address of timonel device on bus

print("No guarantees. If you trash your PC or your device, I'm not liable!")

with smbus2.SMBus(bus) as bus:
        with Timonel(bus, addr, verbose=0) as tim:
                # Initialise
                tim.InitMicro()
                # Get status
                stat = tim.GetStatus()
                print(stat)

                if not(stat.version_major == 1 and stat.version_minor == 5):
                        print("I was expecting version 1.5 of the boot loader. Terminating for now.")
                        quit()

                if stat.cmd_readdevs:
                        devSig = tim.ReadDeviceSignatureAndFuses()
                        print(devSig)
                else:
                        print("The device doesn't support cmd_readdevs")

                if stat.cmd_readflash:
                        v = tim.ReadFlash(0x1B00, 16)
                        print([hex(x) for x in v])
                else:  
                        print("This device doesn't support reading flash")

                if stat.eeprom_access:
                        # Read first EEPROM bytes
                        data = [tim.ReadByteFromEEPROM(i) for i in range(0,16)]
                        print([hex(x) for x in data])
                        # Write some new data to a few EEPROM bytes
                        now = time.gmtime()
                        tim.WriteByteToEEPROM(1, now.tm_hour)
                        tim.WriteByteToEEPROM(2, now.tm_min)
                        tim.WriteByteToEEPROM(3, now.tm_sec)
                else:
                        print("This device doesn't support EEPROM access")
