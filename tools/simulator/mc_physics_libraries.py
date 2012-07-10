from ROOT import TMath

################################################################################
# Non-relativistic Breit-Wigner function
# Simply calls the ROOT implementation
# 
# Area under the curve is normalized to be 0 (I think)
#
# http://root.cern.ch/root/html/TMath.html#TMath:BreitWigner
# 
# mass: variable mass
# peak: peak position of the BW.
# width: gamma
#
################################################################################
def breit_wigner(mass, peak, width):

    return TMath.BreitWigner(mass, peak, width)

################################################################################
# Return max value of the BW PDF by evaluating it at the peak
################################################################################
def breit_wigner_max(peak, width):

    return TMath.BreitWigner(peak, peak, width)


