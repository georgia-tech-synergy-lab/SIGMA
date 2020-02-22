#!/usr/bin/python 
import math
from fan_func import *

##########################################################
print "//##########################################################"
print "// Generated Fowarding Adder Network (FAN topology)"
print "// Author: Eric Qin"
print "// Contact: ecqin@gatech.edu"
print "//##########################################################\n\n"
##########################################################


##########################################################
# Generating module initization and input/output ports
##########################################################

DATA_TYPE = OUT_DATA_TYPE # true for reduction network (reduce with FP32)

print "module fan_network # ("
print "\tparameter DATA_TYPE = ", OUT_DATA_TYPE, ","
print "\tparameter NUM_PES = ", NUM_PES, ","
print "\tparameter LOG2_PES = ", LOG2_PES, ") ("
print "\tclk,"
print "\trst,"
print "\ti_valid," # valid input data bus signal
print "\ti_data_bus," # input data bus from multipliers
print "\ti_add_en_bus," # adder enable bus
print "\ti_cmd_bus," # cmd for all of the adders
print "\ti_sel_bus," # mux select to the inputs of the adders
print "\to_valid," # output valid signal bus
print "\to_data_bus" # output data bus
print ");" 

print "\tinput clk;"
print "\tinput rst;"
print "\tinput i_valid; // valid input data bus"
print "\tinput [NUM_PES*DATA_TYPE-1 : 0] i_data_bus; // input data bus"
print "\tinput [(NUM_PES-1)-1 : 0] i_add_en_bus; // adder enable bus"
print "\tinput [3*(NUM_PES-1)-1 : 0] i_cmd_bus; // command bits for each adder"
NUM_SEL_BITS = get_sel_bits()
print "\tinput [" +  str(int(NUM_SEL_BITS- 1)) + " : 0] i_sel_bus; // select bits for FAN topolgy"
print "\toutput reg [NUM_PES-1 : 0] o_valid; // output valid signal"
print "\toutput reg [NUM_PES*DATA_TYPE-1 : 0] o_data_bus; // output data bus\n"

##########################################################
# Generate wire and reg declarations 
##########################################################

# tree wires (includes binary and forwarding wires)
print "\t// tree wires (includes binary and forwarding wires)"
for i in range(LOG2_PES):
	TREE_WIRE = get_binary_fwd_wires(i)
	print "\twire [", TREE_WIRE * DATA_TYPE - 1 ," : 0] w_fan_lvl_" + str(i) + ";"
print "\n"

# flop fowarding levels across levels to maintain timing
print "\t// flop forwarding levels across levels to maintain pipeline timing"
for i in range(LOG2_PES - 2): # reg data type for FF
	for j in range(LOG2_PES - 2 - i):
		lvl_src = i
		lvl_dest = LOG2_PES-1-j
		fwd_width = get_fwd_links_width(lvl_src, lvl_dest)
		print "\treg [" + str(fwd_width -1 ) + " : 0] r_fan_ff_lvl_" + str(lvl_src) + "_to_" + str(lvl_dest) +  ";" 
print "\n"

# output virtual neuron (completed partial sums) wires for each level and valid bits
print "\t// output virtual neuron (completed partial sums) wires for each level and valid bits"
for i in range(LOG2_PES):
	upper_bound = (NUM_PES >> i )
	print "\twire [" + str(upper_bound*DATA_TYPE -1) + " : 0] w_vn_lvl_" + str(i) + ";"
	print "\twire [" + str(upper_bound -1) + " : 0] w_vn_lvl_" + str(i) + "_valid;"
print "\n"

# output ff within each level of adder tree to maintain pipeline behavior
print "\t// output ff within each level of adder tree to maintain pipeline behavior"
print "\treg [" + str(NUM_PES * LOG2_PES * DATA_TYPE - 1) + " : 0] r_lvl_output_ff;"
print "\treg [" + str(NUM_PES * LOG2_PES -1) + " : 0] r_lvl_output_ff_valid;" 
print "\n"

# valid FFs for each level of the adder tree
print "\t// valid FFs for each level of the adder tree"
print "\treg [" + str(LOG2_PES + 1) + " : 0] r_valid;" # system delay

