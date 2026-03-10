# Setup module system
if  ! type module &> /dev/null ; then
    if [ -z "$MODULESHOME" ] ; then
        # Load entire tool set of MODULEHOME is empty
        source /arm/tools/setup/init/bash-lite
    else
        # Else just setup the module function in case coming from non bash shell
        MODULESTCL=/arm/tools/tct/tcl/8.5.2/rhe5-x86_64/bin/tclsh
        module (){
            eval `$MODULESTCL $MODULESHOME/lib/modulecmd.tcl bash $*`
        }
    fi
fi

module load swdev python/python/3.11.5 python/ruamel.yaml_py3.11.5/0.18.6 ceme/fts/18.13.0 arm/lupo/3.0.2
module load eda synopsys/vcs/2025.06-1 synopsys/verdi3/2025.06-1 