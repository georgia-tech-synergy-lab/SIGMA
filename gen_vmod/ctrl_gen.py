#!/usr/bin/python 
import math
from ctrl_func import *

##########################################################
print "//##########################################################"
print "// Generated Fowarding Adder Network Controller (FAN topology routing)"
print "// Author: Eric Qin"
print "// Contact: ecqin@gatech.edu"
print "//##########################################################\n\n"
##########################################################


##########################################################
# Generating module initization and input/output ports
##########################################################

print "module fan_ctrl # ("
print "\tparameter DATA_TYPE = ", OUT_DATA_TYPE, ","
print "\tparameter NUM_PES = ", NUM_PES, ","
print "\tparameter LOG2_PES = ", LOG2_PES, ") ("
print "\tclk,"
print "\trst,"
print "\ti_vn," # different partial sum bit seperator
print "\ti_stationary," # determine if input is for stationary or streaming 
print "\ti_data_valid," # if input data is valid or not
print "\to_reduction_add," # if adder needs to add
print "\to_reduction_cmd," # reduction command (VN outputs)
print "\to_reduction_sel," # reduction select for the N-2 muxes
print "\to_reduction_valid" # if reduction output from FAN is valid or not
print ");" 

print "\tinput clk;"
print "\tinput rst;"
print "\tinput [NUM_PES*LOG2_PES-1: 0] i_vn; // different partial sum bit seperator"
print "\tinput i_stationary; // if input data is for stationary or streaming"
print "\tinput i_data_valid; // if input data is valid or not"
print "\toutput reg [(NUM_PES-1)-1:0] o_reduction_add; // determine to add or not"
print "\toutput reg [3*(NUM_PES-1)-1:0] o_reduction_cmd; // reduction command (for VN commands)"
NUM_SEL_BITS = get_sel_bits()
print "\toutput reg [" + str(int(NUM_SEL_BITS- 1)) + " : 0] o_reduction_sel; // select bits for FAN topology"
print "\toutput reg o_reduction_valid; // if reduction output from FAN is valid or not\n"


##########################################################
# Generate wire and reg declarations 
##########################################################

# not flopped cmd and sel signals
print "\t// reduction cmd and sel control bits (not flopped for timing yet)"
print "\treg [(NUM_PES-1)-1:0] r_reduction_add;"
print "\treg [3*(NUM_PES-1)-1:0] r_reduction_cmd;"
print "\treg [" + str(int(NUM_SEL_BITS - 1)) + " : 0] r_reduction_sel;"
print "\n"

# diagonal flops for timing leveling (adder en signal)
print "\t// diagonal flops for timing fix across different levels in tree (add_en signal)"
for i in range(LOG2_PES):
	add_max_range = get_adder_lvl(i)
	print "\treg [" + str(add_max_range) + " : 0] r_add_lvl_" +  str(i) + ";"
print "\n"

# diagonal flops for timing leveling (cmd signal)
print "\t// diagonal flops for timing fix across different levels in tree (cmd signal)"
for i in range(LOG2_PES):
	max_range = get_cmd_lvl(i)
	print "\treg [" + str(max_range) + " : 0] r_cmd_lvl_" +  str(i) + ";"
print "\n"
	
# diagonal flops for timing leveling (sel signal)
print "\t// diagonal flops for timing fix across different levels in tree (sel signal)"
for i in range(LOG2_PES-2):
	max_range = get_sel_lvl(i+2) # plus two as first two levels do not need sel
	print "\treg [" + str(max_range) + " : 0] r_sel_lvl_" +  str(i+2) + ";"
print "\n"


# timing alignment signals for i_vn delay and for output valid
VALID_DELAY = 4 # test which value works for timing alignment
CMD_SEL_DELAY = 2 # test which value works for timing alignment
print "\t// timing alignment for i_vn delay and for output valid"
print "\treg [" + str(CMD_SEL_DELAY) + "*NUM_PES*LOG2_PES-1:0] r_vn;"
print "\treg [NUM_PES*LOG2_PES-1:0] w_vn;"
print "\treg [" + str(VALID_DELAY) + " : 0 ] r_valid;" 
print "\n"

