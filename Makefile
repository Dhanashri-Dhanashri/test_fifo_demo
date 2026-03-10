export FSDB_FAULT_DUMP_MODE=fm
export VERDI_FUSA_DEBUG=1
export VERDI_FUSA_DUMP_FSDB_CMD=./COLLATERAL/VERDI/dumping_v.sh

run_vc_zoix: vc_comp vc_fcm_exp 

run_zoix: z_comp z_fmsh

run_vc_fmdump: clean vc_comp  vc_fcm_exp vc_verdi vc_info 

clean:
	rm -rf sim.* fcm.dir* *.fsdb novas* *.log ucli* csrc fdb*  fgen* verdi* simv*  fcm_tsim_fsdb fcm_fsim_save


## VC-Z01X ##

vc_comp:
	vcs -f ./rtl.f ./src/strobe.sv -fsim=dut:test.DUT -kdb -lca -fsim=portfaults -debug_access -sverilog -full64 -l comp_v.log

vc_fcm_exp:
	vc_fcm -tcl_script ./COLLATERAL/FCM/fcm.tcl -connect 

## Z01X ##

z_comp:
	zoix -f ./rtl.f ./src/strobe.sv -kdb -lca +sv -portfaults -fsdb -l comp_z.log

z_fmsh:
	fmsh -load ./COLLATERAL/FMSH/user.fmsh

## VERDI DUMPING ##

vc_verdi:
	verdi -lca -dbdir simv.daidir &

vc_info:
	cat ./COLLATERAL/VERDI/dumping_note 
