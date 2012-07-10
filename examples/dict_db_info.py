from pydecay.db.dict_impl import *

pi0 = ParticleType(mass=134.9766, width=7.9e-6, spin=0)
pi_c = ParticleType(mass=139.57018, width=2.5452e-14, spin=0)
nue = ParticleType(mass=0.00000000001, width=0, spin=0.5)
D0 = ParticleType(mass=1864.84, width=1.616e-09, spin=0)
K_c = ParticleType(mass=493.677, width=5.352e-14, spin=0)
e = ParticleType(mass=0.51099891, width=0, spin=0.5)
D_c = ParticleType(mass=1867, width=1.62e-10, spin=0)

ParticleType.particles.update({
    'pi0' : pi0,
    'pi+' : pi_c,
    'pi-' : pi_c.copy(),
    'nu(e)' : nue,
    'nubar(e)' : nue.copy(),
    'D0' : D0,
    'D+' : D_c,
    'K-' : K_c,
    'K+' : K_c.copy(),
    'K*(892)0' : K_c.copy(),
    'e+' : e,
    'e-' : e.copy()
})

DecayMode.decays.update({
    'D0' : [ DecayMode(products=['e+', 'K-', 'nu(e)'], branching_fraction=0.0355),
             # Other D0 decays go here 
            ],
    # These branching fractions are wrong - just for demo purposes
    'D+' : [ DecayMode(products=['K*(892)0', 'pi+'], branching_fraction=0.02)],
    'K*(892)0' : [ DecayMode(products=['K-', 'pi+'], branching_fraction=0.03),
                   DecayMode(products=['K+', 'pi-'], branching_fraction=0.04)],
    
})