##########################################################
# Generate FF for i_vn cycle delays
##########################################################

print "\tgenvar i, x;;"
# add flip flops to delay i_vn
print "\t// add flip flops to delay i_vn"
print "\tgenerate"
print "\t\tfor (i=0; i < " + str(CMD_SEL_DELAY) + "; i=i+1) begin : vn_ff"
print "\t\t\tif (i == 0) begin: pass"
print "\t\t\t\talways @ (posedge clk) begin"
print "\t\t\t\t\tif (rst == 1'b1) begin"
print "\t\t\t\t\t\tr_vn[(i+1)*NUM_PES*LOG2_PES-1:i*NUM_PES*LOG2_PES] <= 'd0;"
print "\t\t\t\t\tend else begin"
print "\t\t\t\t\t\tr_vn[(i+1)*NUM_PES*LOG2_PES-1:i*NUM_PES*LOG2_PES] <= i_vn;"
print "\t\t\t\t\tend"
print "\t\t\t\tend"
print "\t\t\tend else begin: flop"
print "\t\t\t\talways @ (posedge clk) begin"
print "\t\t\t\t\tif (rst == 1'b1) begin"
print "\t\t\t\t\t\tr_vn[(i+1)*NUM_PES*LOG2_PES-1:i*NUM_PES*LOG2_PES] <= 'd0;"
print "\t\t\t\t\tend else begin"
print "\t\t\t\t\t\tr_vn[(i+1)*NUM_PES*LOG2_PES-1:i*NUM_PES*LOG2_PES] <= r_vn[i*NUM_PES*LOG2_PES-1:(i-1)*NUM_PES*LOG2_PES];"
print "\t\t\t\t\tend"
print "\t\t\t\tend"
print "\t\t\tend"
print "\t\tend"
print "\tendgenerate\n"
# assign last flop to w_vn
print "\t// assign last flop to w_vn"
print "\talways @(*) begin"
print "\t\tw_vn = r_vn[" + str(CMD_SEL_DELAY) + "*NUM_PES*LOG2_PES-1:" + str(CMD_SEL_DELAY-1) + "*NUM_PES*LOG2_PES];" 
print "\tend"
print "\n"


##########################################################

##########################################################



##########################################################
# Controller Logic to Compute CMD and SEL bits for each adder
##########################################################

