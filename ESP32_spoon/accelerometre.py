# C'était plus facile de faire en français. Désolé pour ce fichier.

import utime # pyright: ignore[reportMissingImports]
import struct
import math
from machine import Pin, I2C # pyright: ignore[reportMissingImports]
import configAcc

# MPU6050 regs
REG_PWR_MGMT_1 = 0x6B
REG_WHO_AM_I   = 0x75
REG_CONFIG     = 0x1A
REG_GYRO_CFG   = 0x1B
REG_ACCEL_CFG  = 0x1C
REG_DATA_START = 0x3B  # accel(6) + temp(2) + gyro(6)

ACC_LSB_PER_G = 16384.0
EPS = 1e-6

def norme(x, y, z):
    return math.sqrt(x*x + y*y + z*z)

def signe(x, dead=0.0):
    if x > dead: return 1
    if x < -dead: return -1
    return 0

def recuperer_bus_i2c():
    scl = Pin(configAcc.I2C_SCL_PIN, Pin.OPEN_DRAIN, value=1)
    sda = Pin(configAcc.I2C_SDA_PIN, Pin.OPEN_DRAIN, value=1)
    utime.sleep_us(50)
    for _ in range(9):
        scl.value(0); utime.sleep_us(10)
        scl.value(1); utime.sleep_us(10)
    sda.value(0); utime.sleep_us(10)
    scl.value(1); utime.sleep_us(10)
    sda.value(1); utime.sleep_us(10)

def creer_i2c():
    scl = Pin(configAcc.I2C_SCL_PIN, Pin.PULL_UP)
    sda = Pin(configAcc.I2C_SDA_PIN, Pin.PULL_UP)
    return I2C(0, scl=scl, sda=sda, freq=configAcc.I2C_FREQ_HZ)

def lire_who_am_i(i2c, addr):
    try:
        return i2c.readfrom_mem(addr, REG_WHO_AM_I, 1)[0]
    except:
        return None

def configurer_mpu(i2c, addr):
    i2c.writeto_mem(addr, REG_PWR_MGMT_1, b"\x00")
    utime.sleep_ms(50)
    i2c.writeto_mem(addr, REG_CONFIG, b"\x03")
    i2c.writeto_mem(addr, REG_GYRO_CFG, b"\x00")
    i2c.writeto_mem(addr, REG_ACCEL_CFG, b"\x00")

def lire_accel_brut(i2c, addr):
    data = i2c.readfrom_mem(addr, REG_DATA_START, 14)
    ax, ay, az, _t, _gx, _gy, _gz = struct.unpack(">hhhhhhh", data)
    return ax, ay, az

