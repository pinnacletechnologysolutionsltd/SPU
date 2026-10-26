# nextpnr pre-pack script; refuse missing clock-net names.
for clock_net, mhz in (("sys_clk", 50), ("clk_25", 25)):
    assert clock_net in ctx.nets, "Missing benchmark clock " + clock_net
    ctx.addClock(clock_net, mhz)
