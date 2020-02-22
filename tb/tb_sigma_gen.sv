`timescale 1ns / 1ps
//##########################################################
// SIGMA Testbench
// Author: Eric Qin
// Contact: ecqin@gatech.edu
// Note: Floating point calculator: http://weitz.de/ieee/
//##########################################################


module tb_flexdpe ();
	parameter IN_DATA_TYPE = 16; // input data type width
	parameter OUT_DATA_TYPE = 32; // output data type width
	parameter NUM_PES = 32; // number of PE Inputs
	parameter LOG2_PES = 5; // log2 of the number of PEs
	parameter NUM_TESTS = 8;
	reg clk = 0;
	reg rst;
	reg [NUM_PES * IN_DATA_TYPE -1 : 0] i_data_bus [0:NUM_TESTS-1] =
		{
			512'h3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80,
			512'h3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80,
			512'h0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80,
			512'h0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80_3F80,
			512'h0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_3FC0_3FC0_3FC0_3FC0_3FC0_3FC0_3FC0_3FC0_3FC0_3FC0_3FC0_3FC0_3FC0_3FC0_3FC0_3FC0,
			512'h0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_4000_4000_4000_4000_4000_4000_4000_4000_4000_4000_4000_4000_4000_4000_4000_4000,
			512'h0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000,
			512'h0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000};


	reg [NUM_TESTS-1:0] i_data_valid = 8'b00111111;
	reg [NUM_TESTS-1:0] i_stationary = 8'b00000001;


	reg [NUM_PES * LOG2_PES -1:0] i_dest_bus [0:NUM_TESTS-1] =
		{
			160'hffbbcdeb38bdab49ca307b9ac5a928398a418820, // stationary
			160'h7b9ac5a928398a4188207b9ac5a928398a418820, // streaming
			160'h7b9ac5a928398a4188207b9ac5a928398a418820, // streaming
			160'h7b9ac5a928398a4188207b9ac5a928398a418820, // streaming
			160'h7b9ac5a928398a4188207b9ac5a928398a418820, // streaming
			160'h7b9ac5a928398a4188207b9ac5a928398a418820, // streaming
			160'h0,
			160'h0};


	reg [NUM_PES * LOG2_PES -1:0] i_vn_seperator [0:NUM_TESTS-1] =
		{
			160'b00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000, // stationary
			160'b00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000, // streaming
			160'b00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000, // streaming
			160'b01011_01010_01010_01010_01001_01001_01001_01000_01000_01000_00111_00111_00111_00110_00110_00110_00101_00101_00101_00100_00100_00100_00011_00011_00011_00010_00010_00010_00001_00001_00001_00000, // streaming
			160'b00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000, // streaming
			160'b00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00001_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000_00000, // streaming
			160'd0,
			160'd0};


	reg [NUM_PES-1:0] o_data_valid;
	reg [NUM_PES * OUT_DATA_TYPE -1 : 0] o_data_bus; 
	reg [10:0] counter = 'd0;


	// register of the inputs 
	reg [NUM_PES * IN_DATA_TYPE -1 : 0] r_data_bus = 'd0;
	reg r_data_valid = 'd0;
	reg r_stationary = 'd0;
	reg [NUM_PES * LOG2_PES -1:0] r_dest_bus = 'd0;
	reg [NUM_PES * LOG2_PES -1:0] r_vn_seperator;


	// generate simulation clock
	always #1 clk = !clk;


	// set reset signal
	initial begin
		rst = 1'b1;
		#4
		rst = 1'b0;
	end


	// generate input signals to DUT
	always @ (posedge clk) begin
		if (rst == 1'b0 && counter < NUM_TESTS) begin
			r_data_bus = i_data_bus[counter];
			r_data_valid = i_data_valid[counter];
			r_stationary = i_stationary[counter];
			r_dest_bus = i_dest_bus[counter];
			r_vn_seperator = i_vn_seperator[counter];
			if (counter < NUM_TESTS) begin
				counter = counter + 1'b1;
			end
		end else begin
			r_data_bus = 'd0;
			r_data_valid = 'd0;
			r_stationary = 'd0;
			r_dest_bus = 'd0;
			r_vn_seperator = 'd0;
		end
	end


	// instantiate system (DUT)
	flexdpe # (
		.IN_DATA_TYPE(IN_DATA_TYPE),
		.OUT_DATA_TYPE(OUT_DATA_TYPE),
		.NUM_PES(NUM_PES),
		.LOG2_PES(LOG2_PES))
		my_flexdpe (
		.clk(clk),
		.rst(rst),
		.i_data_valid(r_data_valid),
		.i_data_bus(r_data_bus),
		.i_stationary(r_stationary),
		.i_dest_bus(r_dest_bus), 
		.i_vn_seperator(r_vn_seperator),
		.o_data_valid(o_data_valid),
		.o_data_bus(o_data_bus)
	);


	// create simulation waveform
	initial begin
		$vcdplusfile("flexdpe.vpd");
	 	$vcdpluson(0, tb_flexdpe); 
		#100 $finish;
	end


	integer g;
	initial begin
		g = $fopen("out_dump.txt","w");
		$fwrite(g, "\n------------------------------------------\n");
		$fwrite(g, "Timestamp - Valid, - Value ");
		$fwrite(g, "\n------------------------------------------\n");
	end


	always @ (posedge clk) begin
		$fwrite(g, "------------------------------------------ \n");
		$fwrite(g, "%d, %h, %h\n", $time, my_flexdpe.my_fan_network.o_valid[31:0], my_flexdpe.my_fan_network.o_data_bus[1023:0]);
	end


endmodule
