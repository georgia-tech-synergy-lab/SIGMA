#!/usr/bin/python 
import math
from parameters import *
from general_func import *

##########################################################
# Specific functions for generating Fan controller RTL
# Author: Eric Qin
# Contact: ecqin@gatech.edu
##########################################################


##########################################################
# INSTANTIATE DIAGONAL FLOPS FOR CMD AND SEL TIMING
##########################################################

# Number of adder bits per lvl multiplied by the number of flops
def get_adder_lvl(i):
	adder_bits = 1
	max_range = (i+1)*adder_bits*(NUM_PES >> (i+1)) - 1
	return max_range

# Number of cmd bits per lvl multiplied by the number of flops
def get_cmd_lvl(i):
	cmd_bits = 3
	max_range = (i+1)*cmd_bits*(NUM_PES >> (i+1)) - 1
	return max_range
	
# Number of selection bits per lvl multiplied by the number of flops	
def get_sel_lvl(i): 
	num_adders = 2**(LOG2_PES - i - 1)
	num_bits = 2 *  math.ceil(math.log(i, 2)) 
	num_sel = int(num_adders * num_bits)	
	max_range = (i+1)*num_sel - 1
	return max_range
	

##########################################################
# FUNCTIONS TO FIND CMD AND SEL INDICIES 
##########################################################

# function to determine base cmd shift per level	
def get_cmd_shift_accum(i):
	sum = 0
	for l in range(i):
		sum = sum + (NUM_PES >> (l+1))
	return str(int(sum))

# function to determine the sel range per adder
def generate_sel_range(lvl, side):

	sum = 0
	for i in range(lvl):
		sum = sum + num_sel_bits_in_lvl(i)
	bits = num_sel_bits_per_adder(lvl)	
	side_bits = int(bits/2)
	
	if (side == "full"):
		return "r_reduction_sel[" + "(x*" + str(bits) + ")+" + str(sum) + "+:" + str(bits) + "]"
	elif (side == "left"):		
		return "r_reduction_sel[" + "(x*" + str(bits) + ")+" + str(sum) + "+:" + str(side_bits) + "]"	
	elif (side == "right"):
		return "r_reduction_sel[" + "(x*" + str(bits) + ")+" + str(sum+side_bits) + "+:" + str(side_bits) + "]" 
		
			
				
##########################################################
# FUNCTIONS TO GENERATE LEVEL SEL AND CMD LOGIC
##########################################################

