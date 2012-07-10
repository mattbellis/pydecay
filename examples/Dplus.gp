decay [simulator=JETSET];
ChargeConj=True;

D+ [p=[x=0, y=0, z=4.0]];
PiPlus1 [type=pi+];
PiPlus2 [type=pi+];
K*(892)0 [lineshape=BW];

D+ -> {K*(892)0 PiPlus1};
K*(892)0 -> {K+ pi-} [angulardist=VSS];
K*(892)0 -> {K- PiPlus2} [angulardist=VSS];

