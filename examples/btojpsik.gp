K       [type=K+,  listname=KLHVeryLoose];
muplus  [type=mu+, listname=muNNVeryLoose];
muminus [type=mu-, listname=muNNVeryLoose];

Jpsi [type=J/psi,
     fittingAlgorithm=TreeFitter,
     fitConstraints=[Geo, Mass],
     preFitSelectors=[Mass=2.8:3.4],
     postFitSelectors=[Mass=2.9:3.3]];

B [type=B+, ntp_name=B,
   fittingAlgorithm=TreeFitter,
   fitConstraints=[Geo],
   preFitSelectors=[DeltaE=-0.20:0.20, Mes=5.19:5.30],
   postFitSelectors=[ProbChiSq=0.001:, DeltaE=-0.12:0.12, Mes=5.20:5.30, CmsCosTheta,Mmiss],
   createUsrData=true,
  ];


B -> {Jpsi K};
Jpsi -> {muplus muminus};