# Generate correct w_vn comparison range for cmd generation at each adder level & position
def generate_lvl_wn_range(lvl, func, edge):

	# Starting shift value per level (accum)
	accum = 0
	for i in range(lvl+1):
		if (i > 0):
			accum = accum + 2**(i-1)
	
	# Comparison shift and bound value
	if (lvl == 0):
		shift = 0
		bound = 0
	else:
		shift = 2**(lvl-1)
		bound = 2**(lvl)
		

	a0 = "(" + str(2**(lvl+1)) + "*x+" + str(accum) + ")*LOG2_PES" 
	a1 = "(" + str(2**(lvl+1)) + "*x+" + str(accum+1) + ")*LOG2_PES" 

	l0 = "(" + str(2**(lvl+1)) + "*x+" + str(accum+1) + ")*LOG2_PES" 
	l1 = "(" + str(2**(lvl+1)) + "*x+" + str(accum+2) + ")*LOG2_PES" 
	r0 = "(" + str(2**(lvl+1)) + "*x+" + str(accum) + ")*LOG2_PES" 
	r1 = "(" + str(2**(lvl+1)) + "*x+" + str(accum-1) + ")*LOG2_PES"
	
	# For non-lvl-0
	a0_shift = "(" + str(2**(lvl+1)) + "*x+" + str(accum-shift) + ")*LOG2_PES" 
	a0_shift_plus = "(" + str(2**(lvl+1)) + "*x+" + str(accum+1-shift) + ")*LOG2_PES" 
	a1_shift = "(" + str(2**(lvl+1)) + "*x+" + str(accum+1+shift) + ")*LOG2_PES" 
	a1_shift_minus = "(" + str(2**(lvl+1)) + "*x+" + str(accum+shift) + ")*LOG2_PES"
	a0_bound = "(" + str(2**(lvl+1)) + "*x+" + str(accum-bound) + ")*LOG2_PES" 
	a1_bound = "(" + str(2**(lvl+1)) + "*x+" + str(accum+1+bound) + ")*LOG2_PES"

	if (lvl == 0):
		if (func == "add"):
			return "w_vn[" + str(a0) + "+:LOG2_PES] == w_vn[" + str(a1) + "+:LOG2_PES]"
				
		elif (func == "bothpass"):
			if (edge == "left"):
				return "w_vn[" + str(l0) + "+:LOG2_PES] != w_vn[" + str(l1) + "+:LOG2_PES] && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"
			elif (edge == "right"):
				return "w_vn[" + str(r0) + "+:LOG2_PES] != w_vn[" + str(r1) + "+:LOG2_PES] && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"
			elif (edge == "middle"):
				return "(w_vn[" + str(r0) + "+:LOG2_PES] != w_vn[" + str(r1) + "+:LOG2_PES]) && (w_vn[" + str(l0) + "+:LOG2_PES] != w_vn[" + str(l1) + "+:LOG2_PES]) && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"
					
		elif (func == "leftpass"):
			if (edge == "left"):
				return "w_vn[" + str(l0) + "+:LOG2_PES] == w_vn[" + str(l1) + "+:LOG2_PES] && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"
			elif (edge == "middle"):
				return "(w_vn[" + str(r0) + "+:LOG2_PES] != w_vn[" + str(r1) + "+:LOG2_PES]) && (w_vn[" + str(l0) + "+:LOG2_PES] == w_vn[" + str(l1) + "+:LOG2_PES]) && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"
					
		elif (func == "rightpass"):
			if (edge == "right"):
				return "w_vn[" + str(r0) + "+:LOG2_PES] == w_vn[" + str(r1) + "+:LOG2_PES] && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"
			elif (edge == "middle"):
				return "(w_vn[" + str(r0) + "+:LOG2_PES] == w_vn[" + str(r1) + "+:LOG2_PES]) && (w_vn[" + str(l0) + "+:LOG2_PES] != w_vn[" + str(l1) + "+:LOG2_PES]) && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"

	elif (lvl == 1):
		if (func == "add"):
			return "w_vn[" + str(a0) + "+:LOG2_PES] == w_vn[" + str(a1) + "+:LOG2_PES]"
				
		elif (func == "bothpass"):
			if (edge == "left"):
				return "(w_vn[" + str(a0_shift) + "+:LOG2_PES] == w_vn[" + str(a0_shift_plus) + "+:LOG2_PES]) && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] == w_vn[" + str(a1_shift) + "+:LOG2_PES]) && (w_vn[" + str(a1_bound) + "+:LOG2_PES] != w_vn[" + str(a1_shift) + "+:LOG2_PES]) && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"
			elif (edge == "right"):
				return "(w_vn[" + str(a0_shift) + "+:LOG2_PES] == w_vn[" + str(a0_shift_plus) + "+:LOG2_PES]) && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] == w_vn[" + str(a1_shift) + "+:LOG2_PES]) && (w_vn[" + str(a0_shift) + "+:LOG2_PES] != w_vn[" + str(a0_bound) + "+:LOG2_PES]) && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"
			elif (edge == "middle"):
				return "(w_vn[" + str(a0_shift) + "+:LOG2_PES] == w_vn[" + str(a0_shift_plus) + "+:LOG2_PES]) && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] == w_vn[" + str(a1_shift) + "+:LOG2_PES]) && (w_vn[" + str(a0_shift) + "+:LOG2_PES] != w_vn[" + str(a0_bound) + "+:LOG2_PES]) && (w_vn[" + str(a1_bound) + "+:LOG2_PES] != w_vn[" + str(a1_shift) + "+:LOG2_PES]) && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"

				
		elif (func == "leftpass"):
			if (edge == "left"):
				return "(w_vn[" + str(a0_shift) + "+:LOG2_PES] == w_vn[" + str(a0_shift_plus) + "+:LOG2_PES]) && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"
			elif (edge == "middle"):
				return "(w_vn[" + str(a0_shift) + "+:LOG2_PES] == w_vn[" + str(a0_shift_plus) + "+:LOG2_PES]) && (w_vn[" + str(a0_shift) + "+:LOG2_PES] != w_vn[" + str(a0_bound) + "+:LOG2_PES]) && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"
				
		elif (func == "rightpass"):
			if (edge == "right"):
				return "(w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] == w_vn[" + str(a1_shift) + "+:LOG2_PES]) && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"
			elif (edge == "middle"):
				return "(w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] == w_vn[" + str(a1_shift) + "+:LOG2_PES]) && (w_vn[" + str(a1_bound) + "+:LOG2_PES] != w_vn[" + str(a1_shift) + "+:LOG2_PES]) && w_vn[" + str(a0) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]"

	else:
		if (func == "add"):
			return "w_vn[" + str(a0) + "+:LOG2_PES] == w_vn[" + str(a1) + "+:LOG2_PES]"
				
		elif (func == "bothpass"):
			if (edge == "left"):
				return "(w_vn[" + str(a0_shift) + "+:LOG2_PES] == w_vn[" + str(a0_shift_plus) + "+:LOG2_PES]) && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] == w_vn[" + str(a1_shift) + "+:LOG2_PES]) && (w_vn[" + str(a1_bound) + "+:LOG2_PES] != w_vn[" + str(a1_shift) + "+:LOG2_PES]) && (w_vn[" + str(a0_shift_plus) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]) && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] != w_vn[" + str(a0) + "+:LOG2_PES])"
			elif (edge == "right"):
				return "(w_vn[" + str(a0_shift) + "+:LOG2_PES] == w_vn[" + str(a0_shift_plus) + "+:LOG2_PES]) && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] == w_vn[" + str(a1_shift) + "+:LOG2_PES]) && (w_vn[" + str(a0_shift) + "+:LOG2_PES] != w_vn[" + str(a0_bound) + "+:LOG2_PES]) && (w_vn[" + str(a0_shift_plus) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]) && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] != w_vn[" + str(a0) + "+:LOG2_PES])"
			elif (edge == "middle"):
				return "(w_vn[" + str(a0_shift) + "+:LOG2_PES] == w_vn[" + str(a0_shift_plus) + "+:LOG2_PES]) && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] == w_vn[" + str(a1_shift) + "+:LOG2_PES]) && (w_vn[" + str(a0_shift) + "+:LOG2_PES] != w_vn[" + str(a0_bound) + "+:LOG2_PES]) && (w_vn[" + str(a1_bound) + "+:LOG2_PES] != w_vn[" + str(a1_shift) + "+:LOG2_PES])  && (w_vn[" + str(a0_shift_plus) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]) && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] != w_vn[" + str(a0) + "+:LOG2_PES])"
			elif (edge == "last"):
				return "(w_vn[" + str(a0_shift) + "+:LOG2_PES] == w_vn[" + str(a0_shift_plus) + "+:LOG2_PES]) && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] == w_vn[" + str(a1_shift) + "+:LOG2_PES]) && (w_vn[" + str(a0_shift_plus) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES]) && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] != w_vn[" + str(a0) + "+:LOG2_PES])"
			
		elif (func == "leftpass"):
			if (edge == "left"):
				return "(w_vn[" + str(a0_shift) + "+:LOG2_PES] == w_vn[" + str(a0_shift_plus) + "+:LOG2_PES]) && (w_vn[" + str(a0_shift_plus) + "+:LOG2_PES] != w_vn[" + str(a1) + "+:LOG2_PES])"
			elif (edge == "middle"):
				return "(w_vn[" + str(a0_shift) + "+:LOG2_PES] == w_vn[" + str(a0_shift_plus) + "+:LOG2_PES]) && (w_vn[" + str(a0_shift) + "+:LOG2_PES] != w_vn[" + str(a0_bound) + "+:LOG2_PES]) && (w_vn[" + str(a1) + "+:LOG2_PES] != w_vn[" + str(a0_shift_plus) + "+:LOG2_PES])"	
			elif (edge == "last"):
				return "(w_vn[" + str(a0_shift) + "+:LOG2_PES] == w_vn[" + str(a0_shift_plus) + "+:LOG2_PES]) && (w_vn[" + str(a1) + "+:LOG2_PES] != w_vn[" + str(a0_shift_plus) + "+:LOG2_PES])"
										
		elif (func == "rightpass"):
			if (edge == "right"):
				return "(w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] == w_vn[" + str(a1_shift) + "+:LOG2_PES]) && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] != w_vn[" + str(a0) + "+:LOG2_PES])"
			elif (edge == "middle"):
				return "(w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] == w_vn[" + str(a1_shift) + "+:LOG2_PES]) && (w_vn[" + str(a1_bound) + "+:LOG2_PES] != w_vn[" + str(a1_shift) + "+:LOG2_PES])  && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] != w_vn[" + str(a0) + "+:LOG2_PES])"	
			elif (edge == "last"):
				return "(w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] == w_vn[" + str(a1_shift) + "+:LOG2_PES]) && (w_vn[" + str(a1_shift_minus) + "+:LOG2_PES] != w_vn[" + str(a0) + "+:LOG2_PES])"	

	
	