# flop final adder output cmd and values for timing alignment
print "\t// flop final adder output cmd and values"
print "\treg [DATA_TYPE-1:0] r_final_sum;"
print "\treg r_final_add;"
print "\treg r_final_add2;"

##########################################################
# Generate Flip Flops for fowarding levels to maintain timing (FAN Toplogy fwd link timing)
##########################################################

# Flip flops for forwarding levels to maintain pipeline timing
print "\t// FAN topology flip flops between forwarding levels to maintain pipeline timing"
print "\talways @ (posedge clk) begin"
print "\t\tif (rst == 1'b1) begin" # set FFs to zero when reset is 1'b1
for i in range(LOG2_PES - 2):
	for j in range(LOG2_PES - 2 - i):
		lvl_src = i
		lvl_dest = LOG2_PES-1-j
		print "\t\t\tr_fan_ff_lvl_" + str(lvl_src) + "_to_" + str(lvl_dest) +  " = 'd0;" 
print "\t\tend else begin" # set FFs to corresponding inputs
for i in range(LOG2_PES - 2):
	new_i = 0
	for j in range(LOG2_PES - 2 - i):
		lvl_src = i
		lvl_dest = LOG2_PES-1-j
		num_links = get_num_fwd_links(lvl_src, lvl_dest)
	
		if (new_i == LOG2_PES - 2 - i - 1): # Input of fowarding link FF comes directly from adder
			for n in range(num_links):
				print "\t\t\tr_fan_ff_lvl_" + str(lvl_src) + "_to_" + str(lvl_dest) + "[" + str(int((n+1)*DATA_TYPE-1)) + ":" + str(n*int(DATA_TYPE)) + "] = w_fan_lvl_" + str(lvl_src) + get_ff_adder_index(lvl_src, lvl_dest, n)
				
		else: # Input of forwarding link FF comes from a previous FF
			for n in range(num_links):
				print "\t\t\tr_fan_ff_lvl_" + str(lvl_src) + "_to_" + str(lvl_dest) + "[" + str(int((n+1)*DATA_TYPE-1)) + ":" + str(n*int(DATA_TYPE)) + "] = r_fan_ff_lvl_" + str(lvl_src) + "_to_" + str(lvl_dest-1) + get_ff_fwd_index(lvl_src, lvl_dest, n)
			new_i = new_i + 1
			
print "\t\tend"
print "\tend"
print "\n"

##########################################################
# Generate Output Buffers and Muxes across all levels to pipeline finished VNs (complete Psums)
##########################################################

