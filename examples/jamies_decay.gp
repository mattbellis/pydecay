p    [type=p+, listname=pKMTight];
pminus    [type=p-, listname=pKMTight];
piminus    [type=pi-, listname=GoodTracksLoose];

antiDpp  [type=D--,
    fittingAlgorithm=TreeFitter,
    fitConstraints=[BeamBFlight],
    preFitSelectors=[Mass="0.7:2.2"],
    postFitSelectors=[Mass="1.0:1.7", ProbChiSq="0.01:1", FlightSignificance="0"]];


B [type=B-, ntp_name=B,
  fittingAlgorithm=TreeFitter,
  fitConstraints=[BeamBFlight, Energy, Mass=anti-Delta--, Geo],
  preFitSelectors=[Mass="3.8:6.8"],
  postFitSelectors=[Mass="4.5:5.6", ProbChiSq="0.01:1", FlightSignificance=0]];

B -> {p antiDpp};
antiDpp -> {pminus piminus};
