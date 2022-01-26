from amaranth import *
from amaranth.build import *
from amaranth.lib.cdc import ResetSynchronizer
from amaranth_boards.ulx3s import *
from amaranth_boards.ulx3s import *

from cores.spimemio_wrapper import QSPIPins
from cores.gpio import GPIOPins
from cores.uart import UARTPins
from cores.hyperram import HyperRAMPins

class Ulx3sWrapper(Elaboratable):
    """
    This wrapper provides glue to simplify use of the ULX3S platform, and integrate between
    the Amaranth platform and the format of pins that the IP cores expect.
    """

    def get_flash(self, m, platform):
        plat_flash = platform.request("spi_flash", dir=dict(cs='-', copi='-', cipo='-', wp='-', hold='-'))

        flash = QSPIPins()
        # Flash clock requires a special primitive to access in ECP5
        m.submodules.usrmclk = Instance("USRMCLK",
            i_USRMCLKI=flash.clk_o,
            i_USRMCLKTS=ResetSignal(), # tristate in reset for programmer accesss
            a_keep=1,
        )
        # IO pins and buffers
        m.submodules += Instance("OBZ",
            o_O=plat_flash.cs.io,
            i_I=flash.csn_o,
            i_T=ResetSignal(),
        )
        # Pins in order
        data_pins = ["copi", "cipo", "wp", "hold"]

        for i in range(4):
            m.submodules += Instance("BB",
                io_B=getattr(plat_flash, data_pins[i]).io,
                i_I=flash.d_o[i],
                i_T=~flash.d_oe[i],
                o_O=flash.d_i[i]
            )
        return flash

    def get_led_gpio(self, m, platform):
        leds = GPIOPins(width=8)
        for i in range(8):
            led = platform.request("led", i)
            m.d.comb += led.o.eq(leds.o[i])
        return leds

    def get_uart(self, m, platform):
        plat_uart = platform.request("uart")
        uart = UARTPins()
        m.d.comb += [
            plat_uart.tx.o.eq(uart.tx_o),
            uart.rx_i.eq(plat_uart.rx.i),
        ]
        return uart

    def get_hram(self, m, platform):
        # Dual HyperRAM PMOD, starting at GPIO 14+/-
        platform.add_resources([
            Resource("hyperram", 0,
                Subsignal("csn",    Pins("23- 23+ 24- 24+", conn=("gpio", 0), dir='o')),
                Subsignal("rstn",   Pins("22+", conn=("gpio", 0), dir='o')),
                Subsignal("clk",    Pins("22-", conn=("gpio", 0), dir='o')),
                Subsignal("rwds",   Pins("21+", conn=("gpio", 0), dir='io')),

                Subsignal("dq",     Pins("17- 16- 15- 14- 14+ 15+ 16+ 17+", conn=("gpio", 0), dir='io')),

                Attrs(IO_TYPE="LVCMOS33"),
            )
        ])

        plat_hram = platform.request("hyperram", 0)
        hram = HyperRAMPins(cs_count=4)
        m.d.comb += [
            plat_hram.clk.o.eq(hram.clk_o),
            plat_hram.csn.o.eq(hram.csn_o),
            plat_hram.rstn.o.eq(hram.rstn_o),

            plat_hram.rwds.o.eq(hram.rwds_o),
            plat_hram.rwds.oe.eq(hram.rwds_oe),
            hram.rwds_i.eq(plat_hram.rwds.i),

            plat_hram.dq.o.eq(hram.dq_o),
            plat_hram.dq.oe.eq(hram.dq_oe[0]),
            hram.dq_i.eq(plat_hram.dq.i),
        ]
        return hram

    def elaborate(self, platform):
        clk25 = platform.request("clk25")
        m = Module()
        m.domains.sync = ClockDomain()
        m.d.comb += ClockSignal().eq(clk25.i)
        reset_in = platform.request("button_pwr", 0)
        m.submodules += ResetSynchronizer(reset_in)
        return m
