set LUT_K 4
set FAB_ROOT $::env(HOME)/FABulous/nextpnr/fabulous/synth
set THIS_ROOT [file dirname [file normalize $argv0]]

yosys read_verilog -lib ${FAB_ROOT}/prims.v
yosys hierarchy -check -top top
yosys proc
#yosys flatten
yosys tribuf -logic
yosys deminout

yosys opt_expr
yosys opt_clean
yosys check
yosys opt -nodffe -nosdff
yosys fsm
yosys opt
yosys wreduce
yosys peepopt
yosys opt_clean
yosys share
yosys opt_expr
yosys opt_clean
yosys techmap -map ${THIS_ROOT}/mul_map.v
yosys alumacc
yosys memory_map
yosys opt -full
yosys techmap -map +/techmap.v
yosys opt -fast
yosys dfflegalize -cell \$_DFF_P_ 0 -cell \$_DLATCH_?_ x
yosys techmap -map ${FAB_ROOT}/latches_map.v
yosys abc -lut $LUT_K -dress
yosys clean
yosys techmap -D LUT_K=$LUT_K -map ${FAB_ROOT}/cells_map.v
yosys clean
yosys hierarchy -check
yosys stat
