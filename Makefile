PYTHON2 = /usr/bin/python
MV = mv
CP = cp
MKDIR = mkdir -p
RM = rm -rf
CD = cd

ROOT = .

GEN_VMOD_DIR = $(ROOT)/gen_vmod
VMOD_DIR = $(ROOT)/vmod
GEN_TB_DIR = $(ROOT)/gen_tb
GEN_MATRIX_DIR = $(GEN_TB_DIR)/gen_matrix
TB_DIR = $(ROOT)/tb
TEST_DIR = $(ROOT)/test

.PHONY: test dve fan clean

test: fan
	$(MKDIR) test
	$(CP) $(VMOD_DIR)/* $(TEST_DIR)
	$(CP) $(TB_DIR)/tb_sigma_gen.sv $(TEST_DIR)
	$(CP) filelist.f $(TEST_DIR)
	$(CD) test
	vcs -sverilog -debug_all -full64 -f filelist.f +v2k +neg_tchk -l run.log -cpp /usr/bin/g++ ;

dve :
	./simv
	dve -full64 -vpd *.vpd

fan:
	$(CP) parameters.py $(GEN_VMOD_DIR) 
	$(CP) parameters.py $(GEN_TB_DIR)
	$(CP) parameters.py $(GEN_MATRIX_DIR)
	$(PYTHON2) $(GEN_VMOD_DIR)/flexdpe_gen.py > $(VMOD_DIR)/flexdpe.v
	$(PYTHON2) $(GEN_VMOD_DIR)/fan_gen.py > $(VMOD_DIR)/fan_network.v
	$(PYTHON2) $(GEN_VMOD_DIR)/ctrl_gen.py > $(VMOD_DIR)/fan_ctrl.v
	$(PYTHON2) $(GEN_TB_DIR)/tb_sigma_gen.py > $(TB_DIR)/tb_sigma_gen.sv

clean:
	$(RM) $(GEN_VMOD_DIR)/*pyc  $(GEN_TB_DIR)/*pyc $(GEN_VMOD_DIR)/out.txt $(GEN_VMOD_DIR)/tags $(TEST_DIR) run.log simv* csrc ucli.key DVE* ./out_dump.txt *vpd *pyc
