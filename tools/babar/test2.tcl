#  Main tcl file for analysis

#..General setup needed in all jobs
sourceFoundFile ErrLogger/ErrLog.tcl
sourceFoundFile FrameScripts/FwkCfgVar.tcl
sourceFoundFile FrameScripts/talkto.tcl

#-------------- FwkCfgVars needed to control this job ---------------------
set ProdTclOnly true

#..allowed values of BetaMiniReadPersistence are "Kan", "Bdb"
FwkCfgVar BetaMiniReadPersistence Kan

#..allowed values of levelOfDetail are "micro", "cache", "extend" or "refit"
FwkCfgVar levelOfDetail "cache"

#..allowed values of ConfigPatch are "Run2" or "MC".
# This is generally over ridden in the job control tcl file
FwkCfgVar ConfigPatch "MC"

#..Filter on tag bits by default
FwkCfgVar FilterOnTag   "true"

#..Print Frequency
FwkCfgVar PrintFreq 1000

#..Ntuple type and name
FwkCfgVar BetaMiniTuple "root"
FwkCfgVar histFileName "default.root"

#..Number of Events defaults to 0 (run on full tcl file)
FwkCfgVar NEvents 0

################################################################################
#..General physics sequences

# Set to 'trace' to get info on a configuration problem
ErrLoggingLevel warning

#..btaMiniPhysics is the basic physics sequences;
sourceFoundFile BetaMiniUser/btaMiniPhysics.tcl

################################################################################
# Needed for BremRecoElectrons
sourceFoundFile CompositionSequences/CompPsiInitSequence.tcl

#--------------------------------------------------------------------------
#..Use SimpleComposition to make the candidates of interest

#..Create Analysis sequence and append it to the path.
#  All the composition modules get added to this sequence
sequence create AnalysisSequence
path append Everything AnalysisSequence

mod clone SmpMakerDefiner My_Jpsi_to_mucmuc
seq append AnalysisSequence My_Jpsi_to_mucmuc
talkto My_Jpsi_to_mucmuc {
	decayMode             set "J/psi -> mu+ mu-"
	daughterListNames     set "muNNVeryLoose"
	daughterListNames     set "muNNVeryLoose"
	preFitSelectors       set ":3.4"
	preFitSelectors       set "Mass 2.8"
}
mod clone SmpRefitterDefiner My_Jpsi_to_mucmuc_Constrained
seq append AnalysisSequence My_Jpsi_to_mucmuc_Constrained
talkto My_Jpsi_to_mucmuc_Constrained {
	unrefinedListName     set "My_Jpsi_to_mucmuc"
	preFitSelectors       set ":3.4"
	preFitSelectors       set "Mass 2.8"
	postFitSelectors      set ":3.3"
	postFitSelectors      set "Mass 2.9"
	fittingAlgorithm      set "TreeFitter"
	fitConstraints        set "Mass"
	fitConstraints        set "Geo"
}
mod clone SmpMakerDefiner My_Bc_to_JpsiKc
seq append AnalysisSequence My_Bc_to_JpsiKc
talkto My_Bc_to_JpsiKc {
	decayMode             set "B+ -> J/psi K+"
	daughterListNames     set "My_Jpsi_to_mucmuc_Constrained"
	daughterListNames     set "KLHVeryLoose"
	preFitSelectors       set ":5.30"
	preFitSelectors       set "DeltaE -0.20"
	preFitSelectors       set "Mes 5.19"
	preFitSelectors       set ":0.20"
	createUsrData         set "true"
}
mod clone SmpRefitterDefiner My_Bc_to_JpsiKc_Constrained
seq append AnalysisSequence My_Bc_to_JpsiKc_Constrained
talkto My_Bc_to_JpsiKc_Constrained {
	unrefinedListName     set "My_Bc_to_JpsiKc"
	preFitSelectors       set ":5.30"
	preFitSelectors       set "DeltaE -0.20"
	preFitSelectors       set "Mes 5.19"
	preFitSelectors       set ":0.20"
	fittingAlgorithm      set "TreeFitter"
	fitConstraints        set "Geo"
	postFitSelectors      set ":0.12"
	postFitSelectors      set "ProbChiSq 0.001"
	postFitSelectors      set "CmsCosTheta"
	postFitSelectors      set "Mmiss"
	postFitSelectors      set "DeltaE -0.12"
	postFitSelectors      set "Mes 5.20"
	postFitSelectors      set ":"
	postFitSelectors      set ":5.30"
	createUsrData         set "true"
}
#--------------------------------------------------------------------
#..Use BtuTupleMaker to write out ntuples for SimpleComposition job
path append Everything BtuTupleMaker

talkto BtuTupleMaker {

#..Event information to dump
    eventBlockContents   set "EventID CMp4 BeamSpot"
    eventTagsInt set "nTracks"
    eventTagsFloat set "R2All xPrimaryVtx yPrimaryVtx zPrimaryVtx"
    writeEveryEvent set false

#..MC truth info
    fillMC set true
    mcBlockContents set "Mass CMMomentum Momentum Vertex"


	listToDump set My_Bc_to_JpsiKc_Constrained

	ntpBlockConfigs  set "B+        B         2         50"
	ntpBlockContents set "B:        MCIdx Mass Momentum CMMomentum Vertex VtxChi2"

	ntpBlockConfigs  set "J/psi     Jpsi      2         50"
	ntpBlockContents set "Jpsi:     MCIdx Mass Momentum CMMomentum Vertex VtxChi2"

	ntpBlockConfigs  set "mu+       muc       0         50"
	ntpBlockContents set "muc:      MCIdx Mass Momentum CMMomentum"

	ntpBlockConfigs  set "K+        Kc        0         50"
	ntpBlockContents set "Kc:       MCIdx Mass Momentum CMMomentum"

	ntpBlockToTrk   set "muc Kc "
	#..TRK block. Save all of them as well.
	ntpBlockContents set "TRK  : MCIdx Momentum CMMomentum"
	fillAllCandsInList set "TRK ChargedTracks"
	
	#..Want to save all CalorNeutrals in the gamma block
	ntpBlockConfigs set "gamma   gamma  0      60"
	ntpBlockContents set "gamma: MCIdx Momentum"
	gamExtraContents set EMC
	fillAllCandsInList set "gamma CalorNeutral"
	
	
	trkExtraContents set "BitMap:pSelectorsMap,KSelectorsMap,piSelectorsMap,muSelectorsMap,eSelectorsMap,TracksMap"
	trkExtraContents set HOTS
	trkExtraContents set Eff:ave
	}
	
#--------------- Turn on PID weights and neutral corrections ----------------

#pidCfg_mode weight *

talkto EmcNeutCorrLoader {
    correctionOn set true
#endcapShift  set true
}

#----------------------------------------------------------------------------
#..Use $FilterOnTag to disable tag filtering if desired.
module clone TagFilterByName TagJpsill
module talk TagJpsill
orList set JpsiELoose
orList set JpsiMuLoose
assertIfMissing set true
exit
if { $FilterOnTag=="true" } {
    sequence append BetaMiniReadSequence -a KanEventUpdateTag TagJpsill
}

#-----------------------------------------------------------------------
#..Run time options

mod talk EvtCounter
printFreq set $PrintFreq
exit

path list

if { $NEvents>=0 } {
    ev beg -nev $NEvents
        exit
}


