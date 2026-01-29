# Minimal MFRC522 (RC522) driver for MicroPython (ESP32)
# Reads UID (anticollision) over SPI

import time

class MFRC522:
    OK       = 0
    NOTAGERR = 1
    ERR      = 2

    # MFRC522 registers
    CommandReg       = 0x01
    ComIEnReg        = 0x02
    ComIrqReg        = 0x04
    ErrorReg         = 0x06
    Status1Reg       = 0x07
    FIFODataReg      = 0x09
    FIFOLevelReg     = 0x0A
    ControlReg       = 0x0C
    BitFramingReg    = 0x0D
    ModeReg          = 0x11
    TxASKReg         = 0x15
    TxControlReg     = 0x14
    TModeReg         = 0x2A
    TPrescalerReg    = 0x2B
    TReloadRegH      = 0x2C
    TReloadRegL      = 0x2D
    CRCResultRegM    = 0x21
    CRCResultRegL    = 0x22

    # MFRC522 commands
    PCD_IDLE         = 0x00
    PCD_CALCCRC      = 0x03
    PCD_TRANSCEIVE   = 0x0C
    PCD_SOFTRESET    = 0x0F

    # PICC commands
    PICC_REQIDL      = 0x26
    PICC_ANTICOLL    = 0x93

    def __init__(self, spi, cs, rst=None):
        self.spi = spi
        self.cs = cs
        self.rst = rst
        self.cs.value(1)

        if self.rst is not None:
            self.rst.value(0)
            time.sleep_ms(10)
            self.rst.value(1)
            time.sleep_ms(10)

        self._wreg(self.CommandReg, self.PCD_SOFTRESET)
        time.sleep_ms(50)
        self.init()

    def _wreg(self, reg, val):
        # SPI address format: 0XXXXXX0 for write
        addr = ((reg << 1) & 0x7E)
        self.cs.value(0)
        self.spi.write(bytes([addr, val & 0xFF]))
        self.cs.value(1)

    def _rreg(self, reg):
        # SPI address format: 1XXXXXX0 for read
        addr = ((reg << 1) & 0x7E) | 0x80
        self.cs.value(0)
        buf = bytearray(2)
        self.spi.write_readinto(bytes([addr, 0x00]), buf)
        self.cs.value(1)
        return buf[1]

    def _set_bit_mask(self, reg, mask):
        self._wreg(reg, self._rreg(reg) | mask)

    def _clear_bit_mask(self, reg, mask):
        self._wreg(reg, self._rreg(reg) & (~mask & 0xFF))

    def antenna_on(self):
        if (self._rreg(self.TxControlReg) & 0x03) != 0x03:
            self._set_bit_mask(self.TxControlReg, 0x03)

    def init(self):
        # Recommended init sequence
        self._wreg(self.TModeReg, 0x8D)
        self._wreg(self.TPrescalerReg, 0x3E)
        self._wreg(self.TReloadRegL, 30)
        self._wreg(self.TReloadRegH, 0)
        self._wreg(self.TxASKReg, 0x40)
        self._wreg(self.ModeReg, 0x3D)
        self.antenna_on()

    def _calculate_crc(self, data):
        self._clear_bit_mask(self.DivIrqReg if hasattr(self, "DivIrqReg") else 0x05, 0x04)
        self._set_bit_mask(self.FIFOLevelReg, 0x80)
        for d in data:
            self._wreg(self.FIFODataReg, d)
        self._wreg(self.CommandReg, self.PCD_CALCCRC)

        i = 255
        while True:
            n = self._rreg(0x05)  # DivIrqReg
            i -= 1
            if (n & 0x04) or i == 0:
                break
        return [self._rreg(self.CRCResultRegL), self._rreg(self.CRCResultRegM)]

    def to_card(self, command, send_data):
        back_data = []
        back_len = 0
        status = self.ERR

        irq_en = 0x77
        wait_irq = 0x30

        self._wreg(self.ComIEnReg, irq_en | 0x80)
        self._clear_bit_mask(self.ComIrqReg, 0x80)
        self._set_bit_mask(self.FIFOLevelReg, 0x80)
        self._wreg(self.CommandReg, self.PCD_IDLE)

        for d in send_data:
            self._wreg(self.FIFODataReg, d)

        self._wreg(self.CommandReg, command)
        if command == self.PCD_TRANSCEIVE:
            self._set_bit_mask(self.BitFramingReg, 0x80)

        i = 2000
        while True:
            n = self._rreg(self.ComIrqReg)
            i -= 1
            if (n & wait_irq) or (n & 0x01) or i == 0:
                break

        self._clear_bit_mask(self.BitFramingReg, 0x80)

        if i != 0:
            err = self._rreg(self.ErrorReg)
            if (err & 0x1B) == 0x00:
                status = self.OK
                if n & 0x01:
                    status = self.NOTAGERR

                if command == self.PCD_TRANSCEIVE:
                    fifo_level = self._rreg(self.FIFOLevelReg)
                    last_bits = self._rreg(self.ControlReg) & 0x07
                    if last_bits != 0:
                        back_len = (fifo_level - 1) * 8 + last_bits
                    else:
                        back_len = fifo_level * 8

                    if fifo_level == 0:
                        fifo_level = 1
                    if fifo_level > 16:
                        fifo_level = 16

                    for _ in range(fifo_level):
                        back_data.append(self._rreg(self.FIFODataReg))
            else:
                status = self.ERR

        return status, back_data, back_len

    def request(self, req_mode):
        self._wreg(self.BitFramingReg, 0x07)
        status, back_data, back_bits = self.to_card(self.PCD_TRANSCEIVE, [req_mode])
        if (status != self.OK) or (back_bits != 0x10):
            return self.ERR, None
        return self.OK, back_data

    def anticoll(self):
        self._wreg(self.BitFramingReg, 0x00)
        status, back_data, back_bits = self.to_card(self.PCD_TRANSCEIVE, [self.PICC_ANTICOLL, 0x20])

        if status != self.OK or len(back_data) != 5:
            return self.ERR, None

        # BCC check
        bcc = 0
        for i in range(4):
            bcc ^= back_data[i]
        if bcc != back_data[4]:
            return self.ERR, None

        return self.OK, back_data[:4]


