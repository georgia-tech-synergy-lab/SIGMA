#!/usr/bin/python 
import math
from parameters import *
from general_func import *

##########################################################
# Specific functions for generating Fan topology RTL
# Author: Eric Qin
# Contact: ecqin@gatech.edu
##########################################################


##########################################################
# FUNCTIONS FOR INSTANTIATING NEEDED INTERNAL WIRES
##########################################################

DATA_TYPE = OUT_DATA_TYPE # (FAN topology uses FP32 reduction)

# get number of binary tree wires per level
def get_binary_fwd_wires(lvl):
	if ( (NUM_PES >> (lvl+1))  > 2):
		num_tree_wire = ( (NUM_PES >> (lvl+1)) - 2)*2 + 2 # due to 2 edge adders
	else:
		num_tree_wire = ((NUM_PES >> (lvl+1)))
	return num_tree_wire

# Number of fwd links from src to dest
def get_num_fwd_links(lvl_src, lvl_dest):
	sub = 0 # subtract previous flops
	for s in range(lvl_dest - lvl_src - 2): # final dest lvl - src lvl
		sub = sub + (NUM_PES >> (s+2+lvl_src));  # sub depends on num_pes, s, and lvl_src 
	num_links = ((NUM_PES >> (lvl_src+1))-2) - int(sub) 
	return num_links

# Width of the fwd links from src to dest
def get_fwd_links_width(lvl_src, lvl_dest):
	num_links = get_num_fwd_links(lvl_src, lvl_dest)
	return int(DATA_TYPE * num_links)


##########################################################
# CONNECTING INTERNAL FAN TOPOLOGY FLIP FLOPS FOR TIMING
##########################################################

# to index r_fan_ff_lvl_X_to_Y from previous r_fan_ff_lvl_X_to_Y
def get_ff_fwd_index(lvl_src, lvl_dest, n):
	num_wire = 4*((NUM_PES / 2**lvl_dest)-1) + 2 # find # of wires from the previous fan ff level
	section = int(math.floor(n/2)) 
	value =  (2 + 4*section) * DATA_TYPE + ((n%2) * DATA_TYPE) 
	return "[" + str(value+DATA_TYPE-1) + ":" + str(value) + "];"

# to index r_fan_ff_lvl_X_to_Y from adder at previous level
def get_ff_adder_index(lvl_src, lvl_dest, n):
	skips = int(math.ceil((n+1)/2.0))
	id_max = (skips*2+n+1)*DATA_TYPE - 1
	id_min = (skips*2+n)*DATA_TYPE
	return "[" + str(id_max) + ":" + str(id_min) + "];"


##########################################################
# FUNCTIONS FOR FINDING FWD WIRE CONNECTIVITY
##########################################################	

# get correct wire inputs to each adder (fwd and regular wires)
def get_fan_wire_in(adderID):
	lvl = get_lvl(adderID)
	wire_in = "}"

	# left side logic
	for i in range(lvl): # input wires from the left side
		if (i == 0): # if it is leftmost wire (not latched from previous level) and append
			l_tree_region =  str( int(math.ceil(adderID >> (lvl-1)) + 0)*DATA_TYPE - 1 ) + ":" + str( int(math.ceil(adderID >> (lvl-1)) - 1)*DATA_TYPE )
			wire_in = " w_fan_lvl_" + str(lvl-1)  + "[" + l_tree_region + "]"	+ wire_in	
		else: # calculate regions of fwding input wire and append
			max_range = int(math.ceil(adderID >> (lvl-1)) + 0)*DATA_TYPE - 1
			min_range = max_range - (DATA_TYPE -1)
			l_fwd_region = str(max_range) + ":" + str(min_range)
			wire_in =  " r_fan_ff_lvl_" + str(lvl-i-1) + "_to_" + str(lvl)  + "[" + l_fwd_region + "]," + wire_in

	# right side logic
	for i in range(lvl-1,-1,-1): # input wires from the right side
		if (i == 0): # if it is rightmost wire (not latched from previous level) and append
			r_tree_region =  str( int(math.ceil(adderID >> (lvl-1)) + 1)*DATA_TYPE - 1 ) + ":" + str( int(math.ceil(adderID >> (lvl-1)) + 0)*DATA_TYPE )
			wire_in = " w_fan_lvl_" + str(lvl-1)  + "[" + r_tree_region + "]," +  wire_in 
		else: # calculate regions of fwding input wire and append 
			max_range = int(math.ceil(adderID >> (lvl-1)) + 1)*DATA_TYPE - 1
			min_range = max_range - (DATA_TYPE -1 )
			r_fwd_region = str(max_range) + ":" + str(min_range)
			wire_in = " r_fan_ff_lvl_" + str(lvl-i-1) + "_to_" + str(lvl)  + "[" + r_fwd_region + "]," + wire_in

	wire_in = "{" + wire_in  
	return wire_in


##########################################################
# FUNCTIONS FOR VN OUT AND ADDER OUT
##########################################################	

# match correct output vn wires to the corresponding adders
def get_vn_out(adderID):
	lvl = get_lvl(adderID)
	shift = get_adder_lvl_shift(adderID)
	return "w_vn_lvl_" + str(lvl) + "[" + str(int((2*shift+2)*DATA_TYPE  -1 ))+ " : " + str(int(2*shift*DATA_TYPE))  + "]"

# match correct output vn wires to the corresponding adders
def get_vn_out_valid(adderID):
	lvl = get_lvl(adderID)
	shift = get_adder_lvl_shift(adderID)
	return "w_vn_lvl_" + str(lvl) + "_valid[" + str(int((2*shift+2)  -1 ))+ " : " + str(int(2*shift))  + "]"

# match correct regular output wires to the corresponding adders
def get_fan_out(adderID):
	lvl = get_lvl(adderID)
	shift = get_adder_lvl_shift(adderID)
	if (lvl == LOG2_PES -1): # last level adder logic
		return "w_fan_lvl_" + str(lvl) + "[" + str(DATA_TYPE  -1 )+ " : " + str(0)  + "]"
	elif ((NUM_PES-1)-adderID < 2**(lvl+1)): # last edge adder of lvl
		return "w_fan_lvl_" + str(lvl) + "[" + str(int((2*shift)*DATA_TYPE  -1 ))+ " : " + str(int((2*shift-1)*DATA_TYPE))  + "]"
	elif (adderID < 2**(lvl+1)): # first edge adder of lvl
		return "w_fan_lvl_" + str(lvl) + "[" + str(int((shift+1)*DATA_TYPE  -1 ))+ " : " + str(int(shift*DATA_TYPE))  + "]"
	else: # everything else 
		return "w_fan_lvl_" + str(lvl) + "[" + str(int((2*shift+1)*DATA_TYPE  -1 ))+ " : " + str(int((2*shift-1)*DATA_TYPE))  + "]"
	
	
	