# Generate full select logic statements
def generate_sel_statement(lvl, side, reset):

	# Get starting point for w_vn comparisons
	accum = 0
	for i in range(lvl+1):
		if (i > 0):
			accum = accum + 2**(i-1)
			
	# Comparison offset by level and region
	if (lvl == 0):
		shift = 0
		bound = 0
	else:
		shift = 2**(lvl-1)
		bound = 2**(lvl)
	
	w0 = ""
	w1 = ""
	statement = ""
	side_input = lvl
	bits = int(math.ceil(math.log(side_input, 2)))
	
	for i in range(lvl):
	
		offset = 2**(lvl-i-1)
	
		left_start = "(" + str(2**(lvl+1)) + "*x+" + str(accum) + ")*LOG2_PES" 
		right_start = "(" + str(2**(lvl+1)) + "*x+" + str(accum+1) + ")*LOG2_PES" 
		left_end = "(" + str(2**(lvl+1)) + "*x+" + str(accum-offset) + ")*LOG2_PES" 
		right_end = "(" + str(2**(lvl+1)) + "*x+" + str(accum+1+offset) + ")*LOG2_PES" 
		sel_val = 0
		
		if (side == "left"):
			w0 = left_start
			w1 = left_end
			sel_val = i
		else:
			w0 = right_start
			w1 = right_end
			sel_val = (lvl-1-i)
		
		
		
		if (i == 0):
			start = "w_vn[" + str(w0) + "+:LOG2_PES]"
			end = "w_vn[" + str(w1) + "+:LOG2_PES]"
			statement = statement + "\t\t\t\t\t\t\tif (" + start +  " == " + end + ") begin"
			statement = statement + "\n\t\t\t\t\t\t\t\t" + str(generate_sel_range(lvl, side)) + " = 'd" + str(sel_val) + ";"
		elif (i == lvl -1):
			start = "w_vn[" + str(w0) + "+:LOG2_PES]"
			end = "w_vn[" + str(w1) + "+:LOG2_PES]"
			statement = statement + "\n\t\t\t\t\t\t\tend else begin"
			statement = statement + "\n\t\t\t\t\t\t\t\t" + str(generate_sel_range(lvl, side)) + " = 'd" + str(sel_val) + ";"
		else:
			start = "w_vn[" + str(w0) + "+:LOG2_PES]"
			end = "w_vn[" + str(w1) + "+:LOG2_PES]"
			statement = statement + "\n\t\t\t\t\t\t\tend else if (" + start +  " == " + end + ") begin"
			statement = statement + "\n\t\t\t\t\t\t\t\t" + str(generate_sel_range(lvl, side)) + " = 'd" + str(sel_val) + ";"
		
	statement = statement + "\n\t\t\t\t\t\t\tend" 
	
	if (reset == "yes"):
		return "\t\t\t\t\t\t\t" + str(generate_sel_range(lvl, "full")) + " = 'd0;"
	else:
		return statement


