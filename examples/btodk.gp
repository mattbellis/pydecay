K   [type=K-,  listname=KLHVeryLoose];
pip0 [type=pi+, listname=ChargedTracks];
pip1 [type=pi+, listname=ChargedTracks];
pim [type=pi-, listname=ChargedTracks];

D [type=D+, ntp_name=Dc,
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


B -> {D pim};
D -> {K pip0 pip1};

