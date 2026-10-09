// SPDX-FileCopyrightText: © 2026 Leo Moser <leo.moser@pm.me>
// SPDX-License-Identifier: Apache-2.0

`define sg13_IOPadIOVdd sg13cmos5l_IOPadIOVdd
`define sg13_IOPadIOVss sg13cmos5l_IOPadIOVss
`define sg13_IOPadVdd sg13cmos5l_IOPadVdd
`define sg13_IOPadVss sg13cmos5l_IOPadVss
`define sg13_IOPadIn sg13cmos5l_IOPadIn
`define sg13_IOPadOut30mA sg13cmos5l_IOPadOut30mA
`define sg13_IOPadInOut30mA sg13cmos5l_IOPadInOut30mA
`define sg13_IOPadAnalog sg13cmos5l_IOPadAnalog

module heichips26_top #(
    // Power/ground pads for core
    parameter NUM_VDD_PADS = 6,
    parameter NUM_VSS_PADS = 6,
    
    // Power/ground pads for I/O
    parameter NUM_IOVDD_PADS = 6,
    parameter NUM_IOVSS_PADS = 6
    )(
    `ifdef USE_POWER_PINS
    inout wire VDD,
    inout wire VSS,
    inout wire IOVDD,
    inout wire IOVSS,
    `endif

    inout  wire         fpga_clk_PAD,
    inout  wire         fpga_rst_n_PAD,

    inout  wire         fpga_sclk_PAD,
    inout  wire         fpga_cs_n_PAD,
    inout  wire         fpga_mosi_PAD,
    inout  wire         fpga_miso_PAD,

    inout  wire         fpga_mode_PAD,
    inout  wire         fpga_config_busy_PAD,
    inout  wire         fpga_config_configured_PAD,
    inout  wire [3:0]   fpga_config_slot_PAD,
    inout  wire         fpga_config_trigger_PAD,

    inout  wire [31:0]  fpga_io_PAD,
    
    // User I/Os
    inout  wire [17:0]  analog_PAD
);

    `ifdef USE_POWER_PINS
    wire VDDA;
    `endif

    // FPGA
    wire fpga_clk_PAD2CORE;
    wire fpga_rst_n_PAD2CORE;

    wire fpga_sclk_CORE2PAD;
    wire fpga_sclk_CORE2PAD_EN;
    wire fpga_sclk_PAD2CORE;

    wire fpga_cs_n_CORE2PAD;
    wire fpga_cs_n_CORE2PAD_EN;
    wire fpga_cs_n_PAD2CORE;

    wire fpga_mosi_CORE2PAD;
    wire fpga_mosi_CORE2PAD_EN;
    wire fpga_mosi_PAD2CORE;

    wire fpga_miso_CORE2PAD;
    wire fpga_miso_CORE2PAD_EN;
    wire fpga_miso_PAD2CORE;
    
    wire        fpga_mode_PAD2CORE;
    wire        fpga_config_busy_CORE2PAD;
    wire        fpga_config_configured_CORE2PAD;
    wire [3:0]  fpga_config_slot_PAD2CORE;
    wire        fpga_config_trigger_PAD2CORE;

    wire [31:0] fpga_io_PAD2CORE;
    wire [31:0] fpga_io_CORE2PAD;
    wire [31:0] fpga_io_CORE2PAD_EN;

    wire icelab_analog_pin0_PADRES;
    wire icelab_analog_pin1_PADRES;
    wire icelab_analog_pin2_PADRES;
    wire icelab_analog_pin3_PADRES;

    wire internal_analog_pin0_PADRES;
    wire internal_analog_pin1_PADRES;
    wire internal_analog_pin2_PADRES;

    wire pudding_i_in_PADRES;
    wire pudding_i_out_PADBARE;

    wire ethernet_dp_PADBARE;
    wire ethernet_dn_PADBARE;

    // Power/ground pad instances

    generate
    for (genvar i=0; i<NUM_IOVDD_PADS; i++) begin : iovdd_pads
        (* keep *)
        `sg13_IOPadIOVdd iovdd_pad  (
            `ifdef USE_POWER_PINS
            .iovdd  (IOVDD),
            .iovss  (IOVSS),
            .vdd    (VDD),
            .vss    (VSS)
            `endif
        );
    end
    for (genvar i=0; i<NUM_IOVSS_PADS; i++) begin : iovss_pads
        (* keep *)
        `sg13_IOPadIOVss iovss_pad  (
            `ifdef USE_POWER_PINS
            .iovdd  (IOVDD),
            .iovss  (IOVSS),
            .vdd    (VDD),
            .vss    (VSS)
            `endif
        );
    end
    for (genvar i=0; i<NUM_VDD_PADS; i++) begin : vdd_pads
        (* keep *)
        `sg13_IOPadVdd vdd_pad  (
            `ifdef USE_POWER_PINS
            .iovdd  (IOVDD),
            .iovss  (IOVSS),
            .vdd    (VDD),
            .vss    (VSS)
            `endif
        );
    end
    for (genvar i=0; i<NUM_VSS_PADS; i++) begin : vss_pads
        (* keep *)
        `sg13_IOPadVss vss_pad  (
            `ifdef USE_POWER_PINS
            .iovdd  (IOVDD),
            .iovss  (IOVSS),
            .vdd    (VDD),
            .vss    (VSS)
            `endif
        );
    end
    endgenerate

    // FPGA IO pad instances

    `sg13_IOPadIn fpga_clk (
        `ifdef USE_POWER_PINS
        .iovdd  (IOVDD),
        .iovss  (IOVSS),
        .vdd    (VDD),
        .vss    (VSS),
        `endif
        .p2c (fpga_clk_PAD2CORE),
        .pad (fpga_clk_PAD)
    );
    
    `sg13_IOPadIn fpga_rst_n (
        `ifdef USE_POWER_PINS
        .iovdd  (IOVDD),
        .iovss  (IOVSS),
        .vdd    (VDD),
        .vss    (VSS),
        `endif
        .p2c (fpga_rst_n_PAD2CORE),
        .pad (fpga_rst_n_PAD)
    );

    `sg13_IOPadInOut30mA fpga_sclk (
        `ifdef USE_POWER_PINS
        .iovdd  (IOVDD),
        .iovss  (IOVSS),
        .vdd    (VDD),
        .vss    (VSS),
        `endif
        .c2p    (fpga_sclk_CORE2PAD),
        .c2p_en (fpga_sclk_CORE2PAD_EN),
        .p2c    (fpga_sclk_PAD2CORE),
        .pad    (fpga_sclk_PAD )
    );
    
    `sg13_IOPadInOut30mA fpga_cs_n (
        `ifdef USE_POWER_PINS
        .iovdd  (IOVDD),
        .iovss  (IOVSS),
        .vdd    (VDD),
        .vss    (VSS),
        `endif
        .c2p    (fpga_cs_n_CORE2PAD),
        .c2p_en (fpga_cs_n_CORE2PAD_EN),
        .p2c    (fpga_cs_n_PAD2CORE),
        .pad    (fpga_cs_n_PAD )
    );
    
    `sg13_IOPadInOut30mA fpga_mosi (
        `ifdef USE_POWER_PINS
        .iovdd  (IOVDD),
        .iovss  (IOVSS),
        .vdd    (VDD),
        .vss    (VSS),
        `endif
        .c2p    (fpga_mosi_CORE2PAD),
        .c2p_en (fpga_mosi_CORE2PAD_EN),
        .p2c    (fpga_mosi_PAD2CORE),
        .pad    (fpga_mosi_PAD )
    );
    
    `sg13_IOPadInOut30mA fpga_miso (
        `ifdef USE_POWER_PINS
        .iovdd  (IOVDD),
        .iovss  (IOVSS),
        .vdd    (VDD),
        .vss    (VSS),
        `endif
        .c2p    (fpga_miso_CORE2PAD),
        .c2p_en (fpga_miso_CORE2PAD_EN),
        .p2c    (fpga_miso_PAD2CORE),
        .pad    (fpga_miso_PAD )
    );

    `sg13_IOPadIn fpga_mode (
        `ifdef USE_POWER_PINS
        .iovdd  (IOVDD),
        .iovss  (IOVSS),
        .vdd    (VDD),
        .vss    (VSS),
        `endif
        .p2c (fpga_mode_PAD2CORE),
        .pad (fpga_mode_PAD)
    );
    
    `sg13_IOPadOut30mA fpga_config_busy (
        `ifdef USE_POWER_PINS
        .iovdd  (IOVDD),
        .iovss  (IOVSS),
        .vdd    (VDD),
        .vss    (VSS),
        `endif
        .c2p (fpga_config_busy_CORE2PAD),
        .pad (fpga_config_busy_PAD)
    );
    
    generate
    for (genvar i=0; i<32; i++) begin : fpga_ios
        `sg13_IOPadInOut30mA fpga_io (
            `ifdef USE_POWER_PINS
            .iovdd  (IOVDD),
            .iovss  (IOVSS),
            .vdd    (VDD),
            .vss    (VSS),
            `endif
            .c2p    (fpga_io_CORE2PAD[i]),
            .c2p_en (fpga_io_CORE2PAD_EN[i]),
            .p2c    (fpga_io_PAD2CORE[i]),
            .pad    (fpga_io_PAD[i])
        );
    end
    endgenerate

    `sg13_IOPadOut30mA fpga_config_configured (
        `ifdef USE_POWER_PINS
        .iovdd  (IOVDD),
        .iovss  (IOVSS),
        .vdd    (VDD),
        .vss    (VSS),
        `endif
        .c2p (fpga_config_configured_CORE2PAD),
        .pad (fpga_config_configured_PAD)
    );

    generate
    for (genvar i=0; i<4; i++) begin : fpga_config_slot
        `sg13_IOPadIn fpga_config_slot (
            `ifdef USE_POWER_PINS
            .iovdd  (IOVDD),
            .iovss  (IOVSS),
            .vdd    (VDD),
            .vss    (VSS),
            `endif
            .p2c (fpga_config_slot_PAD2CORE[i]),
            .pad (fpga_config_slot_PAD[i])
        );
    end
    endgenerate

    `sg13_IOPadIn fpga_config_trigger (
        `ifdef USE_POWER_PINS
        .iovdd  (IOVDD),
        .iovss  (IOVSS),
        .vdd    (VDD),
        .vss    (VSS),
        `endif
        .p2c (fpga_config_trigger_PAD2CORE),
        .pad (fpga_config_trigger_PAD)
    );
    
    // Analog for the user projects
    wire [17:0] analog_routing;
    
    generate
    for (genvar i=0; i<18; i++) begin : analog
        (* keep *) `sg13_IOPadAnalog analog_pad (
            `ifdef USE_POWER_PINS
            .iovdd  (IOVDD),
            .iovss  (IOVSS),
            .vdd    (VDD),
            .vss    (VSS),
            `endif
            .padres (analog_routing[i]),
            .pad (analog_PAD[i])
        );
    end
    endgenerate

    // Core
    heichips26_core heichips26_core (
        `ifdef USE_POWER_PINS
        .VDD  (VDD),
        .VSS  (VSS),
        .VDDA (VDDA),
        `endif
    
        // FPGA
        .fpga_clk_i     (fpga_clk_PAD2CORE),
        .fpga_rst_ni    (fpga_rst_n_PAD2CORE),

        .fpga_sclk_i    (fpga_sclk_PAD2CORE),
        .fpga_sclk_o    (fpga_sclk_CORE2PAD),
        .fpga_sclk_en_o (fpga_sclk_CORE2PAD_EN),
        
        .fpga_cs_n_i    (fpga_cs_n_PAD2CORE),
        .fpga_cs_n_o    (fpga_cs_n_CORE2PAD),
        .fpga_cs_n_en_o (fpga_cs_n_CORE2PAD_EN),
        
        .fpga_mosi_i    (fpga_mosi_PAD2CORE),
        .fpga_mosi_o    (fpga_mosi_CORE2PAD),
        .fpga_mosi_en_o (fpga_mosi_CORE2PAD_EN),
        
        .fpga_miso_i    (fpga_miso_PAD2CORE),
        .fpga_miso_o    (fpga_miso_CORE2PAD),
        .fpga_miso_en_o (fpga_miso_CORE2PAD_EN),

        .fpga_mode_i                (fpga_mode_PAD2CORE),
        .fpga_config_busy_o         (fpga_config_busy_CORE2PAD),
        .fpga_config_configured_o   (fpga_config_configured_CORE2PAD),
        .fpga_config_slot_i         (fpga_config_slot_PAD2CORE),
        .fpga_config_trigger_i      (fpga_config_trigger_PAD2CORE),

        .heichips26_instance_small_0_analog_0 (analog_routing[0]),
        .heichips26_instance_small_0_analog_1 (analog_routing[1]),
        .heichips26_instance_small_0_analog_2 (analog_routing[2]),

        .heichips26_instance_small_1_analog_0 (analog_routing[3]),
        .heichips26_instance_small_1_analog_1 (analog_routing[4]),
        .heichips26_instance_small_1_analog_2 (analog_routing[5]),

        .heichips26_instance_small_5_analog_0 (analog_routing[6]),
        .heichips26_instance_small_5_analog_1 (analog_routing[7]),
        .heichips26_instance_small_5_analog_2 (analog_routing[8]),

        // I/Os FPGA
        .fabric_io_in_i     (fpga_io_PAD2CORE),
        .fabric_io_out_o    (fpga_io_CORE2PAD),
        .fabric_io_oe_o     (fpga_io_CORE2PAD_EN)
    );

    // Alignment marks for bonding
    (* keep *) alignment_mark alignment_mark_0 ();
    (* keep *) alignment_mark alignment_mark_1 ();
    (* keep *) alignment_mark alignment_mark_2 ();
    (* keep *) alignment_mark alignment_mark_3 ();

    // Logos
    (* keep *) logo_heichips logo_heichips ();
    (* keep *) logo_fabulous logo_fabulous ();
    (* keep *) logo_credits logo_credits ();

endmodule
