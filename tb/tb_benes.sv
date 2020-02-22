`timescale 1ns / 1ps
////////////////////////////////////////////////////////////

// Design: tb_benes.v
// Author: Eric Qin

// Description: Simple testbench for benes network.

////////////////////////////////////////////////////////////

module tb_benes ();

	parameter DATA_TYPE = 16; // data type width
	parameter NUM_PES = 8; // number of PE Inputs
	parameter LEVELS = 7; // Levels of switching for a non-blocking back-to-back butterfly: 2log(2*NUM_PES)+1

	parameter NUM_TESTS = 3;
	
	reg clk = 0;
	reg rst = 0;
	reg [2*(LEVELS-2)*NUM_PES + NUM_PES-1 : 0] i_mux_bus [0:NUM_TESTS-1] = 
		{88'hFF_FFFF_FFFF_FFFF_FFFF_FFFF, 
		 88'h00_0000_0000_0000_0000_0000,
		 88'hFF_0000_0000_0000_0000_0000}; // pass through, all horizontal

	reg [NUM_PES * DATA_TYPE -1 : 0] i_data_bus = 128'h7777_6666_5555_4444_3333_2222_1111_0000;

	wire [NUM_PES * DATA_TYPE -1 : 0] o_dist_bus;

	reg [2*(LEVELS-2)*NUM_PES + NUM_PES-1 : 0] r_mux_bus;
	
	reg [10:0] counter = 'd0;
	
	// Generate simulation clock (NOT USED)
	always #1 clk = !clk;
	
	// set the input values per clock cycle
	always @ (posedge clk) begin
		r_mux_bus = i_mux_bus[counter];
		if (counter < NUM_TESTS-1) begin
			counter = counter + 1'b1;
		end else begin
			counter = 'd0;
		end
	end

	// instantiate system
	benes my_benes(
		.clk(clk),
		.rst(rst),
		.i_data_bus(i_data_bus),
		.i_mux_bus(r_mux_bus),
		.o_dist_bus(o_dist_bus)
	);


	initial begin
		$vcdplusfile("benes.vpd");
	 	$vcdpluson(0, tb_benes); 
		#100 $finish;
	end

endmodule



