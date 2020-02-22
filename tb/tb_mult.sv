`timescale 1ns / 1ps
////////////////////////////////////////////////////////////

// Design: tb_mult.v
// Author: Eric Qin

// Description: Testbench for BFP16 Multiplier

////////////////////////////////////////////////////////////

module tb_mult ();

	parameter DATA_TYPE = 16; // data type width
  parameter NUM_TESTS = 4;

	reg clk = 0;
	reg rst = 0;

	reg [DATA_TYPE-1:0] input_A [0:NUM_TESTS-1] = 
    // 3, 8, 1024, 1.25
    {16'h4040, 16'h4100, 16'h4480, 16'h3FA0};
    
	reg [DATA_TYPE-1:0] input_B [0:NUM_TESTS-1] = 
    // 1, 1240, 8192, 2.5
    {16'h3F80, 16'h449B, 16'h4600, 16'h4020};
    
  reg [10:0] counter = 'd0;

	reg [DATA_TYPE-1:0] O; // Expected = 3, 9920, 8388608, 3.125  // 0x4040, 0x461B, 0x4B00, 0x4048
 
  reg [DATA_TYPE-1:0] A;
  reg [DATA_TYPE-1:0] B;

	// Generate simulation clock
	always #1 clk = !clk;

  // set the input values per clock cycle
  always @ (posedge clk) begin
      A = input_A[counter];
      B = input_B[counter];
      if (counter < NUM_TESTS-1) begin
        counter = counter + 1'b1;
      end else begin
        counter = 'd0;
      end
  end

	// instantiate system
	multiplier my_mult(
		.clk(clk),
		.A(A),
		.B(B),
		.O(O)
	);

	// Print the mux inputs...
	initial begin
		#1000 $finish;
	end


	initial begin
		$vcdplusfile("mult.vpd");
	 	$vcdpluson(0, tb_mult); 
		#100 $finish;
	end

endmodule

