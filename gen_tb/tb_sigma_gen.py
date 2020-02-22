#!/usr/bin/python
import math
from parameters import *

print"`timescale 1ns / 1ps"

##########################################################
print "//##########################################################"
print "// SIGMA Testbench"
print "// Author: Eric Qin"
print "// Contact: ecqin@gatech.edu"
print "// Note: Floating point calculator: http://weitz.de/ieee/"
print "//##########################################################\n\n"
##########################################################

# BFP16 Hex Reference 
#   0x3F80 is 1
#   0x3FC0 is 1.5
#   0x4000 is 2


# Function to generate same data with length of amount of PEs
def gen_hex_data(data, pattern):
	if (pattern == "all"):
		string = ""
		for i in range(NUM_PES):
			if (i == 0):
				string = string + data
			else:
				string = string + "_" + data
		return string
	elif (pattern == "half"):
		string = ""
		for i in range(NUM_PES/2):
			if (i == 0):
				string = string + "0000"
			else:
				string = string + "_0000"
		for i in range(NUM_PES/2):
			string = string + "_" + data
		return string


# Determine number of dest bits needed based on topology
def gen_dest_width(top):
	if (top == "xbar"):
		return int(LOG2_PES*NUM_PES)
	elif (top == "benes"):
		levels = 2*LOG2_PES + 1
		return int(2*(levels-2)*NUM_PES + NUM_PES)

# decimal to binary
def convertToBinary(n, width):
	binary = str(bin(n).replace("0b", ""))
	length = len(binary)
	diff = width - length
	if (diff > 0):
		for i in range(diff):
			binary = "0" + binary
	return binary


# Generate simple xbar dest bus 
def gen_dest_bus(top, mapping):
	string = ""
	if (top == "xbar"):
		if (mapping == "direct"):
			for i in range(NUM_PES):
				string = convertToBinary(i, LOG2_PES) + string
		elif (mapping == "split"):
			for j in range(2):
				for i in range(NUM_PES/2):
					string = convertToBinary(i, LOG2_PES) + string
		else: # random mapping
			return string # TODO
		hexstring = str(hex(int(string, 2)).replace("0x", ""))
		hexstring = str(hexstring.replace("L", ""))
		return hexstring

	elif (top == "benes"): # TODO
		if (mapping == "direct"):
			return string
		elif (mapping == "split"):
			return string
		else: # random mapping
			return string

# Generate VN seperator
def gen_vn_seperator(style):
	string = ""
	if (style == "full"):
		for i in range(NUM_PES):
			if (i != NUM_PES-1):
				string = "_" + convertToBinary(0, LOG2_PES) + string
			else:
				string = convertToBinary(0, LOG2_PES) + string
			
	elif (style == "half"):
		for i in range(NUM_PES/2):
			string = "_" + convertToBinary(0, LOG2_PES) + string
		for i in range(NUM_PES/2):
			if (i != (NUM_PES/2)-1):
				string = "_" + convertToBinary(1, LOG2_PES) + string
			else:
				string = convertToBinary(1, LOG2_PES) + string
	elif (style == "odd"):
		start = 0
		for i in range(NUM_PES):
			if (i % 3 == 0):
				string = "_" + convertToBinary(start, LOG2_PES) + string
				start = start + 1
			else:
				if (i != NUM_PES-1):
					string = "_" + convertToBinary(start, LOG2_PES) + string
				else:
					string = convertToBinary(start, LOG2_PES) + string
	return string

##########################################################

print "module tb_flexdpe ();"

print"	parameter IN_DATA_TYPE = 16; // input data type width"
print"	parameter OUT_DATA_TYPE = 32; // output data type width"
print"	parameter NUM_PES = " + str(NUM_PES) + "; // number of PE Inputs"
print"	parameter LOG2_PES = " + str(LOG2_PES) + "; // log2 of the number of PEs"
	
print"	parameter NUM_TESTS = 8;"

print"	reg clk = 0;"
print"	reg rst;"

DBUS_WIDTH = int(16 * NUM_PES)


