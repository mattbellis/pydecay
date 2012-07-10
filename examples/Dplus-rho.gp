PiPlus1 [type=pi+];
PiPlus2 [type=pi+];
PiZero1 [type=pi0];
PiZero2 [type=pi0];
rho [lineshape=NONRELBW];

D+ -> {rho PiPlus1};

D->pi;


rho -> {PiPlus2 pi-} [fraction=0.5];
rho -> {PiZero1 PiZero2} [fraction=0.5];
