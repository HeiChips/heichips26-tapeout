// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

`default_nettype none

module tt_project (
    input  wire       clk1,
    input  wire       rst,
    input  wire       ena,
    
    input  wire [7:0] ui,       // Dedicated inputs
    output wire [7:0] uo,       // Dedicated outputs
    inout  wire [7:0] uio,      // IOs
);

    wire clk1_buf, rst_n_buf;

    GBUF clock_buf (
      .IN   (clk1),
      .OUT  (clk1_buf)
    );

    GBUF #(
      .INVERT (1'b1)
    ) reset_n_buf (
      .IN   (rst),
      .OUT  (rst_n_buf)
    );

    wire [7:0] ui_in;
    wire [7:0] uo_out;
    wire [7:0] uio_in;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;

    TT_PROJECT_wrapper TT_PROJECT_wrapper (
        .UI_IN    (ui_in),
        .UO_OUT   (uo_out),
        .UIO_IN   (uio_in),
        .UIO_OUT  (uio_out),
        .UIO_OE   (uio_oe),
        .ENA      (ena),
        .CLK      (clk1_buf),
        .RST_N    (rst_n_buf)
    );

    assign ui_in = ui;
    assign uo = uo_out;
    assign uio_in = uio;
    assign uio = uio_oe ? uio_out : 8'bz;

endmodule

module TT_PROJECT_wrapper (
    input  wire [7:0] UI_IN,
    output wire [7:0] UO_OUT,
    input  wire [7:0] UIO_IN,
    output wire [7:0] UIO_OUT,
    output wire [7:0] UIO_OE,
    input  wire       ENA,
    input  wire       CLK,
    input  wire       RST_N
);

    TT_PROJECT i_TT_PROJECT (
        .UI_IN0    (UI_IN[0]),
        .UI_IN1    (UI_IN[1]),
        .UI_IN2    (UI_IN[2]),
        .UI_IN3    (UI_IN[3]),
        .UI_IN4    (UI_IN[4]),
        .UI_IN5    (UI_IN[5]),
        .UI_IN6    (UI_IN[6]),
        .UI_IN7    (UI_IN[7]),

        .UO_OUT0    (UO_OUT[0]),
        .UO_OUT1    (UO_OUT[1]),
        .UO_OUT2    (UO_OUT[2]),
        .UO_OUT3    (UO_OUT[3]),
        .UO_OUT4    (UO_OUT[4]),
        .UO_OUT5    (UO_OUT[5]),
        .UO_OUT6    (UO_OUT[6]),
        .UO_OUT7    (UO_OUT[7]),

        .UIO_IN0    (UIO_IN[0]),
        .UIO_IN1    (UIO_IN[1]),
        .UIO_IN2    (UIO_IN[2]),
        .UIO_IN3    (UIO_IN[3]),
        .UIO_IN4    (UIO_IN[4]),
        .UIO_IN5    (UIO_IN[5]),
        .UIO_IN6    (UIO_IN[6]),
        .UIO_IN7    (UIO_IN[7]),

        .UIO_OUT0    (UIO_OUT[0]),
        .UIO_OUT1    (UIO_OUT[1]),
        .UIO_OUT2    (UIO_OUT[2]),
        .UIO_OUT3    (UIO_OUT[3]),
        .UIO_OUT4    (UIO_OUT[4]),
        .UIO_OUT5    (UIO_OUT[5]),
        .UIO_OUT6    (UIO_OUT[6]),
        .UIO_OUT7    (UIO_OUT[7]),
        
        .UIO_OE0    (UIO_OE[0]),
        .UIO_OE1    (UIO_OE[1]),
        .UIO_OE2    (UIO_OE[2]),
        .UIO_OE3    (UIO_OE[3]),
        .UIO_OE4    (UIO_OE[4]),
        .UIO_OE5    (UIO_OE[5]),
        .UIO_OE6    (UIO_OE[6]),
        .UIO_OE7    (UIO_OE[7]),
        
        .ENA    (ENA),
        .CLK    (CLK),
        .RST_N  (RST_N)
    );

endmodule
