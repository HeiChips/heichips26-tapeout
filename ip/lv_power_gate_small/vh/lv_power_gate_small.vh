module lv_power_gate_small (
`ifdef USE_POWER_PINS
  inout VPWR,
  inout VGND,
  inout VPWR_SW,
`endif
  input ena
);
endmodule
