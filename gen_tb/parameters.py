import math


# RTL Generation Parameters
IN_DATA_TYPE = 16 # FIXED
OUT_DATA_TYPE = 32 # FIXED
NUM_PES = 32
LOG2_PES = int(math.log(NUM_PES, 2))
DTOP = "xbar" # FIXED (Future work: connect Benes RTL)

# For Random Testbench Generation Parameters
FLEX_DPE_SIZE = NUM_PES # FIXED
FLEX_DPE_IN_BW = NUM_PES # FIXED
NUM_FLEX_DPE = 1 # FIXED (Future work: fix bugs)
M_DIM = 6
N_DIM = 4
K_DIM = 8
ZERO_RATIO_MK = 0.5
ZERO_RATIO_KN = 0.8

# Equal Macros Names
MK_SPARSE = ZERO_RATIO_MK
KN_SPARSE = ZERO_RATIO_KN