for i in range(LOG2_PES):
	print "\t// generating control bits for lvl: " + str(i)
	if ( i < LOG2_PES -1): 
		print "\t// Note: lvl 0 and 1 do not require sel bits"
		print "\tgenerate"
		print "\t\tfor (x=0; x < " + str(NUM_PES >> (i+1)) + "; x=x+1) begin: adders_lvl_" + str(i)
		############################################### LEFT CASE ###########################################
		print "\t\t\tif (x == 0) begin: l_edge_case"
		print "\t\t\t\talways @ (*) begin"
		print "\t\t\t\t\tif (rst == 1'b1) begin"
		print "\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) + "+x] = 'd0;"
		print "\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 'd0;"
		if (i > 1): # need select logic for level 2 and over
			print "\t\t\t\t\t\t"  + generate_sel_range(i, "full") + " = 'd0;"
		print "\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t// generate cmd logic"
		print "\t\t\t\t\t\tif (r_valid[" + str(CMD_SEL_DELAY-1) + "] == 1'b1) begin"
		print "\t\t\t\t\t\t\tif (" + generate_lvl_wn_range(i, "add", "left") + ") begin"
		print "\t\t\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) + "+x] = 1'b1; // add enable"
		print "\t\t\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) + "+x] = 1'b0;"
		print "\t\t\t\t\t\t\tend"
		print "\n"
		print "\t\t\t\t\t\t\tif (" + generate_lvl_wn_range(i, "bothpass", "left") +  ") begin"
		print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b101; // both vn done"
		if (i > 0):
			print "\t\t\t\t\t\t\tend else if (" + generate_lvl_wn_range(i, "rightpass", "middle") + ") begin"
			print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b100; // right vn done"
			print "\t\t\t\t\t\t\tend else if (" + generate_lvl_wn_range(i, "leftpass", "left") + ") begin"
			print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b011; // left vn done"				
		else:	
			print "\t\t\t\t\t\t\tend else if (" + generate_lvl_wn_range(i, "leftpass", "left") + ") begin"
			print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b011; // left vn done"
		print "\t\t\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b000; // nothing"
		print "\t\t\t\t\t\t\tend"
		print "\t\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) + "+x] = 1'b0;"
		print "\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b000; // nothing"
		print "\t\t\t\t\t\tend\n"
		if (i > 1): # need select logic
			print "\t\t\t\t\t\t// generate left select logic"
			print "\t\t\t\t\t\tif (r_valid[" + str(CMD_SEL_DELAY-1) + "] == 1'b1) begin"
			print generate_sel_statement(i, "left", "no")
			print "\t\t\t\t\t\tend else begin"
			print generate_sel_statement(i, "left", "yes")
			print "\t\t\t\t\t\tend\n"
			print "\n\t\t\t\t\t\t// generate right select logic"
			print "\t\t\t\t\t\tif (r_valid[" + str(CMD_SEL_DELAY-1) + "] == 1'b1) begin"
			print generate_sel_statement(i, "right", "no")
			print "\t\t\t\t\t\tend else begin"
			print generate_sel_statement(i, "right", "yes")
			print "\t\t\t\t\t\tend\n"
		print "\t\t\t\t\tend"
		print "\t\t\t\tend"
		############################################### RIGHT CASE ###########################################
		print "\t\t\tend else if (x == " + str((NUM_PES >> (i+1)) -1 )  + ") begin: r_edge_case"
		print "\t\t\t\talways @ (*) begin"
		print "\t\t\t\t\tif (rst == 1'b1) begin"
		print "\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) +  "+x] = 'd0;"
		print "\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 'd0;"
		if (i > 1): # need select logic for level 2 and over
			print "\t\t\t\t\t\t" + generate_sel_range(i, "full") + " = 'd0;"	
		print "\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t// generate cmd logic"
		print "\t\t\t\t\t\tif (r_valid[" + str(CMD_SEL_DELAY-1) + "] == 1'b1) begin"
		print "\t\t\t\t\t\t\tif (" + generate_lvl_wn_range(i, "add", "right") + ") begin"
		print "\t\t\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) + "+x] = 1'b1; // add enable"
		print "\t\t\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) + "+x] = 1'b0;"
		print "\t\t\t\t\t\t\tend"
		print "\n"
		print "\t\t\t\t\t\t\tif (" + generate_lvl_wn_range(i, "bothpass", "right") + ") begin"
		print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b101; // both vn done"
		if (i > 0):
			print "\t\t\t\t\t\t\tend else if (" + generate_lvl_wn_range(i, "leftpass", "middle") + ") begin"
			print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b011; // left vn done"
			print "\t\t\t\t\t\t\tend else if (" + generate_lvl_wn_range(i, "rightpass", "right") + ") begin"
			print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b100; // right vn done"				
		else:	
			print "\t\t\t\t\t\t\tend else if (" + generate_lvl_wn_range(i, "rightpass", "right") + ") begin"
			print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b100; // right vn done"
		print "\t\t\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b000; // nothing"
		print "\t\t\t\t\t\t\tend\n"
		print "\t\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) + "+x] = 1'b0;"
		print "\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b000; // nothing"
		print "\t\t\t\t\t\tend\n"
		if (i > 1): # need select logic
			print "\t\t\t\t\t\t// generate left select logic"
			print "\t\t\t\t\t\tif (r_valid[" + str(CMD_SEL_DELAY-1) + "] == 1'b1) begin"
			print generate_sel_statement(i, "left", "no")
			print "\t\t\t\t\t\tend else begin"
			print generate_sel_statement(i, "left", "yes")
			print "\t\t\t\t\t\tend\n"
			print "\n\t\t\t\t\t\t// generate right select logic"
			print "\t\t\t\t\t\tif (r_valid[" + str(CMD_SEL_DELAY-1) + "] == 1'b1) begin"
			print generate_sel_statement(i, "right", "no")
			print "\t\t\t\t\t\tend else begin"
			print generate_sel_statement(i, "right", "yes")
			print "\t\t\t\t\t\tend\n"
		print "\t\t\t\t\tend"
		print "\t\t\t\tend"	
		############################################### NORMAL ###########################################
		print "\t\t\tend else begin: normal"
		print "\t\t\t\talways @ (*) begin"
		print "\t\t\t\t\tif (rst == 1'b1) begin"
		print "\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) +  "+x] = 'd0;"
		print "\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 'd0;"
		if (i > 1): # need select logic for level 2 and over
			print "\t\t\t\t\t\t"  + generate_sel_range(i, "full") + " = 'd0;"
		print "\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t// generate cmd logic"
		print "\t\t\t\t\t\tif (r_valid[" + str(CMD_SEL_DELAY-1) + "] == 1'b1) begin"
		print "\t\t\t\t\t\t\tif (" + generate_lvl_wn_range(i, "add", "middle") + ") begin"
		print "\t\t\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) + "+x] = 1'b1; // add enable"
		print "\t\t\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) + "+x] = 1'b0;"
		print "\t\t\t\t\t\t\tend"
		print "\n"
		print "\t\t\t\t\t\t\tif (" + generate_lvl_wn_range(i, "bothpass", "middle") + ") begin"
		print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b101; // both vn done"
		if (i > 0):
			print "\t\t\t\t\t\t\tend else if (" + generate_lvl_wn_range(i, "rightpass", "middle") + ") begin"
			print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b100; // right vn done"
			print "\t\t\t\t\t\t\tend else if (" + generate_lvl_wn_range(i, "leftpass", "middle") + ") begin"
			print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b011; // left vn done"				
		else:
			print "\t\t\t\t\t\t\tend else if (" + generate_lvl_wn_range(i, "rightpass", "middle") + ") begin"
			print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b100; // right vn done"
			print "\t\t\t\t\t\t\tend else if (" + generate_lvl_wn_range(i, "leftpass", "middle") + ") begin"
			print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b011; // left vn done"
		print "\t\t\t\t\t\t\tend else begin"
		if (i == 0): # bypass
			print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b001; // bypass"
		else: # no bypass needed
			print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b000; // nothing"
		print "\t\t\t\t\t\t\tend\n"
		print "\t\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) + "+x] = 1'b0;"
		print "\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b000; // nothing"
		print "\t\t\t\t\t\tend\n"
		if (i > 1): # need select logic
			print "\t\t\t\t\t\t// generate left select logic"
			print "\t\t\t\t\t\tif (r_valid[" + str(CMD_SEL_DELAY-1) + "] == 1'b1) begin"
			print generate_sel_statement(i, "left", "no") 
			print "\t\t\t\t\t\tend else begin"
			print generate_sel_statement(i, "left", "yes")
			print "\t\t\t\t\t\tend\n"
			print "\n\t\t\t\t\t\t// generate right select logic"
			print "\t\t\t\t\t\tif (r_valid[" + str(CMD_SEL_DELAY-1) + "] == 1'b1) begin"
			print generate_sel_statement(i, "right", "no")
			print "\t\t\t\t\t\tend else begin"
			print generate_sel_statement(i, "right", "yes")
			print "\t\t\t\t\t\tend\n"
		print "\t\t\t\t\tend"
		print "\t\t\t\tend"	
		print "\t\t\tend"
		print "\t\tend"
		print "\tendgenerate\n"
	############################################### LAST LEVEL ###########################################
	else: # last level
		print "\tgenerate"
		print "\t\tfor (x=0; x < " + str(NUM_PES >> (i+1)) + "; x=x+1) begin: adders_lvl_" + str(i)
		print "\t\t\tif (x == 0) begin: middle_case"
		print "\t\t\t\talways @ (*) begin"
		print "\t\t\t\t\tif (rst == 1'b1) begin"
		print "\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) +  "+x] = 'd0;"
		print "\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 'd0;"
		if (i > 1): # need select logic for level 2 and over
			print "\t\t\t\t\t\t"  + generate_sel_range(i, "full") + " = 'd0;"
		print "\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t// generate cmd logic"
		print "\t\t\t\t\t\tif (r_valid[" + str(CMD_SEL_DELAY-1) + "] == 1'b1) begin"
		print "\t\t\t\t\t\t\tif (" + generate_lvl_wn_range(i, "add", "last") + ") begin"
		print "\t\t\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) + "+x] = 1'b1; // add enable"
		print "\t\t\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) + "+x] = 1'b0;"
		print "\t\t\t\t\t\t\tend"
		print "\n"
		print "\t\t\t\t\t\t\tif (" + generate_lvl_wn_range(i, "bothpass", "last") + ") begin"
		print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b101; // both vn done"
		print "\t\t\t\t\t\t\tend else if (" + generate_lvl_wn_range(i, "rightpass", "last") + ") begin"
		print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b100; // right vn done"
		print "\t\t\t\t\t\t\tend else if (" + generate_lvl_wn_range(i, "leftpass", "last") + ") begin"
		print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b011; // left vn done"
		print "\t\t\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b000; // nothing"
		print "\t\t\t\t\t\t\tend\n"
		print "\t\t\t\t\t\tend else begin"
		print "\t\t\t\t\t\t\tr_reduction_add[" + get_cmd_shift_accum(i) + "+x] = 1'b0;"
		print "\t\t\t\t\t\t\tr_reduction_cmd[3*" + get_cmd_shift_accum(i) +  "+3*x+:3] = 3'b000; // nothing"
		print "\t\t\t\t\t\tend\n"
		if (i > 1): # need select logic
			print "\t\t\t\t\t\t// generate left select logic"
			print "\t\t\t\t\t\tif (r_valid[" + str(CMD_SEL_DELAY-1) + "] == 1'b1) begin"
			print generate_sel_statement(i, "left", "no")
			print "\t\t\t\t\t\tend else begin"
			print generate_sel_statement(i, "left", "yes")
			print "\t\t\t\t\t\tend\n"
			print "\n\t\t\t\t\t\t// generate right select logic"
			print "\t\t\t\t\t\tif (r_valid[" + str(CMD_SEL_DELAY-1) + "] == 1'b1) begin"
			print generate_sel_statement(i, "right", "no")
			print "\t\t\t\t\t\tend else begin"
			print generate_sel_statement(i, "right", "yes")
			print "\t\t\t\t\t\tend\n"
		print "\t\t\t\t\tend"
		print "\t\t\t\tend"
		print "\t\t\tend"
		print "\t\tend"
		print "\tendgenerate\n"


