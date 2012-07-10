Bbar0_2 [type=Bbar0];
B0_2 [type=B0];
LC [type=Lambda(c)-];
AntiLC [type=Lambda(c)-];
e- [recognition=eBremReco];
e+ [recognition=4];


Upsilon(4S)0 -> {Bbar0 B0} [ fraction=0.5, simulator=VSS_BMIX, simParams=dm ];

Bbar0 -> {LC e-} [simparams=PHSP, fittingAlgorithm=TreeFitter, fit=Geo,
		     pre=[Mes, Mmiss, Mass=5.0:5.5, DeltaE=-0.5:0.5],
		     post=[ Mass, DeltaE, Mes, Mmiss, ProbChiSq, Flight, FlightSignificance] ];

LC -> {p(P11)+ K- pi+} [simparams=PHSP, unrefinedListName=LambdaCTopKpi, fittingAlgorithm=TreeFitter,
			 fit=[Mass, Geo],
			 post=[Flight, FlightSignificance] ];
B0 -> {};


Upsilon(4S)0 -> {B0_2 Bbar0_2}  [fraction=0.5, simulator=VSS_BMIX, simParams=dm];

B0_2 -> {AntiLC e+}  [simparams=PHSP, fittingAlgorithm=TreeFitter, fit=Geo,
			pre=[Mes, Mmiss, Mass=5.0:5.5, DeltaE=-0.5:0.5],
			post=[ Mass, DeltaE, Mes, Mmiss, ProbChiSq, Flight, FlightSignificance] ];

AntiLC -> {p(P11)- K+ pi-} [simparams=PHSP, unrefinedListName=LambdaCTopKpi, fittingAlgorithm=TreeFitter,
				  fit=[Mass, Geo],
				  post=[Flight, FlightSignificance] ];
Bbar0_2 -> {};
