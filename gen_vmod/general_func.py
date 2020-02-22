#!/usr/bin/python
import math
from parameters import *

##########################################################
# Basic function for generating FAN topology and controller
# Author: Eric Qin
# Contact: ecqin@gatech.edu 
##########################################################


##########################################################
# FUNCTIONS FOR FINDING THE POSITION OF A PARTICULAR ADDER
##########################################################

# determine the lvl of the specific AdderID (starts at lvl 0)
def get_lvl(adderID):
	lvl = 0
	if (adderID % 2 == 0):
		lvl = 0
		return lvl
	else:
		for i in range(LOG2_PES):
			if ((adderID + 1) % 2**i == 0):
				lvl = i
		return lvl

# determine adder shift in the particular level (starts at shift 0)
def get_adder_lvl_shift(adderID): 
	lvl = get_lvl(adderID)
	shift = math.floor(adderID/ (2**(lvl + 1)))
	return shift

# determine the adderID given the level and shift
def get_adder_id(lvl, shift):
	return int(2**(lvl+1)*shift + 2**(lvl)-1)

# determine number of adders in a particular adder tree level
def num_adders_in_lvl(i):
	return int(NUM_PES >> (i+1)) # level starts at 0
	
# determine if adder is an edge or regular adder
def is_edge(adderID):
	lvl = get_lvl(adderID)
	if (((NUM_PES-1)-adderID < 2**(lvl+1)) or (adderID < 2**(lvl+1))):
		return "true"
	else:
		return "false"

# adder number based on left to right, top to bottom
def get_adder_en_id(adderID):
	lvl = get_lvl(adderID)
	shift = get_adder_lvl_shift(adderID)
	num_adders = 0
	for i in range(lvl):
		num_adders = num_adders + (NUM_PES >> (i+1))
	total_adders = int(num_adders + shift)
	return "[" + str(total_adders) + "]"
		
		
##########################################################
# FUNCTIONS FOR THE SELECTION CONTROL BITS (N-to-2 MUXES)
##########################################################

# Total number of selection bits for all of the N-to-2 muxes
def get_sel_bits(): 
	num_sel = 0
	for i in range(LOG2_PES):
		if (i >= 2): # only from the second level onwards
			num_adders = 2**(LOG2_PES - i - 1)
			num_bits = 2 *  math.ceil(math.log(i, 2)) 
			num_sel = num_sel + (num_adders * num_bits)
	return int(num_sel)

# determine the number of wires leading to a specific adder switch
def get_wire_in(adderID):
	lvl = get_lvl(adderID)
	wire_in = 2 # default for all adders
	if (lvl > 1): # fwding starts at level 2 
		wire_in = 2*lvl
	return wire_in

#  # of sel bits required for a specific adder
def get_sel_in(adderID):
	wire_in = int(get_wire_in(adderID))
	one_side_sel_in = math.ceil(math.log(wire_in/2, 2))
	sel_in = one_side_sel_in * 2
	return int(sel_in)

# Determine # of sel bits for one adder in a particular adder tree level
def num_sel_bits_per_adder(i): 
	if (i == 0 or i == 1):
		return int(0)
	else:
		bits_per_side = math.ceil(math.log(i, 2))
		total_bits = 2 * bits_per_side
		return int(total_bits)

# Determine number of select bits in a particular adder tree level
def num_sel_bits_in_lvl(i): 
	return int(num_adders_in_lvl(i) * num_sel_bits_per_adder(i))

# get selection bit region for the specific adderID
def get_sel_region(adderID):
	lvl = get_lvl(adderID)
	sel_accum = 0
	if (lvl <= 1):
		return ""
	else:
		for i in range(lvl):
			if (i > 1):
				sel_accum = sel_accum + num_sel_bits_in_lvl(i)
			if (i == (int(lvl) - 1)):
				bits = get_sel_in(adderID)
				shift = get_adder_lvl_shift(adderID)
		return "[" + str( int(sel_accum) + int(bits*(shift+1)) - 1) + ":" + str(int(sel_accum) + int(bits*shift)) + "]"

# given a specific level, determine region of sel bits
def get_lvl_sel_range(lvl):
	start = 0
	end = 0
	for i in range(lvl):
		start = start + num_sel_bits_in_lvl(i)
	for i in range(lvl+1):
		end = end + num_sel_bits_in_lvl(i)
	return "[" + str(end-1) + ":" + str(start) + "]"

##########################################################
# FUNCTIONS FOR THE ADDER FUNCTIONALITY CMD CONTROL BITS
##########################################################

# Total number of cmd bits for all of the adders
def get_cmd_bits():
	return int(3*(NUM_PES-1))

# given adderID, determine cmd signal bus range
def get_cmd_range(adderID):
	lvl = get_lvl(adderID)
	shift = get_adder_lvl_shift(adderID)
	num_adders = 0
	for i in range(lvl):
		num_adders = num_adders + (NUM_PES >> (i+1))
	total_adders = int(num_adders + shift)
	return "[" + str(3*(total_adders+1)-1) + ":" + str(3*total_adders) + "]"

# given a specific level, determine region of cmd bits
def get_lvl_cmd_range(lvl):
	start_adder = 0
	end_adder = 0
	for i in range(lvl):
		start_adder = start_adder + (NUM_PES >> (i+1))
	for i in range(lvl+1):
		end_adder = end_adder + (NUM_PES >> (i+1))
	return "[" + str(int(end_adder*3-1)) + ":" + str(int(start_adder*3)) + "]"
		
# given a specific level, determine region of cmd bits
def get_lvl_add_range(lvl):
	start_adder = 0
	end_adder = 0
	for i in range(lvl):
		start_adder = start_adder + (NUM_PES >> (i+1))
	for i in range(lvl+1):
		end_adder = end_adder + (NUM_PES >> (i+1))
	return "[" + str(int(end_adder-1)) + ":" + str(int(start_adder)) + "]"