print"\t// Output Buffers and Muxes across all levels to pipeline finished VNs (complete Psums)"
for i in range(LOG2_PES):
	max_range = (i+1)*NUM_PES*DATA_TYPE-1 
	min_range = i*NUM_PES*DATA_TYPE 
	max_range_v = (i+1)*NUM_PES-1
	min_range_v = i*NUM_PES
	adder_vn = []
	print "\talways @ (posedge clk) begin"
	print "\t\tif (rst == 1'b1) begin" # set output VN FFs to zero when reset is 1'b1
	print "\t\t\tr_lvl_output_ff[" + str(max_range) + ":" + str(min_range) + "] <= 'd0;"
	print "\t\t\tr_lvl_output_ff_valid[" + str(max_range_v) + ":" + str(min_range_v) + "] <= 'd0;"
	print "\t\tend else begin" # set output VN FFs to previous level
	if (i == 0): # level 0
		for s in range(NUM_PES >> (i+1)):
			print "\t\t\tif (w_vn_lvl_" + str(i) + "_valid[" + str(s*2+1) + ":" + str(s*2) + "] == 2'b11) begin // both VN complete" 
			print "\t\t\t\tr_lvl_output_ff[" + str(2*(s+1)*DATA_TYPE-1) + ":" + str(2*s*DATA_TYPE) + "] <= w_vn_lvl_0[" + str(2*(s+1)*DATA_TYPE-1) + ":" + str(2*s*DATA_TYPE) + "];"
			print "\t\t\t\tr_lvl_output_ff_valid[" + str(2*(s+1)-1) + ":" + str(2*s) + "] <= 2'b11;"
			print "\t\t\tend else if (w_vn_lvl_" + str(i) + "_valid[" + str(s*2+1) + ":" + str(s*2) + "] == 2'b10) begin // right VN complete"
			print "\t\t\t\tr_lvl_output_ff[" + str(2*(s+1)*DATA_TYPE-1) + ":" + str(2*s*DATA_TYPE+DATA_TYPE) + "] <= w_vn_lvl_0[" + str(2*(s+1)*DATA_TYPE-1) + ":" + str(2*s*DATA_TYPE+DATA_TYPE) + "];"
			print "\t\t\t\tr_lvl_output_ff[" + str(2*s*DATA_TYPE+DATA_TYPE-1) + ":" + str(2*s*DATA_TYPE) + "] <= 'd0;"
			print "\t\t\t\tr_lvl_output_ff_valid[" + str(2*(s+1)-1) + ":" + str(2*s) + "] <= 2'b10;"
			print "\t\t\tend else if (w_vn_lvl_" + str(i) + "_valid[" + str(s*2+1) + ":" + str(s*2) + "] == 2'b01) begin // left VN complete"
			print "\t\t\t\tr_lvl_output_ff[" + str(2*(s+1)*DATA_TYPE-1) + ":" + str(2*s*DATA_TYPE) + "] <= 'd0;"
			print "\t\t\t\tr_lvl_output_ff[" + str(2*s*DATA_TYPE+DATA_TYPE-1) + ":" + str(2*s*DATA_TYPE) + "] <= w_vn_lvl_0[" +  str(2*s*DATA_TYPE+DATA_TYPE-1) + ":" + str(2*s*DATA_TYPE) + "];"
			print "\t\t\t\tr_lvl_output_ff_valid[" + str(2*(s+1)-1) + ":" + str(2*s) + "] <= 2'b01;"
			print "\t\t\tend else begin // no VN complete"
			print "\t\t\t\tr_lvl_output_ff[" + str(2*(s+1)*DATA_TYPE-1) + ":" + str(2*s*DATA_TYPE) + "] <= 'd0; "
			print "\t\t\t\tr_lvl_output_ff_valid[" + str(2*(s+1)-1) + ":" + str(2*s) + "] <= 2'b00;"
			print "\t\t\tend"
			print "\n"
	else:
		for n in range(NUM_PES >> (i+1)): # find adder_ids in the lvl that can output to vn
			adder_vn.append(int(2**(i+1)*n+ 2**(i)-1))
			adder_vn.append(int(2**(i+1)*n+ 2**(i)-1)+1)	
		count = 0
		for s in range(NUM_PES):
			if (s not in adder_vn):
				print "\t\t\tr_lvl_output_ff[" + str((i*DATA_TYPE*NUM_PES)+(s+1)*DATA_TYPE-1) + ":" + str((i*DATA_TYPE*NUM_PES)+s*DATA_TYPE) + "] <= r_lvl_output_ff[" + str(((i-1)*DATA_TYPE*NUM_PES)+(s+1)*DATA_TYPE-1) + ":" + str(((i-1)*DATA_TYPE*NUM_PES)+s*DATA_TYPE) + "];"
				print "\t\t\tr_lvl_output_ff_valid[" + str((i*NUM_PES)+s) + "] <= r_lvl_output_ff_valid[" + str((i-1)*NUM_PES+s) + "];"
			else:
				print "\t\t\tif (w_vn_lvl_" + str(i) + "_valid[" + str(count) + "] == 1'b1) begin"
				print "\t\t\t\tr_lvl_output_ff[" + str((i*DATA_TYPE*NUM_PES)+(s+1)*DATA_TYPE-1) + ":" + str((i*DATA_TYPE*NUM_PES)+s*DATA_TYPE) + "] <= w_vn_lvl_" + str(i) + "[" + str(DATA_TYPE * (count+1) -1) + ":" + str(DATA_TYPE * count) + "];"
				print "\t\t\t\tr_lvl_output_ff_valid[" + str((i*NUM_PES)+s) + "] <= 1'b1;"
				print "\t\t\tend else begin"
				print "\t\t\t\tr_lvl_output_ff[" + str((i*DATA_TYPE*NUM_PES)+(s+1)*DATA_TYPE-1) + ":" + str((i*DATA_TYPE*NUM_PES)+s*DATA_TYPE) + "] <= r_lvl_output_ff[" + str(((i-1)*DATA_TYPE*NUM_PES)+(s+1)*DATA_TYPE-1) + ":" + str(((i-1)*DATA_TYPE*NUM_PES)+s*DATA_TYPE) + "];"
				print "\t\t\t\tr_lvl_output_ff_valid[" + str((i*NUM_PES)+s) + "] <= r_lvl_output_ff_valid[" + str((i-1)*NUM_PES+s) + "];"
				print "\t\t\tend"
				count = count + 1
			print "\n"
	print "\t\tend"
	print "\tend"
	print "\n"

	
