K1   [type=K-,  listname=KLHVeryLoose];
K2   [type=K-,  listname=KLHVeryLoose];
pip0 [type=pi+, listname=ChargedTracks];
pip1 [type=pi+, listname=ChargedTracks];
pip2 [type=pi+, listname=ChargedTracks];
pim1 [type=pi-, listname=ChargedTracks];
pim2 [type=pi-, listname=ChargedTracks];

D0 [type=D+, ntp_name=Dc,
     fittingAlgorithm=TreeFitter,
     fitConstraints=[Geo, Mass],
     preFitSelectors=[Mass=1.7:2.1],
     postFitSelectors=[Mass=1.7:2.1]];

D1 [type=D+, ntp_name=Dc,
     fittingAlgorithm=TreeFitter,
     fitConstraints=[Geo, Mass],
     preFitSelectors=[Mass=1.7:2.1],
     postFitSelectors=[Mass=1.7:2.1]];

B [type=B0, ntp_name=B,
   fittingAlgorithm=TreeFitter,
   fitConstraints=[Geo],
   preFitSelectors=[DeltaE=-0.30:0.30, Mes=5.19:5.30],
   postFitSelectors=[ProbChiSq=0.001:, DeltaE=-0.20:0.20, Mes=5.20:5.30],
   fitSettings=[InvalidateFit,UpdateDaughters],
   createUsrData=true,
  ];


B -> {D0 pim1}[fraction=0.5];
B -> {D1 pim2}[fraction=0.5];

D0 -> {K1 pip0 pip1};
D1 -> {K2 pip2};

