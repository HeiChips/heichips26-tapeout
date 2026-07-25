module tt_project_to_sram (
    input  wire       clk1,
    input  wire       rst,

    output wire [27-1:0] io_out
);

    logic [7:0] ui_in;
    logic [7:0] uo_out;
    logic [7:0] uio_in;
    logic [7:0] uio_out;
    logic [7:0] uio_oe;
    logic       rst_n;

    assign rst_n = !rst;

    // Top left user project at (X0Y1)
    // Change the coordinates under primitive_wrappers.v
    TT_PROJECT_wrapper TT_PROJECT_wrapper (
        .UI_IN      (ui_in),
        .UO_OUT     (uo_out),
        .UIO_IN     (uio_in),
        .UIO_OUT    (uio_out),
        .UIO_OE     (uio_oe),
        .ENA        (1'b1),
        .CLK        (clk1),
        .RST_N      (rst_n)
    );

    logic [ 9:0] sram_addr;
    logic [31:0] sram_bm;
    logic [31:0] sram_din;
    logic        sram_wen;
    logic        sram_men;
    logic        sram_ren;
    logic [31:0] sram_dout;
    
    IHP_SRAM_1024x32_1RW_wrapper IHP_SRAM_1024x32_1RW_wrapper (
        .CLK   (clk1),
        .ADDR  (sram_addr),
        .BM    (sram_bm),
        .DIN   (sram_din),
        .WEN   (sram_wen),
        .MEN   (sram_men),
        .REN   (sram_ren),
        .DOUT  (sram_dout)
    );
    
    // Assignments
    // - do random stuff
    
    assign sram_addr = {2'b0, uo_out};
    assign sram_bm = {{8{uio_out[3]}}, {8{uio_out[2]}}, {8{uio_out[1]}}, {8{uio_out[0]}}};
    assign sram_din = uo_out;
    assign sram_wen = uio_out[4];
    assign sram_men = 1'b1;
    assign sram_ren = uio_out[5];
    
    assign ui_in = sram_dout[7:0];
    assign uio_in = sram_dout[15:8];
    assign io_out[15:0] = sram_dout[31:16];
    
    assign io_out[17:16] = uio_out[7:6];
    assign io_out[26:18] = uio_oe;

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

module IHP_SRAM_1024x32_1RW_wrapper (
    input                 CLK,
    input  [(10 - 1) : 0] ADDR,
    input  [(32 - 1) : 0] DIN,
    input  [(32 - 1) : 0] BM,
    input                 WEN,
    input                 MEN,
    input                 REN,
    	output [(32 - 1) : 0] DOUT
);

    IHP_SRAM_1024x32_1RW IHP_SRAM_1024x32_1RW (
        .CLK  (CLK),
        .ADDR0 (ADDR[0]),
        .ADDR1 (ADDR[1]),
        .ADDR2 (ADDR[2]),
        .ADDR3 (ADDR[3]),
        .ADDR4 (ADDR[4]),
        .ADDR5 (ADDR[5]),
        .ADDR6 (ADDR[6]),
        .ADDR7 (ADDR[7]),
        .ADDR8 (ADDR[8]),
        .ADDR9 (ADDR[9]),
        .DIN0 (DIN[0]),
        .DIN1 (DIN[1]),
        .DIN2 (DIN[2]),
        .DIN3 (DIN[3]),
        .DIN4 (DIN[4]),
        .DIN5 (DIN[5]),
        .DIN6 (DIN[6]),
        .DIN7 (DIN[7]),
        .DIN8 (DIN[8]),
        .DIN9 (DIN[9]),
        .DIN10 (DIN[10]),
        .DIN11 (DIN[11]),
        .DIN12 (DIN[12]),
        .DIN13 (DIN[13]),
        .DIN14 (DIN[14]),
        .DIN15 (DIN[15]),
        .DIN16 (DIN[16]),
        .DIN17 (DIN[17]),
        .DIN18 (DIN[18]),
        .DIN19 (DIN[19]),
        .DIN20 (DIN[20]),
        .DIN21 (DIN[21]),
        .DIN22 (DIN[22]),
        .DIN23 (DIN[23]),
        .DIN24 (DIN[24]),
        .DIN25 (DIN[25]),
        .DIN26 (DIN[26]),
        .DIN27 (DIN[27]),
        .DIN28 (DIN[28]),
        .DIN29 (DIN[29]),
        .DIN30 (DIN[30]),
        .DIN31 (DIN[31]),
        .BM0 (BM[0]),
        .BM1 (BM[1]),
        .BM2 (BM[2]),
        .BM3 (BM[3]),
        .BM4 (BM[4]),
        .BM5 (BM[5]),
        .BM6 (BM[6]),
        .BM7 (BM[7]),
        .BM8 (BM[8]),
        .BM9 (BM[9]),
        .BM10 (BM[10]),
        .BM11 (BM[11]),
        .BM12 (BM[12]),
        .BM13 (BM[13]),
        .BM14 (BM[14]),
        .BM15 (BM[15]),
        .BM16 (BM[16]),
        .BM17 (BM[17]),
        .BM18 (BM[18]),
        .BM19 (BM[19]),
        .BM20 (BM[20]),
        .BM21 (BM[21]),
        .BM22 (BM[22]),
        .BM23 (BM[23]),
        .BM24 (BM[24]),
        .BM25 (BM[25]),
        .BM26 (BM[26]),
        .BM27 (BM[27]),
        .BM28 (BM[28]),
        .BM29 (BM[29]),
        .BM30 (BM[30]),
        .BM31 (BM[31]),
        .WEN  (WEN),
        .MEN  (MEN),
        .REN  (REN),
        .DOUT0 (DOUT[0]),
        .DOUT1 (DOUT[1]),
        .DOUT2 (DOUT[2]),
        .DOUT3 (DOUT[3]),
        .DOUT4 (DOUT[4]),
        .DOUT5 (DOUT[5]),
        .DOUT6 (DOUT[6]),
        .DOUT7 (DOUT[7]),
        .DOUT8 (DOUT[8]),
        .DOUT9 (DOUT[9]),
        .DOUT10 (DOUT[10]),
        .DOUT11 (DOUT[11]),
        .DOUT12 (DOUT[12]),
        .DOUT13 (DOUT[13]),
        .DOUT14 (DOUT[14]),
        .DOUT15 (DOUT[15]),
        .DOUT16 (DOUT[16]),
        .DOUT17 (DOUT[17]),
        .DOUT18 (DOUT[18]),
        .DOUT19 (DOUT[19]),
        .DOUT20 (DOUT[20]),
        .DOUT21 (DOUT[21]),
        .DOUT22 (DOUT[22]),
        .DOUT23 (DOUT[23]),
        .DOUT24 (DOUT[24]),
        .DOUT25 (DOUT[25]),
        .DOUT26 (DOUT[26]),
        .DOUT27 (DOUT[27]),
        .DOUT28 (DOUT[28]),
        .DOUT29 (DOUT[29]),
        .DOUT30 (DOUT[30]),
        .DOUT31 (DOUT[31])
    );

endmodule
