from pydecay import *

K = Particle("K-")
Kstar = Particle("K*(892)-")
e = Particle("e+")
mu = Particle("mu+")
nue = Particle("nu(e)", mass=0.00000000001, mass_err_plus=0, mass_err_minus=0,
               width=0, width_err_plus=0, width_err_minus=0, spin='0.5')
numu = Particle("nu(mu)", mass=0.00000000001, mass_err_plus=0, mass_err_minus=0,
               width=0, width_err_plus=0, width_err_minus=0, spin='0.5')
D = Particle("D0")
pi0 = Particle("pi0")
pim = Particle("pi-")
K0 = Particle("K0")

D.add_decay([K,           e,     nue],  fraction=0.0355)
D.add_decay([K.clone(False), mu, numu], fraction=0.0331)

D.add_decay([Kstar,           e.clone(False),     nue.clone(False)],  fraction=0.0217)
D.add_decay([Kstar.clone(False), mu.clone(False), numu.clone(False)], fraction=0.0198)

Kstar.add_decay([K.clone(False),pi0], fraction=0.4995)
Kstar.add_decay([K0,pim], fraction=0.4995)

decay_root = D
