#!/usr/bin/python 
import math
from fan_func import *

print "`timescale 1ns / 1ps"
print "/////////////////////////////////////////////////////////////////////////\n"

print "// Design: flexdpe.v"
print "// Author: Eric Qin\n"

print "// Description: SIGMA Macro PE (FLEX-DPE) top level design\n"

print "/////////////////////////////////////////////////////////////////////////\n"

print "module flexdpe("
print "\tclk,"
print "\trst,"
print "\ti_data_valid, // input data bus valid"
print "\ti_data_bus, // input data bus"
print "\ti_stationary, // control bit signaling input data is stored in stationary buffer"
print "\ti_dest_bus, // dest bus for xbar network"
print "\ti_vn_seperator, // alternate virtual neuron seperator\n"

print "\to_data_valid, // valid data signals"
print "\to_data_bus // output data bus"
print ");\n"

print "\tparameter IN_DATA_TYPE = 16; // input data type width (BFP16)"
print "\tparameter OUT_DATA_TYPE = 32; // output data type width (FP32)"
print "\tparameter NUM_PES = " + str(NUM_PES) + "; // number of PES"
print "\tparameter LOG2_PES = " + str(LOG2_PES) + ";\n"

print "\tinput clk;"
print "\tinput rst;"
print "\tinput i_data_valid;"
print "\tinput [NUM_PES * IN_DATA_TYPE -1 : 0] i_data_bus;"
print "\tinput i_stationary;"
print "\tinput [NUM_PES * LOG2_PES -1:0] i_dest_bus;"
print "\tinput [NUM_PES * LOG2_PES -1:0] i_vn_seperator;\n"
	
print "\toutput [NUM_PES-1:0] o_data_valid;"
print "\toutput [NUM_PES * OUT_DATA_TYPE -1:0] o_data_bus;\n"
	
print "\twire [(NUM_PES-1)-1:0] w_reduction_add;"
print "\twire [3*(NUM_PES-1)-1:0] w_reduction_cmd;"
NUM_SEL_BITS = get_sel_bits()
print "\twire [" + str(NUM_SEL_BITS-1) + " : 0] w_reduction_sel;"
print "\twire w_reduction_valid;\n"

print "\treg [NUM_PES * OUT_DATA_TYPE -1: 0] r_mult;\n"


print "\twire [NUM_PES * IN_DATA_TYPE -1 : 0]  w_dist_bus; // output of xbar network"
print "\twire w_mult_valid;\n"

print "\treg [NUM_PES * IN_DATA_TYPE -1 : 0] r_data_bus_ff, r_data_bus_ff2;"
print "\treg r_data_valid_ff, r_data_valid_ff2;"
print "\treg r_stationary_ff, r_stationary_ff2;"
print "\treg [NUM_PES * LOG2_PES -1:0] r_dest_bus_ff, r_dest_bus_ff2;\n"


print "\t// adjust some input signal delays from xbar and controller"
print "\talways @ (posedge clk) begin"
print "\t\tr_data_bus_ff <= i_data_bus;"
print "\t\tr_data_bus_ff2 <= r_data_bus_ff;"
print "\t\tr_data_valid_ff <= i_data_valid; "
print "\t\tr_data_valid_ff2 <= r_data_valid_ff;"
print "\t\tr_stationary_ff <= i_stationary;"
print "\t\tr_stationary_ff2 <= r_stationary_ff;"
print "\t\tr_dest_bus_ff <= i_dest_bus;"
print "\t\tr_dest_bus_ff2 <= r_dest_bus_ff;"
print "\tend\n"


print "\t// instantize controller"
print "\tfan_ctrl #("
print "\t\t.DATA_TYPE(IN_DATA_TYPE),"
print "\t\t.NUM_PES(NUM_PES),"
print "\t\t.LOG2_PES(LOG2_PES))"
print "\t\tmy_controller("
print "\t\t.clk(clk),"
print "\t\t.rst(rst),"
print "\t\t.i_vn(i_vn_seperator),"
print "\t\t.i_stationary(i_stationary),"
print "\t\t.i_data_valid(i_data_valid),"
print "\t\t.o_reduction_add(w_reduction_add),"
print "\t\t.o_reduction_cmd(w_reduction_cmd),"
print "\t\t.o_reduction_sel(w_reduction_sel),"
print "\t\t.o_reduction_valid(w_reduction_valid)"
print "\t);\n"

print "\t// instantize distribution network  (can be xbar or benes)"
print "\txbar #("
print "\t\t.DATA_TYPE(IN_DATA_TYPE),"
print "\t\t.NUM_PES(NUM_PES),"
print "\t\t.INPUT_BW(NUM_PES),"
print "\t\t.LOG2_PES(LOG2_PES))"
print "\t\tmy_xbar ("
print "\t\t.clk(clk),"
print "\t\t.rst(rst),"
print "\t\t.i_data_bus(r_data_bus_ff2),"
print "\t\t.i_mux_bus(r_dest_bus_ff2),"
print "\t\t.o_dist_bus(w_dist_bus)"
print "\t);\n"
	

print "\t// generate multiplier chain (output of xbar to input of multiplier chain)"
print "\tmult_gen #("
print "\t\t.IN_DATA_TYPE(IN_DATA_TYPE),"
print "\t\t.OUT_DATA_TYPE(OUT_DATA_TYPE),"
print "\t\t.NUM_PES(NUM_PES))"
print "\t\tmy_mult_gen ("
print "\t\t.clk(clk),"
print "\t\t.rst(rst),"
print "\t\t.i_valid(r_data_valid_ff2),"
print "\t\t.i_data_bus(w_dist_bus),"
print "\t\t.i_stationary(r_stationary_ff2),"
print "\t\t.o_valid(w_mult_valid),"
print "\t\t.o_data_bus(r_mult)"
print "\t);\n"
	

print "\t// instantiate fan reduction topology"
print "\tfan_network #("
print "\t\t.DATA_TYPE(OUT_DATA_TYPE),"
print "\t\t.NUM_PES(NUM_PES),"
print "\t\t.LOG2_PES(LOG2_PES))"
print "\t\tmy_fan_network("
print "\t\t.clk(clk),"
print "\t\t.rst(rst),"
print "\t\t.i_valid(w_reduction_valid),"
print "\t\t.i_data_bus(r_mult),"
print "\t\t.i_add_en_bus(w_reduction_add),"
print "\t\t.i_cmd_bus(w_reduction_cmd),"
print "\t\t.i_sel_bus(w_reduction_sel),"
print "\t\t.o_valid(o_data_valid),"
print "\t\t.o_data_bus(o_data_bus)"
print "\t);\n"

print "endmodule"