print "\n"

##########################################################
# Generate diagonal flops cmd/sel timing alignment
##########################################################

# flops to adjust for timing
print "\t// generate diagonal flops for cmd and sel timing alignment"
print "\talways @ (posedge clk) begin"
print "\t\tif (rst == 1'b1) begin"
for i in range(LOG2_PES):
	print "\t\t\tr_add_lvl_" +  str(i) + " <= 'd0;"
print "\n"
for i in range(LOG2_PES):
	print "\t\t\tr_cmd_lvl_" +  str(i) + " <= 'd0;"
print "\n"
for i in range(LOG2_PES-2):
	print "\t\t\tr_sel_lvl_" + str(i+2) + " <= 'd0;"
print "\t\tend else begin"
for i in range(LOG2_PES):
	num_adder = num_adders_in_lvl(i)
	for j in range(i+1):
		if (j == 0):
			print "\t\t\tr_add_lvl_" + str(i) + "[" + str(num_adder-1) + ":0] <= r_reduction_add" + get_lvl_add_range(i) + ";"
		else:
			print "\t\t\tr_add_lvl_" + str(i) + "[" + str((j+1)*num_adder-1) + ":" + str(j*num_adder) + "] <= r_add_lvl_" + str(i) + "[" + str(j*num_adder-1) + ":" + str((j-1)*num_adder) + "];"
