#!/bin/sh

# Build the appropriate schema in ORCOFF.  Takes as argument the schema to be used. (ie CMS_COND_BTAU)
# find passwords in /afs/cern.ch/cms/DB/conddb

eval `scramv1 runtime -sh`

pool_build_object_relational_mapping \
        -f $CMSSW_RELEASE_BASE/src/CondFormats/PhysicsToolsObjects/xml/MVAComputerContainer_basic_0.xml \
	-d CondFormatsPhysicsToolsObjects \
	-c oracle://cms_orcoff_prep/CMS_COND_BTAU \
        -u cms_cond_btau \
        -p WCYE6II08K530GPK \
        -dry 
