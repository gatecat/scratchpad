from ..fabric.tiletype import *
from ..fabric.bel import *
from ..fabric.fabric import *
from itertools import product

class LogicCell(Bel):
    def __init__(self, name, prefix, tech):
        super().__init__(name, "LogicCell", prefix)
        for port in ("A", "B", "C", "D", "gclocki", "O"):
            setattr(self, port, Signal())

        self.tech = tech
        self._k = 4
        self._lut_init = self.cfg_word("INIT", 2**k)
        self._ff_used = self.cfg_bit("FF")

    def elaborate(self, platform):
        m = Module()
        lut_out = Signal()
        self.split_mux(m=m,
            inputs=[self._lut_init[i] for i in range(2**k)],
            sel=Cat(self.A, self.B, self.C, self.D),
            y=lut_out,
            name="lut_mux",
        )
        ff_out = Signal()
        self.add_dff(d=lut_out, clk=ClockSignal(), q=ff_out, name="ff_i")
        self.add_mux(m=m, inputs=[lut_out, ff_out], sel=[self._ff_used, ], y=self.O, name="ff_sel")
        return m

    def get_ports(self):
        return [
            PortSpec(name="A", dir=PortDir.IN),
            PortSpec(name="B", dir=PortDir.IN),
            PortSpec(name="C", dir=PortDir.IN),
            PortSpec(name="D", dir=PortDir.IN),
            PortSpec(name="O", dir=PortDir.OUT),
        ]

if __name__ == '__main__':
    import sys
    from amaranth.back import verilog
    from .switch_matrix import *
    from ..tech.base import BaseTech

    tech = BaseTech()
    cfg = FabricConfig(tech)
    class LogicTile(Tile):
        def __init__(self, cfg):
            ports = base_ports()
            matrix = base_switch_matrix(
                inputs=list(product(f"L{l}_{i}" for l, i in product(list("ABCDEFGH"), list("ABCD")))),
                outputs=[f"L{l}_O" for l in list("ABCDEFGH")],
            )
            bels = [
                LogicCell(f"L{n}", f"L{n}_", cfg.tech) for n in "ABCDEFGH"
            ]
            super().__init__(name="LogicTile", fcfg=cfg, ports=ports, bels=bels, switch_matrix=switch_matrix)

        def elaborate(self, platform):
            super().elaborate(platform)
    tile = LogicTile(cfg)
    tile_ports = [x[1] for x in t.toplevel_ports()]
    with open(sys.argv[1], "w") as f:
        f.write(verilog.convert(tile, ports=tile_ports))