print "\n"
for i in range(LOG2_PES):
	num_adder = num_adders_in_lvl(i)
	for j in range(i+1):
		if (j == 0):
			print "\t\t\tr_cmd_lvl_" + str(i) + "[" + str(3*num_adder-1) + ":0] <= r_reduction_cmd" + get_lvl_cmd_range(i) + ";"
		else:
			print "\t\t\tr_cmd_lvl_" + str(i) + "[" + str((j+1)*3*num_adder-1) + ":" + str(j*3*num_adder) + "] <= r_cmd_lvl_" + str(i) + "[" + str(j*3*num_adder-1) + ":" + str((j-1)*3*num_adder) + "];"
print "\n"
for i in range(LOG2_PES-2):
	num_sel = num_sel_bits_in_lvl(i+2)
	for j in range(i+3):
		if (j == 0):
			print "\t\t\tr_sel_lvl_" + str(i+2) + "[" + str(num_sel-1) + ":0] <= r_reduction_sel" + get_lvl_sel_range(i+2) + ";"
		else:
			print "\t\t\tr_sel_lvl_" + str(i+2) + "[" + str((j+1)*num_sel-1) + ":" + str(j*num_sel) + "] <= r_sel_lvl_" + str(i+2) + "[" + str(j*num_sel-1) + ":" + str((j-1)*num_sel) + "];"