##########################################################
# Flop input valid for different level of the adder tree
##########################################################
print "\t// Flop input valid for different level of the adder tree"
print "\talways @ (*) begin"
print "\t\tif (i_valid == 1'b1) begin"
print "\t\t\tr_valid[0] <= 1'b1;"
print "\t\tend else begin"
print "\t\t\tr_valid[0] <= 1'b0;"
print "\t\tend"
print "\tend\n"

print "\tgenvar i;"
print "\tgenerate"
print "\t\tfor (i=0; i < " + str(LOG2_PES + 1) + "; i=i+1) begin"
print "\t\t\talways @ (posedge clk) begin"
print "\t\t\t\tif (rst == 1'b1) begin"
print "\t\t\t\t\tr_valid[i+1] <= 1'b0;"
print "\t\t\t\tend else begin"
print "\t\t\t\t\tr_valid[i+1] <= r_valid[i];"
print "\t\t\t\tend"
print "\t\t\tend"
print "\t\tend"
print "\tendgenerate\n"


##########################################################
# Instantiate Adder Switches 
##########################################################

print "\t// Instantiating Adder Switches"
for adderID in range(NUM_PES - 1):
	lvl = get_lvl(adderID)
	WIRE_IN = get_wire_in(adderID)
	SEL_IN = get_sel_in(adderID)
	
	if (is_edge(adderID) == "true"): # edge adder (1 output)
		print "\n\tedge_adder_switch #("
	else : # regular adder (2 outputs)
		print "\n\tadder_switch #("
		
	print "\t\t.DATA_TYPE(", DATA_TYPE, "),"
	print "\t\t.NUM_IN(", WIRE_IN, "),"
	
	if (SEL_IN == 0) : # Switch needs to be hardcoded
		print "\t\t.SEL_IN(", 2 , ")) my_adder_" + str(adderID) + " ("
	else:
		print "\t\t.SEL_IN(", SEL_IN, ")) my_adder_" + str(adderID) + " ("	
		
	print "\t\t.clk(clk),"
	print "\t\t.rst(rst),"
	print "\t\t.i_valid(r_valid[" + str(lvl) +"]),"

	if (lvl == 0): # first level adders, get inputs from multipliers (i_data_bus)
		print "\t\t.i_data_bus(i_data_bus[" + str((adderID + 2)*DATA_TYPE -1) + " : " + str((adderID)*DATA_TYPE) + "]),"
	else: # following level adders, get inputs from previous adder outputs
		FAN_WIRE_IN = get_fan_wire_in(adderID)
		print "\t\t.i_data_bus(" + str(FAN_WIRE_IN)  + "),"

	print "\t\t.i_add_en(i_add_en_bus" + get_adder_en_id(adderID) + "),"
	print "\t\t.i_cmd(i_cmd_bus" + get_cmd_range(adderID) + "),"

	if (lvl <= 1):
		print "\t\t.i_sel(2'b00),"
	else:
		print "\t\t.i_sel(i_sel_bus" + get_sel_region(adderID) + "),"

	print "\t\t.o_vn(" +  get_vn_out(adderID) + "),"
	print "\t\t.o_vn_valid(" + get_vn_out_valid(adderID) + "),"
	print "\t\t.o_adder(" + get_fan_out(adderID) + ")"
	print "\t);"	

print "\n"
	
