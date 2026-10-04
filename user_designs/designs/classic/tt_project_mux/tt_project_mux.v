// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

`default_nettype none

module tt_project_mux #(
    parameter NUM_TT_PROJECT = 8,
    parameter NUM_TT_PROJECT_MUX = 2,
    parameter NUM_TT_PROJECT_LARGE = 3
)(
    input  wire       clk1,
    input  wire       rst,
    input  wire       ena,
    
    input  wire [$clog2(NUM_TT_PROJECT + NUM_TT_PROJECT_MUX + NUM_TT_PROJECT_LARGE)-1:0] sel,
    
    input  wire [7:0] ui,       // Dedicated inputs
    output wire [7:0] uo,       // Dedicated outputs
    inout  wire [7:0] uio,      // IOs
);

    wire rst_n_buf;

    GBUF #(
      .INVERT (1'b1)
    ) reset_n_buf (
      .IN   (rst),
      .OUT  (rst_n_buf)
    );
    
    wire [7:0] ui_in;
    wire [7:0] uo_out [NUM_TT_PROJECT];
    wire [7:0] uio_in;
    wire [7:0] uio_out [NUM_TT_PROJECT];
    wire [7:0] uio_oe [NUM_TT_PROJECT];
    
    genvar i;
    generate
    
      for (i=0; i<NUM_TT_PROJECT + NUM_TT_PROJECT_MUX + NUM_TT_PROJECT_LARGE; i++) begin : tt_projects
          if (i < NUM_TT_PROJECT) begin
              TT_PROJECT_wrapper TT_PROJECT_wrapper (
                  .UI_IN    (ui_in),
                  .UO_OUT   (uo_out[i]),
                  .UIO_IN   (uio_in),
                  .UIO_OUT  (uio_out[i]),
                  .UIO_OE   (uio_oe[i]),
                  .ENA      (ena),
                  .CLK      (clk1),
                  .RST_N    (rst_n_buf)
              );
          end else if (i < NUM_TT_PROJECT + NUM_TT_PROJECT_MUX) begin
              TT_PROJECT_MUX_wrapper TT_PROJECT_MUX_wrapper (
                  .UI_IN    (ui_in),
                  .UO_OUT   (uo_out[i]),
                  .UIO_IN   (uio_in),
                  .UIO_OUT  (uio_out[i]),
                  .UIO_OE   (uio_oe[i]),
                  .ENA      (ena),
                  .CLK      (clk1),
                  .RST_N    (rst_n_buf)
              );
          end else begin
              TT_PROJECT_LARGE_wrapper TT_PROJECT_LARGE_wrapper (
                  .UI_IN    ({8'b0, ui_in}),
                  .UO_OUT   (uo_out[i]),
                  .UIO_IN   ({8'b0, uio_in}),
                  .UIO_OUT  (uio_out[i]),
                  .UIO_OE   (uio_oe[i]),
                  .ENA      (ena),
                  .CLK      (clk1),
                  .RST_N    (rst_n_buf)
              );
          end
      end
    
    endgenerate
    
    wire [7:0] uo_out_sel;
    wire [7:0] uio_out_sel;
    wire [7:0] uio_oe_sel;

    assign ui_in = ui;
    assign uo = uo_out[sel];
    assign uio_in = uio;
    assign uio = uio_oe[sel] ? uio_out[sel] : 8'bz;


endmodule

module TT_PROJECT_wrapper #(
    parameter ENABLE_POWER=0
)(
    input  wire [7:0] UI_IN,
    output wire [7:0] UO_OUT,
    input  wire [7:0] UIO_IN,
    output wire [7:0] UIO_OUT,
    output wire [7:0] UIO_OE,
    input  wire       ENA,
    input  wire       CLK,
    input  wire       RST_N
);

    TT_PROJECT #(
        .ENABLE_POWER (ENABLE_POWER)
    ) i_TT_PROJECT (
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

module TT_PROJECT_MUX_wrapper #(
    parameter ENABLE_POWER=0,
    parameter SELECT_SLOT=0
)(
    input  wire [7:0] UI_IN,
    output wire [7:0] UO_OUT,
    input  wire [7:0] UIO_IN,
    output wire [7:0] UIO_OUT,
    output wire [7:0] UIO_OE,
    input  wire       ENA,
    input  wire       CLK,
    input  wire       RST_N
);

    TT_PROJECT_MUX #(
        .ENABLE_POWER (ENABLE_POWER),
        .SELECT_SLOT (SELECT_SLOT)
    ) i_TT_PROJECT_MUX (
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

module TT_PROJECT_LARGE_wrapper #(
    parameter ENABLE_POWER=0
)(
    input  wire [15:0] UI_IN,
    output wire [15:0] UO_OUT,
    input  wire [15:0] UIO_IN,
    output wire [15:0] UIO_OUT,
    output wire [15:0] UIO_OE,
    input  wire        ENA,
    input  wire        CLK,
    input  wire        RST_N
);

    TT_PROJECT_LARGE #(
        .ENABLE_POWER (ENABLE_POWER)
    ) i_TT_PROJECT_LARGE (
        .UI_IN0    (UI_IN[0]),
        .UI_IN1    (UI_IN[1]),
        .UI_IN2    (UI_IN[2]),
        .UI_IN3    (UI_IN[3]),
        .UI_IN4    (UI_IN[4]),
        .UI_IN5    (UI_IN[5]),
        .UI_IN6    (UI_IN[6]),
        .UI_IN7    (UI_IN[7]),
        .UI_IN8    (UI_IN[8]),
        .UI_IN9    (UI_IN[9]),
        .UI_IN10   (UI_IN[10]),
        .UI_IN11   (UI_IN[11]),
        .UI_IN12   (UI_IN[12]),
        .UI_IN13   (UI_IN[13]),
        .UI_IN14   (UI_IN[14]),
        .UI_IN15   (UI_IN[15]),

        .UO_OUT0    (UO_OUT[0]),
        .UO_OUT1    (UO_OUT[1]),
        .UO_OUT2    (UO_OUT[2]),
        .UO_OUT3    (UO_OUT[3]),
        .UO_OUT4    (UO_OUT[4]),
        .UO_OUT5    (UO_OUT[5]),
        .UO_OUT6    (UO_OUT[6]),
        .UO_OUT7    (UO_OUT[7]),
        .UO_OUT8    (UO_OUT[8]),
        .UO_OUT9    (UO_OUT[9]),
        .UO_OUT10   (UO_OUT[10]),
        .UO_OUT11   (UO_OUT[11]),
        .UO_OUT12   (UO_OUT[12]),
        .UO_OUT13   (UO_OUT[13]),
        .UO_OUT14   (UO_OUT[14]),
        .UO_OUT15   (UO_OUT[15]),

        .UIO_IN0    (UIO_IN[0]),
        .UIO_IN1    (UIO_IN[1]),
        .UIO_IN2    (UIO_IN[2]),
        .UIO_IN3    (UIO_IN[3]),
        .UIO_IN4    (UIO_IN[4]),
        .UIO_IN5    (UIO_IN[5]),
        .UIO_IN6    (UIO_IN[6]),
        .UIO_IN7    (UIO_IN[7]),
        .UIO_IN8    (UIO_IN[8]),
        .UIO_IN9    (UIO_IN[9]),
        .UIO_IN10   (UIO_IN[10]),
        .UIO_IN11   (UIO_IN[11]),
        .UIO_IN12   (UIO_IN[12]),
        .UIO_IN13   (UIO_IN[13]),
        .UIO_IN14   (UIO_IN[14]),
        .UIO_IN15   (UIO_IN[15]),

        .UIO_OUT0    (UIO_OUT[0]),
        .UIO_OUT1    (UIO_OUT[1]),
        .UIO_OUT2    (UIO_OUT[2]),
        .UIO_OUT3    (UIO_OUT[3]),
        .UIO_OUT4    (UIO_OUT[4]),
        .UIO_OUT5    (UIO_OUT[5]),
        .UIO_OUT6    (UIO_OUT[6]),
        .UIO_OUT7    (UIO_OUT[7]),
        .UIO_OUT8    (UIO_OUT[8]),
        .UIO_OUT9    (UIO_OUT[9]),
        .UIO_OUT10   (UIO_OUT[10]),
        .UIO_OUT11   (UIO_OUT[11]),
        .UIO_OUT12   (UIO_OUT[12]),
        .UIO_OUT13   (UIO_OUT[13]),
        .UIO_OUT14   (UIO_OUT[14]),
        .UIO_OUT15   (UIO_OUT[15]),

        .UIO_OE0    (UIO_OE[0]),
        .UIO_OE1    (UIO_OE[1]),
        .UIO_OE2    (UIO_OE[2]),
        .UIO_OE3    (UIO_OE[3]),
        .UIO_OE4    (UIO_OE[4]),
        .UIO_OE5    (UIO_OE[5]),
        .UIO_OE6    (UIO_OE[6]),
        .UIO_OE7    (UIO_OE[7]),
        .UIO_OE8    (UIO_OE[8]),
        .UIO_OE9    (UIO_OE[9]),
        .UIO_OE10   (UIO_OE[10]),
        .UIO_OE11   (UIO_OE[11]),
        .UIO_OE12   (UIO_OE[12]),
        .UIO_OE13   (UIO_OE[13]),
        .UIO_OE14   (UIO_OE[14]),
        .UIO_OE15   (UIO_OE[15]),
        
        .ENA    (ENA),
        .CLK    (CLK),
        .RST_N  (RST_N)
    );

endmodule