print "\t\tend" 
print "\tend"

print "\n"

##########################################################
# Assigning final outputs
##########################################################

# Adjust output valid timing and logic..
print "\t// Adjust output valid timing and logic"
print "\talways @ (posedge clk) begin"
print "\t\tif (i_stationary == 1'b0 && i_data_valid == 1'b1) begin"
print "\t\t\tr_valid[0] <= 1'b1;"
print "\t\tend else begin"
print "\t\t\tr_valid[0] <= 1'b0;"
print "\t\tend"
print "\tend\n"

print "\tgenerate"
print "\t\tfor (i=0; i < " + str(VALID_DELAY) + "; i=i+1) begin"
print "\t\t\talways @ (posedge clk) begin"
print "\t\t\t\tif (rst == 1'b1) begin"
print "\t\t\t\t\tr_valid[i+1] <= 1'b0;"
print "\t\t\t\tend else begin"
print "\t\t\t\t\tr_valid[i+1] <= r_valid[i];"
print "\t\t\t\tend"
print "\t\t\tend"
print "\t\tend"
print "\tendgenerate\n"

print "\talways @ (*) begin"
print "\t\tif (rst == 1'b1) begin"
print "\t\t\to_reduction_valid <= 1'b0;"
print "\t\tend else begin"
print "\t\t\to_reduction_valid <= r_valid[" + str(int(VALID_DELAY-1)) + "];"
print "\t\tend"
print "\tend\n"


# Assigning final outputs for both diagonal flopped cmd and sel
print "\t// assigning diagonally flopped cmd and sel"
print "\talways @ (posedge clk) begin"
print "\t\tif (rst == 1'b1) begin"
print "\t\t\to_reduction_add <= 'd0;"
print "\t\t\to_reduction_cmd <= 'd0;"
print "\t\t\to_reduction_sel <= 'd0;"
print "\t\tend else begin"
print "\t\t\to_reduction_add <= " + gen_o_reduction_add(LOG2_PES, NUM_PES)
print "\t\t\to_reduction_cmd <= " + gen_o_reduction_cmd(LOG2_PES, NUM_PES)
print "\t\t\to_reduction_sel <= " + gen_o_reduction_sel(LOG2_PES, NUM_PES)
print "\t\tend"
print "\tend\n"


print "endmodule"