##########################################################
# Assigning output bus (with correct timing and final adder mux)
##########################################################
# Flop last level adder cmd for timing matching
print "\t// Flop last level adder cmd for timing matching"
print "\talways @ (posedge clk) begin"
print "\t\tif (rst == 1'b1) begin"
print "\t\t\tr_final_add <= 'd0;"
print "\t\t\tr_final_add2 <= 'd0;"
print "\t\t\tr_final_sum <= 'd0;"
print "\t\tend else begin"
print "\t\t\tr_final_add <= i_add_en_bus[" + str((NUM_PES-1)-1) + "];"
print "\t\t\tr_final_add2 <= r_final_add;"
print "\t\t\tr_final_sum <= w_fan_lvl_" + str(LOG2_PES-1) + ";"
print "\t\t\tend"
print "\tend"
print "\n"



print "\t// Assigning output bus (with correct timing and final adder mux)"
print "\talways @ (*) begin"
print "\t\tif (rst == 1'b1) begin"
print "\t\t\to_data_bus <= 'd0;"
print "\t\tend else begin"
print "\t\t\to_data_bus[" + str(NUM_PES/2*DATA_TYPE-DATA_TYPE-1) + ":0] <= r_lvl_output_ff[" + str(NUM_PES*DATA_TYPE*(LOG2_PES-1)+NUM_PES/2*DATA_TYPE-DATA_TYPE-1) + ":" + str(NUM_PES*DATA_TYPE*(LOG2_PES-1)) + "];"
print "\t\t\tif (r_final_add2 == 1'b1) begin" # adding
print "\t\t\t\to_data_bus[" + str(NUM_PES/2*DATA_TYPE-1) + ":" + str(NUM_PES/2*DATA_TYPE-DATA_TYPE) + "] <= r_final_sum;"
print "\t\t\tend else begin"
print "\t\t\t\to_data_bus[" + str(NUM_PES/2*DATA_TYPE-1) + ":" + str(NUM_PES/2*DATA_TYPE-DATA_TYPE) + "] <= r_lvl_output_ff[" + str(NUM_PES*DATA_TYPE*(LOG2_PES-1)+NUM_PES/2*DATA_TYPE-1) + ":" + str(NUM_PES*DATA_TYPE*(LOG2_PES-1)+NUM_PES/2*DATA_TYPE-DATA_TYPE) + "];"
print "\t\t\tend"
print "\t\t\to_data_bus[" + str(NUM_PES*DATA_TYPE-1) + ":" + str(NUM_PES/2*DATA_TYPE) + "] <= r_lvl_output_ff[" + str(NUM_PES*DATA_TYPE*LOG2_PES-1) + ":" + str(NUM_PES*DATA_TYPE*(LOG2_PES-1)+NUM_PES/2*DATA_TYPE) + "];" 
print "\t\tend"
print "\tend"
print "\n"

##########################################################
# Assigning output valid (with correct timing and final adder mux)
##########################################################

# Assignment
print "\t// Assigning output valid (with correct timing and final adder mux)"
print "\talways @ (*) begin"
print "\t\tif (rst == 1'b1 || r_valid[" + str(LOG2_PES + 1) + "] == 1'b0) begin"
print "\t\t\to_valid <= 'd0;"
print "\t\tend else begin"
print "\t\t\to_valid[" + str(NUM_PES/2-2) + ":0] <= r_lvl_output_ff_valid[" + str(NUM_PES*(LOG2_PES-1)+NUM_PES/2-1) + ":" + str(NUM_PES*(LOG2_PES-1)) + "];"
print "\t\t\tif (r_final_add2 == 1'b1) begin" # adding
print "\t\t\t\to_valid[" + str(NUM_PES/2-1) + "] <= 1'b1 ;"
print "\t\t\tend else begin"
print "\t\t\t\to_valid[" + str(NUM_PES/2-1) + "] <= r_lvl_output_ff_valid[" + str(NUM_PES*(LOG2_PES-1)+NUM_PES/2-1) + "];"
print "\t\t\tend"
print "\t\t\to_valid[" + str(NUM_PES-1) + ":" + str(NUM_PES/2) + "] <= r_lvl_output_ff_valid[" + str(NUM_PES*LOG2_PES-1) + ":" + str(NUM_PES*(LOG2_PES-1)+NUM_PES/2) + "];" 
print "\t\tend"
print "\tend"
print "\n"

	
print "endmodule"



