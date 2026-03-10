create_campaign -args "-full64 -daidir simv.daidir -sff ./COLLATERAL/SFF/config.sff,./COLLATERAL/SFF/faults.sff -campaign fifodemo -dut test.DUT -overwrite"
set_config -global_max_jobs 2
create_testcases -name test1 -exec "$::env(PWD)/simv" -args "+test1" 
create_testcases -name test2 -exec "$::env(PWD)/simv" -args "+test2" 
fsim
dump -fids "130" -mode fm -tc test1 -fsdb fm_fid130_test1.fsdb
report -report fsim_v.rpt -overwrite