##########################################################
# IMPLEMENT DIAGONAL ADD, SEL AND CMD OUTPUT ASSIGNMENT 
##########################################################

def gen_o_reduction_add(LOG2_PES, NUM_PES):
	prefix = "{"
	text = ""
	for i in range(LOG2_PES):
		max_range = get_adder_lvl(i)
		if (i != 0):
			text = "r_add_lvl_" +  str(i) + "[" + str(max_range) + ":" + str(max_range+1 - (NUM_PES >> (i+1))) + "]," + text
		else:
			text = "r_add_lvl_" +  str(i) + "[" + str(max_range) + ":" + str(max_range+1 - (NUM_PES >> (i+1))) + text + "]};"
	return prefix + text
	

def gen_o_reduction_cmd(LOG2_PES, NUM_PES):
	prefix = "{"
	text = ""
	for i in range(LOG2_PES):
		max_range = get_cmd_lvl(i)
		if (i != 0):
			text = "r_cmd_lvl_" +  str(i) + "[" + str(max_range) + ":" + str(max_range+1 - 3*(NUM_PES >> (i+1))) + "]," + text
		else:
			text = "r_cmd_lvl_" +  str(i) + "[" + str(max_range) + ":" + str(max_range+1 - 3*(NUM_PES >> (i+1))) + text + "]};"
	return prefix + text
	
def gen_o_reduction_sel(LOG2_PES, NUM_PES):
	prefix = "{"
	text = ""
	for i in range(LOG2_PES):
		if (i != 0 and i != 1):
			max_range = get_sel_lvl(i) # Total including flops
			num_adders = 2**(LOG2_PES - i - 1)
			num_bits = 2 *  math.ceil(math.log(i, 2)) 
			num_sel = int(num_adders * num_bits)
			if (i != 2):
				text = "r_sel_lvl_" +  str(i) + "[" + str(max_range) + ":" + str(max_range+1 - num_sel) + "]," + text
			else:
				text = "r_sel_lvl_" +  str(i) + "[" + str(max_range) + ":" + str(max_range+1 - num_sel) + text + "]};"
	return prefix + text
	
	
	
