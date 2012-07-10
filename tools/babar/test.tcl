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

mod clone SmpMakerDefiner My_Dcc_to_pcpic
seq append AnalysisSequence My_Dcc_to_pcpic
talkto My_Dcc_to_pcpic {
	decayMode             set "D-- -> p- pi-"
	daughterListNames     set "pKMTight"
	daughterListNames     set "GoodTracksLoose"
	preFitSelectors       set "Mass 0.7:2.2"
}
mod clone SmpRefitterDefiner My_Dcc_to_pcpic_Constrained
seq append AnalysisSequence My_Dcc_to_pcpic_Constrained
talkto My_Dcc_to_pcpic_Constrained {
	unrefinedListName     set "My_Dcc_to_pcpic"
	preFitSelectors       set "Mass 0.7:2.2"
	postFitSelectors      set "ProbChiSq 0.01:1"
	postFitSelectors      set "FlightSignificance 0"
	postFitSelectors      set "Mass 1.0:1.7"
	fittingAlgorithm      set "TreeFitter"
	fitConstraints        set "BeamBFlight"
}
mod clone SmpMakerDefiner My_Bc_to_pcDcc
seq append AnalysisSequence My_Bc_to_pcDcc
talkto My_Bc_to_pcDcc {
	decayMode             set "B- -> p+ D--"
	daughterListNames     set "pKMTight"
	daughterListNames     set "My_Dcc_to_pcpic_Constrained"
	preFitSelectors       set "Mass 3.8:6.8"
}
mod clone SmpRefitterDefiner My_Bc_to_pcDcc_Constrained
seq append AnalysisSequence My_Bc_to_pcDcc_Constrained
talkto My_Bc_to_pcDcc_Constrained {
	unrefinedListName     set "My_Bc_to_pcDcc"
	preFitSelectors       set "Mass 3.8:6.8"
	postFitSelectors      set "ProbChiSq 0.01:1"
	postFitSelectors      set "FlightSignificance 0"
	postFitSelectors      set "Mass 4.5:5.6"
	fittingAlgorithm      set "TreeFitter"
	fitConstraints        set "Mass anti-Delta--"
	fitConstraints        set "Energy"
	fitConstraints        set "BeamBFlight"
	fitConstraints        set "Geo"
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


	listToDump set My_Bc_to_pcDcc_Constrained

	ntpBlockConfigs  set "B-        B         2         50"
	ntpBlockContents set "B:        MCIdx Mass Momentum CMMomentum Vertex VtxChi2"

	ntpBlockConfigs  set "p+        pc        0         50"
	ntpBlockContents set "pc:       MCIdx Mass Momentum CMMomentum"

	ntpBlockConfigs  set "D--       Dcc       2         50"
	ntpBlockContents set "Dcc:      MCIdx Mass Momentum CMMomentum Vertex VtxChi2"

	ntpBlockConfigs  set "pi-       pic       0         50"
	ntpBlockContents set "pic:      MCIdx Mass Momentum CMMomentum"

	ntpBlockToTrk   set "pc pic "
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


