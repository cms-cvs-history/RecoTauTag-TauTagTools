#!/bin/bash

# A script for distributing the training of the Tau MVA discriminators. To be used in conjuction the directories
# prepared by PrepareForTraining.mva.  Takes as an argument an integer that specifies which directory
# to train.  Optionally takes a second argument as a filter agains the different training directories 
# Author: Evan Friis, UC Davis (friis@physics.ucdavis.edu)

# Edit for your local machine setup....
export SCRAM_ARCH='slc4_ia32_gcc345'
export VO_CMS_SW_DIR='/raid1/cmssw'
source $VO_CMS_SW_DIR/cmsset_default.sh

DirectoriesToChange=`ls -d TrainDir_*$2*/`
counter=0

echo "fuck"
echo $counter

for toTrain in $DirectoriesToChange
do
   echo $toTrain
   echo $counter
   if [ $counter -eq $1 ]; then
      echo "Training "$toTrain
      cd $toTrain
      eval `scramv1 runtime -sh`
      root -b -q trainMVA.C >& training_output.log
   fi
   let counter=$counter+1
done
