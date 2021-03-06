import pycali
import matplotlib.pyplot as plt 
import numpy as np

#######################################################
# first generate mock data
# data/sim_cont.txt, data/sim_line.txt
#

pycali.generate_mock_data()

#######################################################
# setup configurations, there are two ways:
# 1) load from a param file
#    cfg = pycali.Config("param.txt")
# 2) direct call setup()
# 
cfg = pycali.Config()

# except for the argument "fcont", the rest arguments are optional.
# e.g.,  cfg.setup(fcont="data/ngc5548_cont.txt")
#
cfg.setup(fcont="data/sim_cont.txt",     # fcont is a string
          fline=["data/sim_line.txt", "data/sim_line2.txt"],   # fline is a list, include multiple lines
          nmcmc=20000, ptol=0.1,
          scale_range_low=0.5, scale_range_up=1.5,
          shift_range_low=-1.0, shift_range_up=1.0,
          syserr_range_low=0.0, syserr_range_up=0.2,
          errscale_range_low=0.5, errscale_range_up=2.0,
          sigma_range_low=1.0e-4, sigma_range_up=1.0,
          tau_range_low=1.0, tau_range_up=1.0e4,
          fixed_scale=False, fixed_shift=False,
          fixed_syserr=False, fixed_error_scale=True)
cfg.print_cfg()

######################################################
# do intercalibration
#
cali = pycali.Cali(cfg)  # create an instance
cali.mcmc()              # do mcmc
cali.get_best_params()   # calculate the best parameters
cali.output()            # print output
cali.recon()             # do reconstruction

# plot results to PyCALI_results.pdf
pycali.plot_results(cfg)

# a simple plot 
pycali.simple_plot(cfg)