from pydecay import *

upsilon = Particle(type="Upsilon(4S)")

B0_2 = Particle(type="B0")
antiB0_2= Particle(type="antiB0")
upsilon.add_decay( [B0_2, antiB0_2], 0.5, simulator="VSS_BMIX", simParams="dm")

positron= Particle(type="e+",  recognition="4")
antiLC = Particle(type="anti-Lambda_c-")
B0_2.add_decay( [positron, antiLC], 1,
                fittingAlgorithm = "TreeFitter", fit = ["Geo"],
                preFitSelectors = { "Mass" : "5.0:5.5", "DeltaE" : "-0.5:0.5" },
                postFitSelectors = {"Mass" : None, "DeltaE" : None, "Mes" : None, "Mmiss" : None,
                                    "ProbChiSq" : None, "Flight" : None, "FlightSignificance" : None}
                )

antiP = Particle(type="anti-p-", recognition="pLHVeryLoose")
KPlus = Particle(type="K+")
piMinus = Particle(type="pi-")
antiLC.add_decay( [antiP, KPlus, piMinus],
                  unrefinedListName = "LambdaCTopKpi", fittingAlgorithm = "TreeFitter",
                  fit = ["Mass", "Geo"],
                  postFitSelectors = {"Flight" : None, "FlightSignificance" : None}
                  )


B0 = Particle(type="B0")
antiB0= Particle(type="antiB0")
upsilon.add_decay( 0.5, [B0, antiB0], simulator="VSS_BMIX", simParams="dm" )

e = Particle(type="e-", recognition="eBremReco")
LC = Particle(type="Lambda_c+")
antiB0.add_decay( [e, LC],
                  fittingAlgorithm = "TreeFitter", fit = ["Geo"],
                  preFitSelectors = { "Mass" : "5.0:5.5", "DeltaE" : "-0.5:0.5" },
                  postFitSelectors = {"Mass" : None, "DeltaE" : None, "Mes" : None, "Mmiss" : None,
                                      "ProbChiSq" : None, "Flight" : None, "FlightSignificance" : None}
                  )

p = Particle(type="p+")
KMinus = Particle(type="K-")
piPlus = Particle(type="pi+")
LC.add_decay( [p, KMinus, piPlus] ,
              unrefinedListName = "LambdaCTopKpi", fittingAlgorithm = "TreeFitter",
              fit = ["Mass", "Geo"],
              postFitSelectors = ["Flight", "FlightSignificance"]
              )

upsilon.to_dot().write_png('LambdaC.png')