class DetecteurTouillage:

    def __init__(self):
        self.i2c = None
        self.addr = None

        self.grav_x = 0.0
        self.grav_y = 0.0
        self.grav_z = 0.0

        self.lat_fx = 0.0
        self.lat_fy = 0.0
        self.lat_fz = 0.0

        self.prev_lat_x = 0.0
        self.prev_lat_y = 0.0
        self.prev_lat_z = 0.0
        self.has_prev = False

        self.geste_actif = False
        self.dernier_ok_ms = 0

        self.angle_deg = 0.0
        self.direction_live = 0
        self.nb_tours = 0

        self.energie_laterale = 0.0

    def demarrer(self):
        recuperer_bus_i2c()
        self.i2c = creer_i2c()

        if configAcc.PRINT_I2C_SCAN:
            try:
                print("I2C scan:", self.i2c.scan())
            except:
                print("I2C scan: []")

        for a in configAcc.MPU_CANDIDATES:
            who = lire_who_am_i(self.i2c, a)
            if who == 0x68:
                self.addr = a
                break
        if self.addr is None:
            raise RuntimeError("MPU6050 NOT FOUND")

        print("MPU addr:", hex(self.addr), "WHO_AM_I:", hex(self.i2c.readfrom_mem(self.addr, REG_WHO_AM_I, 1)[0]))
        configurer_mpu(self.i2c, self.addr)

        # calibration gravité (immobile)
        sx = sy = sz = 0.0
        n = 0
        t0 = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), t0) < 800:
            axr, ayr, azr = lire_accel_brut(self.i2c, self.addr)
            sx += axr / ACC_LSB_PER_G
            sy += ayr / ACC_LSB_PER_G
            sz += azr / ACC_LSB_PER_G
            n += 1
            utime.sleep_ms(5)

        self.grav_x = sx / n
        self.grav_y = sy / n
        self.grav_z = sz / n

        self.reset_geste()

    def reset_geste(self):
        self.geste_actif = False
        self.has_prev = False
        self.direction_live = 0
        self.angle_deg = 0.0
        self.energie_laterale = 0.0

    def update(self):
        event = 0
        event_dir = 0

        try:
            axr, ayr, azr = lire_accel_brut(self.i2c, self.addr)
        except:
            recuperer_bus_i2c()
            self.i2c = creer_i2c()
            utime.sleep_ms(50)
            configurer_mpu(self.i2c, self.addr)
            return {
                "active": 0, "dir": 0, "event": 0, "event_dir": 0,
                "lateral_g": 0.0, "angle_deg": 0.0, "energy": 0.0, "count": self.nb_tours
            }

        acc_x = axr / ACC_LSB_PER_G
        acc_y = ayr / ACC_LSB_PER_G
        acc_z = azr / ACC_LSB_PER_G

        # gravité low-pass
        a = configAcc.GRAVITY_ALPHA
        self.grav_x = (1.0 - a) * self.grav_x + a * acc_x
        self.grav_y = (1.0 - a) * self.grav_y + a * acc_y
        self.grav_z = (1.0 - a) * self.grav_z + a * acc_z

        gmag = norme(self.grav_x, self.grav_y, self.grav_z) + EPS
        ghat_x = self.grav_x / gmag
        ghat_y = self.grav_y / gmag
        ghat_z = self.grav_z / gmag

        # lin = accel - gravité
        lin_x = acc_x - self.grav_x
        lin_y = acc_y - self.grav_y
        lin_z = acc_z - self.grav_z

        # latéral = projection perp à gravité
        dot = lin_x*ghat_x + lin_y*ghat_y + lin_z*ghat_z
        lat_x = lin_x - dot*ghat_x
        lat_y = lin_y - dot*ghat_y
        lat_z = lin_z - dot*ghat_z

        # filtre latéral
        la = configAcc.LATERAL_ALPHA
        self.lat_fx = (1.0 - la) * self.lat_fx + la * lat_x
        self.lat_fy = (1.0 - la) * self.lat_fy + la * lat_y
        self.lat_fz = (1.0 - la) * self.lat_fz + la * lat_z

        lateral_g = norme(self.lat_fx, self.lat_fy, self.lat_fz)
        now_ms = utime.ticks_ms()

        gate_on  = lateral_g >= configAcc.LATERAL_START_G
        gate_off = lateral_g <= configAcc.LATERAL_STOP_G

        if not self.geste_actif:
            if gate_on:
                self.geste_actif = True
                self.angle_deg = 0.0
                self.energie_laterale = 0.0
                self.has_prev = False
                self.dernier_ok_ms = now_ms
        else:
            if gate_on:
                self.dernier_ok_ms = now_ms
            else:
                if gate_off and utime.ticks_diff(now_ms, self.dernier_ok_ms) > configAcc.MAX_PAUSE_MS:
                    self.reset_geste()

        # énergie (amplitude)
        if self.geste_actif and lateral_g >= configAcc.LATERAL_MIN_FOR_ANGLE_G:
            self.energie_laterale += lateral_g

        # cumul angle + sens
        if self.geste_actif and lateral_g >= configAcc.LATERAL_MIN_FOR_ANGLE_G:
            if self.has_prev:
                prev_norm = norme(self.prev_lat_x, self.prev_lat_y, self.prev_lat_z)
                if prev_norm >= configAcc.LATERAL_MIN_FOR_ANGLE_G:
                    cx = self.prev_lat_y*self.lat_fz - self.prev_lat_z*self.lat_fy
                    cy = self.prev_lat_z*self.lat_fx - self.prev_lat_x*self.lat_fz
                    cz = self.prev_lat_x*self.lat_fy - self.prev_lat_y*self.lat_fx

                    dotp = self.prev_lat_x*self.lat_fx + self.prev_lat_y*self.lat_fy + self.prev_lat_z*self.lat_fz
                    cross_mag = norme(cx, cy, cz)

                    dtheta_deg = math.atan2(cross_mag, dotp + EPS) * 57.2957795
                    spin = cx*ghat_x + cy*ghat_y + cz*ghat_z

                    step_dir = signe(spin, 1e-8) * configAcc.DROITE_GAUCHE_SIGN
                    if step_dir != 0:
                        self.angle_deg += step_dir * dtheta_deg
                        self.direction_live = step_dir
                    else:
                        self.direction_live = 0

            self.prev_lat_x, self.prev_lat_y, self.prev_lat_z = self.lat_fx, self.lat_fy, self.lat_fz
            self.has_prev = True
        else:
            self.direction_live = 0

        # validation: angle + amplitude
        if self.geste_actif and abs(self.angle_deg) >= configAcc.TOUR_SEUIL_DEG:
            if self.energie_laterale >= configAcc.ENERGIE_LATERALE_MIN:
                self.nb_tours += 1
                event = 1
                event_dir = 1 if self.angle_deg > 0 else -1
            self.reset_geste()

        return {
            "active": 1 if self.geste_actif else 0,
            "dir": self.direction_live,
            "event": event,
            "event_dir": event_dir,
            "lateral_g": lateral_g,
            "angle_deg": self.angle_deg,
            "energy": self.energie_laterale,
            "count": self.nb_tours,
        }