print"	reg [NUM_PES * IN_DATA_TYPE -1 : 0] i_data_bus [0:NUM_TESTS-1] ="
print"		{"
print"			" + str(DBUS_WIDTH) + "'h" + gen_hex_data("3F80", "all") + ","
print"			" + str(DBUS_WIDTH) + "'h" + gen_hex_data("3F80", "all") + ","
print"			" + str(DBUS_WIDTH) + "'h" + gen_hex_data("3F80", "half") + ","
print"			" + str(DBUS_WIDTH) + "'h" + gen_hex_data("3F80", "half") + ","
print"			" + str(DBUS_WIDTH) + "'h" + gen_hex_data("3FC0", "half") + ","
print"			" + str(DBUS_WIDTH) + "'h" + gen_hex_data("4000", "half") + ","
print"			" + str(DBUS_WIDTH) + "'h" + gen_hex_data("0000", "half") + ","
print"			" + str(DBUS_WIDTH) + "'h" + gen_hex_data("0000", "half") + "};"
print"\n"			
print"	reg [NUM_TESTS-1:0] i_data_valid = 8'b00111111;"
print"	reg [NUM_TESTS-1:0] i_stationary = 8'b00000001;"
print"\n"	
print"	reg [NUM_PES * LOG2_PES -1:0] i_dest_bus [0:NUM_TESTS-1] ="
print"		{"
print"			" + str(gen_dest_width(DTOP)) + "'h" + gen_dest_bus(DTOP, "direct") + ", // stationary"
print"			" + str(gen_dest_width(DTOP)) + "'h" + gen_dest_bus(DTOP, "split") + ", // streaming"
print"			" + str(gen_dest_width(DTOP)) + "'h" + gen_dest_bus(DTOP, "split") + ", // streaming"
print"			" + str(gen_dest_width(DTOP)) + "'h" + gen_dest_bus(DTOP, "split") + ", // streaming"
print"			" + str(gen_dest_width(DTOP)) + "'h" + gen_dest_bus(DTOP, "split") + ", // streaming"
print"			" + str(gen_dest_width(DTOP)) + "'h" + gen_dest_bus(DTOP, "split") + ", // streaming"
print"			" + str(gen_dest_width(DTOP)) + "'h0,"
print"			" + str(gen_dest_width(DTOP)) + "'h0};"
print"\n"			
print"	reg [NUM_PES * LOG2_PES -1:0] i_vn_seperator [0:NUM_TESTS-1] ="
print"		{" 
print"			" + str(NUM_PES*LOG2_PES) + "'b" + gen_vn_seperator("full") + ", // stationary"
print"			" + str(NUM_PES*LOG2_PES) + "'b" + gen_vn_seperator("full") + ", // streaming"
print"			" + str(NUM_PES*LOG2_PES) + "'b" + gen_vn_seperator("half") + ", // streaming"
print"			" + str(NUM_PES*LOG2_PES) + "'b" + gen_vn_seperator("odd") + ", // streaming"
print"			" + str(NUM_PES*LOG2_PES) + "'b" + gen_vn_seperator("half") + ", // streaming"
print"			" + str(NUM_PES*LOG2_PES) + "'b" + gen_vn_seperator("half") + ", // streaming"
print"			" + str(NUM_PES*LOG2_PES) + "'d0,"
print"			" + str(NUM_PES*LOG2_PES) + "'d0};"
print"\n"
print"	reg [NUM_PES-1:0] o_data_valid;"
print"	reg [NUM_PES * OUT_DATA_TYPE -1 : 0] o_data_bus; "
print"	reg [10:0] counter = 'd0;"
print"\n"
print"	// register of the inputs "
print"	reg [NUM_PES * IN_DATA_TYPE -1 : 0] r_data_bus = 'd0;"
print"	reg r_data_valid = 'd0;"
print"	reg r_stationary = 'd0;"
print"	reg [NUM_PES * LOG2_PES -1:0] r_dest_bus = 'd0;"
print"	reg [NUM_PES * LOG2_PES -1:0] r_vn_seperator;"
print"\n"	
print"	// generate simulation clock"
print"	always #1 clk = !clk;"
print"\n"
print"	// set reset signal"
print"	initial begin"
print"		rst = 1'b1;"
print"		#4"
print"		rst = 1'b0;"
print"	end"
print"\n"
print"	// generate input signals to DUT"
print"	always @ (posedge clk) begin"
print"		if (rst == 1'b0 && counter < NUM_TESTS) begin"
print"			r_data_bus = i_data_bus[counter];"
print"			r_data_valid = i_data_valid[counter];"
print"			r_stationary = i_stationary[counter];"
print"			r_dest_bus = i_dest_bus[counter];"
print"			r_vn_seperator = i_vn_seperator[counter];"
print"			if (counter < NUM_TESTS) begin"
print"				counter = counter + 1'b1;"
print"			end"
print"		end else begin"
print"			r_data_bus = 'd0;"
print"			r_data_valid = 'd0;"
print"			r_stationary = 'd0;"
print"			r_dest_bus = 'd0;"
print"			r_vn_seperator = 'd0;"
print"		end"
print"	end"
print"\n"
print"	// instantiate system (DUT)"
print"	flexdpe # ("
print"		.IN_DATA_TYPE(IN_DATA_TYPE),"
print"		.OUT_DATA_TYPE(OUT_DATA_TYPE),"
print"		.NUM_PES(NUM_PES),"
print"		.LOG2_PES(LOG2_PES))"
print"		my_flexdpe ("
print"		.clk(clk),"
print"		.rst(rst),"
print"		.i_data_valid(r_data_valid),"
print"		.i_data_bus(r_data_bus),"
print"		.i_stationary(r_stationary),"
print"		.i_dest_bus(r_dest_bus), "
print"		.i_vn_seperator(r_vn_seperator),"
print"		.o_data_valid(o_data_valid),"
print"		.o_data_bus(o_data_bus)"
print"	);"
print"\n"
print"	// create simulation waveform"
print"	initial begin"
print"		$vcdplusfile(\"flexdpe.vpd\");"
print"	 	$vcdpluson(0, tb_flexdpe); "
print"		#100 $finish;"
print"	end"
print"\n"
print"	integer g;"
print"	initial begin"
print"		g = $fopen(\"out_dump.txt\",\"w\");"
print"		$fwrite(g, \"\\n------------------------------------------\\n\");"
print"		$fwrite(g, \"Timestamp - Valid, - Value \");"
print"		$fwrite(g, \"\\n------------------------------------------\\n\");"
print"	end"
print"\n"
print"	always @ (posedge clk) begin"
print"		$fwrite(g, \"------------------------------------------ \\n\");"
print"		$fwrite(g, \"%d, %h, %h\\n\", $time, my_flexdpe.my_fan_network.o_valid[" + str(NUM_PES-1) + ":0], my_flexdpe.my_fan_network.o_data_bus[" + str(NUM_PES*OUT_DATA_TYPE-1) + ":0]);"
print"	end"
print"\n"
print"endmodule"



