#!/bin/csh -f
echo "Dump fsdb started!"
echo "Fault ID=${VERDI_FUSA_CURRENT_FAULT_ID_LIST}"
echo "SNPS_FDB_SERVER=${SNPS_FDB_SERVER}"

set idlist = ${VERDI_FUSA_CURRENT_FAULT_ID_LIST}
echo $idlist
set ids = `echo $idlist:q | sed 's|.*,||g'`
set fsdb = `echo $idlist:q | sed 's|,|_|g'`
foreach id ($ids:q)
	echo "Dump fsdb for fault ID $id"
	rm -rf gmfm_${fsdb}.fsdb
	vc_fcm -fc fifodemo -fdb_server ${SNPS_FDB_SERVER}   -tcl dump -fid ${id} -tc test1 -mode fm -fsdb gmfm_${fsdb}.fsdb
end
echo "Dump FSDB is done!"
