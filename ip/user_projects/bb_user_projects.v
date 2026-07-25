module heichips26_example_small (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
    assign uo_out = '0;
    assign uio_out = '0;
    assign uio_oe = '0;
endmodule

module heichips26_example_large (
    input  wire [15:0] ui_in,    // Dedicated inputs
    output wire [15:0] uo_out,   // Dedicated outputs
    input  wire [15:0] uio_in,   // IOs: Input path
    output wire [15:0] uio_out,  // IOs: Output path
    output wire [15:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
    assign uo_out = '0;
    assign uio_out = '0;
    assign uio_oe = '0;
endmodule

module heichips26_example_tiny (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
    assign uo_out = '0;
    assign uio_out = '0;
    assign uio_oe = '0;
endmodule
