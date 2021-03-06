#
# plots for cali 
# 
# run "python plot_for_cali.py" after "./cali param.txt"
#
# this file should be placed in the same directory where "data/" exists
#

import corner
import configparser as cfgpars 
import matplotlib.pyplot as plt 
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from os.path import basename
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

class Config:
  def __init__(self, fname="param.txt"):
    config = cfgpars.RawConfigParser(delimiters=' ', comment_prefixes='#', inline_comment_prefixes='#', \
      default_section=cfgpars.DEFAULTSECT, empty_lines_in_values=False)
    
    with open(fname) as f:
      file_content = '[dump]\n' + f.read()

    config.read_string(file_content)

    param = config["dump"]
    self.fcont = param["FileCont"]

    if "FileLine" in param:
      self.fline = param["FileLine"].split(",")
    else:
      self.fline = []
    
    if "NMCMC" in param:
      self.nmcmc = int(param["NMCMC"])
    else:
      self.nmcmc = 10000
    
    if "PTol" in param:
      self.ptol = float(param["PTol"])
    else:
      self.ptol = 0.1
    
    if "FixedScale" in param:
      self.fixed_scale = int(param["FixedScale"])
    else:
      self.fixed_scale = 0
    
    if "FixedShift" in param:
      self.fixed_scale = int(param["FixedShift"])
    else:
      self.fixed_scale = 0

    if "FixedSyserr" in param:
      self.fixed_syserr = int(param["FixedSyserr"])
    else:
      self.fixed_syserr = 1

    if "FixedErrorScale" in param:
      self.fixed_error_scale = int(param["FixedErrorScale"])
    else:
      self.fixed_error_scale = 1
    

def simple_plot(cfg):
  """
  a simple plot
  """ 
  data={}
  nax = 1
  cont = np.loadtxt(cfg.fcont)
  cont_cali = np.loadtxt(cfg.fcont+"_cali", usecols=(0, 1, 2))
  data["cont"]=[cont, cont_cali]
  
  for i, fl in enumerate(cfg.fline):
    nax+=1
    line = np.loadtxt(fl)
    line_cali = np.loadtxt(fl+"_cali", usecols=(0, 1, 2))
    data["line%d"%i] = [line, line_cali]
  
  fig = plt.figure()
  cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
  for i, key in enumerate(data.keys()):
    ax = fig.add_subplot(nax, 1, i+1)
    d = data[key][0]
    dc = data[key][1]
    ax.errorbar(d[:, 0], d[:, 1], yerr=d[:, 2], ls='none', marker='o', markersize=4, color=cycle[0], 
                ecolor='darkgrey', markeredgecolor=None, elinewidth=1, label=key)
    ax.errorbar(dc[:, 0], dc[:, 1], yerr=dc[:, 2], ls='none', marker='o', markersize=4, color=cycle[1],
                ecolor='darkgrey', markeredgecolor=None,  elinewidth=1, label=key+" cali")
    ax.legend()
    ax.set_xlabel("Time")
    ax.set_ylabel("Flux")
    
    ax.minorticks_on()
  
  plt.show()


def plot_results(cfg):
  """
  a detailed plot, output results to PyCALI_results.pdf.
  """
  pdf = PdfPages("PyCALI_results.pdf")
  
  file_dir = "data"
  file_dir += "/"
  #===================================================================
  # load params
  #===================================================================
  with open(file_dir + "/param_input") as f:
    file_content = '[dump]\n' + f.read()
    
  config = cfgpars.ConfigParser(delimiters='=', allow_no_value=True)
  config.read_string(file_content)
  
  for key in config["dump"].keys():
    print(key, config["dump"][key])
  
  #===================================================================
  # load codes
  #===================================================================
  code = np.genfromtxt(file_dir + "/factor.txt", usecols=(0), skip_header=1, dtype=str)
  ncode = len(code)
  
  #===================================================================
  # load means
  #===================================================================
  fp = open(file_dir + "/PyCALI_output.txt", "r")
  cont_mean = np.zeros(ncode)
  fp.readline()
  for i in range(ncode):
    line = fp.readline()
    cont_mean[i] = float(line.split()[1])
  
  lines_mean = {}
  for j in range(len(cfg.fline)):
    lines_mean["%d"%j] = np.zeros(ncode)
    fp.readline()
    for i in range(ncode):
      line = fp.readline()
      lines_mean["%d"%j][i] = float(line.split()[1])
  
  fp.close()
  
  #===================================================================
  # obtain norm for cont and line
  #===================================================================
  num_params_var = 2
  nset = 1
  for j in range(len(cfg.fline)):
    num_params_var += 2
    nset += 1

  cont_mean_code = np.zeros(ncode)
  lines_mean_code={}
  for j in range(len(cfg.fline)):
    line_mean_code = np.zeros(ncode)
    lines_mean_code["%d"%j] = lines_mean_code
  
  sample = np.loadtxt(file_dir + "/posterior_sample.txt")
  # take into account continuum normalization
  sample[:, 0] += np.log(cont_mean[i]) 
  sample[:, 0] /= np.log(10.0)
  for i in range(ncode):
    # scale
    sample[:, num_params_var+i] *= cont_mean[0]/cont_mean[i]
  
    # syserr
    sample[:, num_params_var+2*ncode+i] *= cont_mean[i] 
  
    # error scale
    sample[:, num_params_var+3*ncode + i] *= 1.0
  
  # shift
  sample[:, num_params_var+ncode:num_params_var+2*ncode] *= cont_mean[0] 
  
  # take into account line normalization
  for j in range(len(cfg.fline)):
    line_mean = lines_mean["%d"%j]
    sample[:, 2+2*j] += np.log(line_mean[0])
    sample[:, 2+2*j] /= np.log(10.0)
    
    for i in range(ncode):
      # syserr 
      sample[:, num_params_var+4*ncode+i] *= line_mean[i]
  
      # error scale
      sample[:, num_params_var+5*ncode + i] *=  1.0
  
  # scale in log10
  sample[:, num_params_var:num_params_var+ncode] = np.log10( sample[:, num_params_var:num_params_var+ncode] )
  # error scale in log10
  sample[:, num_params_var+3*ncode:num_params_var+4*ncode] = np.log10( sample[:, num_params_var+3*ncode:num_params_var+4*ncode] )
  for j in range(len(cfg.fline)):
    sample[:, num_params_var+5*ncode+2*j*ncode:num_params_var+6*ncode+2*j*ncode] = \
    np.log10( sample[:, num_params_var+5*ncode+2*j*ncode:num_params_var+6*ncode+2*j*ncode] )
  
  #===================================================================
  # print posterior values
  #===================================================================
  print("log10 Scale")
  scale = np.zeros(ncode)
  for i in range(ncode):
    mean, low, up = np.quantile(sample[:, num_params_var+i], q=(0.5, 0.16, 0.84))
    scale[i] = mean
    print(code[i], "%5.3f -%5.3f +%5.3f"%(mean, mean-low, up-mean))
  
  print("\nShift")
  for i in range(ncode):
    mean, low, up = np.quantile(sample[:, num_params_var+ncode+i], q=(0.5, 0.16, 0.84))
    print(code[i], "%5.3f -%5.3f +%5.3f"%(mean, mean-low, up-mean))
    
  print("\nSyserr of continuum")
  for i in range(ncode):
    mean, low, up = np.quantile(sample[:, num_params_var+2*ncode+i], q=(0.5, 0.16, 0.84))
    print(code[i], "%5.3f -%5.3f +%5.3f"%(mean, mean-low, up-mean))
  
  print("\nlog10 Error Scale of continuum")
  for i in range(ncode):
    mean, low, up = np.quantile(sample[:, num_params_var+3*ncode+i], q=(0.5, 0.16, 0.84))
    print(code[i], "%5.3f -%5.3f +%5.3f"%(mean, mean-low, up-mean))
  
  for j in range(len(cfg.fline)):
    print("\nSyserr of line%d"%j)
    for i in range(ncode):
      mean, low, up = np.quantile(sample[:, num_params_var+4*ncode+i+2*j*ncode], q=(0.5, 0.16, 0.84))
      print(code[i], "%5.3f -%5.3f +%5.3f"%(mean, mean-low, up-mean))
  
    print("\nlog10 Error Scale of line%d"%j)
    for i in range(ncode):
      mean, low, up = np.quantile(sample[:, num_params_var+5*ncode+i+2*j*ncode], q=(0.5, 0.16, 0.84))
      print(code[i], "%5.3f -%5.3f +%5.3f"%(mean, mean-low, up-mean))
  
  #exit()

  plt.rc('text', usetex=True)
  plt.rc('font', family="serif", size=18)
  
  #===================================================================
  # now plot
  #===================================================================
  data={}
  nax = 1
  # first continuum 
  cont = np.loadtxt(cfg.fcont)
  cont_code_org = np.empty(cont.shape[0], dtype="U20")
  cont_cali = np.loadtxt(cfg.fcont+"_cali", usecols=(0, 1, 2))
  cont_code = np.loadtxt(cfg.fcont+"_cali", usecols=(3), dtype=str)
  data["cont"]=[cont, cont_cali]
  cont_full = np.loadtxt(cfg.fcont+"_recon")
  
  # create original code of the raw data
  i1=0
  i2=0
  for i in range(ncode):
    i2 = i1 + np.count_nonzero(cont_code==code[i])
    cont_code_org[i1:i2]=code[i]
    cont_mean_code[i] = np.mean(cont[i1:i2, 1])
    i1 = i2
  
  # load index for sorting the data
  idx_cont = np.loadtxt(cfg.fcont+"_sort", dtype=int)
  
  # load line data if included
  lines_code = {}
  lines_code_org = {}
  lines_full = {}
  idx_lines = {}
  for j in range(len(cfg.fline)):
    line = np.loadtxt(cfg.fline[j])
    line_code_org = np.empty(line.shape[0], dtype="U20")
    line_cali = np.loadtxt(cfg.fline[j]+"_cali", usecols=(0, 1, 2))
    line_code = np.loadtxt(cfg.fline[j]+"_cali", usecols=(3), dtype=str)
    data["line%d"%j] = [line, line_cali]
    line_full = np.loadtxt(cfg.fline[j]+"_recon")
    idx_line = np.loadtxt(cfg.fline[j]+"_sort", dtype=int)
    
    i1=0
    i2=0
    line_mean_code = lines_mean_code["%d"%j]
    for i in range(ncode):
      i2 = i1 + np.count_nonzero(line_code==code[i])
      line_code_org[i1:i2]=code[i]
      line_mean_code[i] = np.mean(line[i1:i2, 1])
      i1 = i2
    
    lines_code["%d"%j] = line_code
    lines_code_org["%d"%j] = line_code_org
    lines_full["%d"%j] = line_full
    idx_lines["%d"%j] = idx_line
  
  # obtain colors of matplotlib
  if ncode <= 10: 
    cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
  else:
    cycle = [
        '#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c', '#98df8a',
        '#d62728', '#ff9896', '#9467bd', '#c5b0d5', '#8c564b', '#c49c94',
        '#e377c2', '#f7b6d2', '#7f7f7f', '#c7c7c7', '#bcbd22', '#dbdb8d',
        '#17becf', '#9edae5']
  
  fig = plt.figure(figsize=(15, 12))
  
  # plot original data
  ax = fig.add_axes((0.1, 0.68, 0.66, 0.28))
  key="cont"
  d = data[key][0]
  dc = data[key][1]
  for i in range(ncode):
    idx = np.where((cont_code_org == code[i]))
    ax.errorbar(d[idx[0], 0], d[idx[0], 1], yerr=d[idx[0], 2], ls='none', marker='o', markersize=3, color=cycle[np.mod(i, len(cycle), dtype=int)], \
                ecolor='grey', markeredgecolor=None, elinewidth=1, capsize=0.9,  label=r'{0} ${1}~({2})$'.format(i, code[i], len(idx[0])))
                
  ax.legend(frameon=False, loc=(1.0, 0.0), handletextpad=-0.1, fontsize=15)
  ax.set_ylabel("Raw Data Flux")
  xlim = ax.get_xlim()
  ylim = ax.get_ylim()
  [xt.set_visible(False) for xt in ax.get_xticklabels()]
  ax.minorticks_on()
  
  # plot calibrated data              
  ax = fig.add_axes((0.1, 0.38, 0.66, 0.28))
  ax.plot(cont_full[:, 0], cont_full[:, 1], lw=1, linestyle="--", color='k', alpha=0.8)
  ax.plot(cont_full[:, 0], cont_full[:, 1]+cont_full[:, 2], lw=1, linestyle="--", color='k', alpha=0.8)
  ax.plot(cont_full[:, 0], cont_full[:, 1]-cont_full[:, 2], lw=1, linestyle="--", color='k', alpha=0.8)
  for i in range(ncode):
    idx = np.where((cont_code == code[i]))
    ax.errorbar(dc[idx[0], 0], dc[idx[0], 1], yerr=dc[idx[0], 2], ls='none', marker='o', markersize=3, color=cycle[np.mod(i, len(cycle), dtype=int)], \
                ecolor='grey', markeredgecolor=None,  elinewidth=1, capsize=1.5)
    ax.errorbar(dc[idx[0], 0], dc[idx[0], 1], yerr=d[idx_cont[idx[0]], 2]*cont_mean_code[0]/cont_mean_code[i], ls='none', color=cycle[np.mod(i, len(cycle), dtype=int)], \
                ecolor='grey', markeredgecolor=None,  elinewidth=1, capsize=1.5)
    
  ax.set_ylabel("Intercalibrated Flux")
  ax.set_xlim(xlim[0], xlim[1])
  [xt.set_visible(False) for xt in ax.get_xticklabels()]
  ax.minorticks_on()
  
  # plot parameter prior
  ax = fig.add_axes((0.76, 0.38, 0.2, 0.5))
  ax.text(0.3, 0.5, r"$\varphi,~~~~G, ~~~\epsilon, ~~~b$", fontsize=15)
  for i in range(ncode):
    fstr = r"${0}$".format(i)
    ax.text(0.1, 0.45-i*0.04, fstr, fontsize=15)
    fstr=r""
    if np.std(sample[:, num_params_var+i]) == 0.0 :
      fstr = fstr + r"N"
    else:
      fstr = fstr + r"Y"
    
    if np.std(sample[:, num_params_var+ncode+i]) == 0.0 :
      fstr = fstr + r"~~~~~N"
    else:
      fstr = fstr + r"~~~~~Y"
    
    if np.std(sample[:, num_params_var+2*ncode+i]) == 0.0 :
      fstr = fstr + r"~~~~N"
    else:
      fstr = fstr + r"~~~~Y"
    
    if np.std(sample[:, num_params_var+3*ncode+i]) == 0.0 :
      fstr = fstr + r"~~~N"
    else:
      fstr = fstr + r"~~~Y"
    
    ax.text(0.3, 0.45-i*0.04, fstr, fontsize=15)
  
  ax.text(0.1, 0.45-ncode*0.04, "Y: free, N: fixed", fontsize=15)
  ax.set_axis_off()
  
  # plot residuals
  ax = fig.add_axes((0.1, 0.08, 0.66, 0.28))
  for i in range(ncode):
   idx = np.where((cont_code == code[i]))
   res = dc[idx[0], 1] - np.interp(dc[idx[0], 0], cont_full[:, 0], cont_full[:, 1])
   ax.errorbar(dc[idx[0], 0], res, yerr=dc[idx[0], 2], ls='none', marker='o', markersize=3, color=cycle[np.mod(i, len(cycle), dtype=int)], \
                ecolor=cycle[np.mod(i, len(cycle))], markeredgecolor=None,  elinewidth=1, capsize=1.5,  label=r'${0}$'.format(code[i]), zorder=1)
   
   ax.errorbar(dc[idx[0], 0], res, yerr=d[idx_cont[idx[0]], 2]*cont_mean_code[0]/cont_mean_code[i]*10**(scale[i]), ls='none', color=cycle[np.mod(i, len(cycle))], \
                ecolor=cycle[np.mod(i, len(cycle))], markeredgecolor=None,  elinewidth=1, capsize=1.5, zorder=1)
  
  error_mean = np.mean(dc[:, 2])
  ax.axhline(y=0.0, linestyle='--', color='silver', lw=1, zorder=0)
  ax.axhline(y=-error_mean, linestyle='--', color='silver', lw=1, zorder=0)
  ax.axhline(y=error_mean, linestyle='--', color='silver', lw=1, zorder=0)
  ax.set_xlabel("Time")
  #ax.set_title("Continuum Residuals")
  ax.set_ylabel("Residuals")
  ax.set_xlim(xlim[0], xlim[1])
  ylim = ax.get_ylim()
  ax.minorticks_on()
  
  ax = fig.add_axes((0.76, 0.08, 0.07, 0.28))
  xlim = ax.get_xlim()
  for i in range(ncode):
    idx = np.where((cont_code == code[i]))
    ax.errorbar(xlim[1]-(xlim[1]-xlim[0])/(ncode+4) * (i+2), 0.0, yerr=np.mean(dc[idx[0], 2]), color=cycle[np.mod(i, len(cycle), dtype=int)],\
               elinewidth=1, capsize=1.5, zorder=1)
    ax.errorbar(xlim[1]-(xlim[1]-xlim[0])/(ncode+4) * (i+2), 0.0, yerr=np.mean(d[idx_cont[idx[0]], 2])*cont_mean_code[0]/cont_mean_code[i]*10**(scale[i]), color=cycle[np.mod(i, len(cycle), dtype=int)],\
               elinewidth=1, capsize=1.5, zorder=1)
  
  ax.set_xlim(xlim[0], xlim[1])
  ax.set_ylim(ylim[0], ylim[1])
  [xt.set_visible(False) for xt in ax.get_xticklabels()]
  [xt.set_visible(False) for xt in ax.get_yticklabels()]
  ax.minorticks_on()
  ax.axhline(y=0.0, linestyle='--', color='silver', lw=1, zorder=0)
  ax.axhline(y=-error_mean, linestyle='--', color='silver', lw=1, zorder=0)
  ax.axhline(y=error_mean, linestyle='--', color='silver', lw=1, zorder=0)
  
  ax = fig.add_axes((0.88, 0.08, 0.1, 0.28))
  ax.hist((dc[:, 1] - np.interp(dc[:, 0], cont_full[:, 0], cont_full[:, 1]))/dc[:, 2], orientation='horizontal', \
         density=True, bins=20, range=[-4, 4])
  y = np.linspace(-4, 4, 100)
  x = 1.0/np.sqrt(2.0*np.pi)*np.exp(-0.5*y*y)
  ax.plot(x, y)
  ax.set_ylim(-4, 4)
  #[yt.set_visible(False) for yt in ax.get_yticklabels()]
  ax.set_ylabel("Stardarized Residuals")
  ax.minorticks_on()
  
  fname = cfg.fcont
  fname = fname.replace("_", " ")
  fig.suptitle(r"\bf {0}".format(fname), x=0.5, y=1.0)
  pdf.savefig(fig)
  plt.close()
  
  #===================================================================
  # then plot line if there is
  #===================================================================
  for j in range(len(cfg.fline)):
    fig = plt.figure(figsize=(15, 12))
    
    ax = fig.add_axes((0.1, 0.68, 0.66, 0.28))
    key="line%d"%j
    d = data[key][0]
    dc = data[key][1]
    line_code_org = lines_code_org["%d"%j]
    line_code = lines_code["%d"%j]
    line_full = lines_full["%d"%j]
    idx_line = idx_lines["%d"%j]
    line_mean_code = lines_mean_code["%d"%j]
    for i in range(ncode):
     idx = np.where((line_code_org == code[i]))
     ax.errorbar(d[idx[0], 0], d[idx[0], 1], yerr=d[idx[0], 2], ls='none', marker='o', markersize=3, color=cycle[np.mod(i, len(cycle), dtype=int)], \
                 ecolor='grey', markeredgecolor=None, elinewidth=1, capsize=0.9,  label=r'{0} ${1}~({2})$'.format(i, code[i], len(idx[0])))
    
    ax.legend(frameon=False, loc=(1.0, 0.0), handletextpad=-0.1, fontsize=15)
    ax.set_ylabel("Raw Data Flux")
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    ax.minorticks_on()
    [xt.set_visible(False) for xt in ax.get_xticklabels()]
   
    ax = fig.add_axes((0.1, 0.38, 0.66, 0.28))
    ax.plot(line_full[:, 0], line_full[:, 1], lw=1, linestyle="--", color='k', alpha=0.8)
    ax.plot(line_full[:, 0], line_full[:, 1]-line_full[:, 2], lw=1, linestyle="--", color='k', alpha=0.8)
    ax.plot(line_full[:, 0], line_full[:, 1]+line_full[:, 2], lw=1, linestyle="--", color='k', alpha=0.8)
    for i in range(ncode):
     idx = np.where((line_code == code[i]))
     ax.errorbar(dc[idx[0], 0], dc[idx[0], 1], yerr=dc[idx[0], 2], ls='none', marker='o', markersize=3, color=cycle[np.mod(i, len(cycle), dtype=int)], \
                 ecolor='grey', markeredgecolor=None,  elinewidth=1, capsize=0.9, label=r'${0}$'.format(code[i]))
    
    ax.set_ylabel("Intercalibrated Flux")
    ax.set_xlim(xlim[0], xlim[1])
    ax.minorticks_on()
    [xt.set_visible(False) for xt in ax.get_xticklabels()]
   
    # plot parameter prior
    ax = fig.add_axes((0.76, 0.38, 0.2, 0.5))
    ax.text(0.3, 0.5, r"$\varphi,~~~~G, ~~~\epsilon, ~~~b$", fontsize=15)
    for i in range(ncode):
      fstr = r"${0}$".format(i)
      ax.text(0.1, 0.45-i*0.04, fstr, fontsize=15)
      fstr=r""
      if np.std(sample[:, num_params_var+i]) == 0.0 :
        fstr = fstr + r"N"
      else:
        fstr = fstr + r"Y"
      
      # line does not have G
      if np.std(sample[:, num_params_var+ncode+i]) == 0.0 :
        fstr = fstr + r"~~~~~N"
      else:
        fstr = fstr + r"~~~~~N"
      
      if np.std(sample[:, num_params_var+2*ncode+i]) == 0.0 :
        fstr = fstr + r"~~~~N"
      else:
        fstr = fstr + r"~~~~Y"
      
      if np.std(sample[:, num_params_var+3*ncode+i]) == 0.0 :
        fstr = fstr + r"~~~N"
      else:
        fstr = fstr + r"~~~Y"
      
      ax.text(0.3, 0.45-i*0.04, fstr, fontsize=15)
   
    ax.text(0.1, 0.45-ncode*0.04, "Y: free, N: fixed", fontsize=15)
    ax.set_axis_off()
   
    ax = fig.add_axes((0.1, 0.08, 0.66, 0.28))
    for i in range(ncode):
      idx = np.where((line_code == code[i]))
      res = dc[idx[0], 1] - np.interp(dc[idx[0], 0], line_full[:, 0], line_full[:, 1])
      ax.errorbar(dc[idx[0], 0], res, yerr=dc[idx[0], 2], ls='none', marker='o', markersize=3, color=cycle[np.mod(i, len(cycle), dtype=int)], \
                 ecolor=cycle[np.mod(i, len(cycle), dtype=int)], markeredgecolor=None,  elinewidth=1, capsize=0.9, label=r'${0}$'.format(code[i]), zorder=0)
      
      ax.errorbar(dc[idx[0], 0], res, yerr=d[idx_line[idx[0]], 2]*line_mean_code[0]/line_mean_code[i]*10**(scale[i]), \
                  ls='none', color=cycle[np.mod(i, len(cycle))], \
                  ecolor=cycle[np.mod(i, len(cycle))], markeredgecolor=None,  elinewidth=1, capsize=1.5, zorder=1)
      
    error_mean = np.mean(dc[:, 2])
    ax.axhline(y=0.0, linestyle='--', color='silver', lw=1, zorder=0)
    ax.axhline(y=-error_mean, linestyle='--', color='silver', lw=1, zorder=0)
    ax.axhline(y=error_mean, linestyle='--', color='silver', lw=1, zorder=0)
    ax.set_xlabel("Time")
    ax.set_ylabel("Residuals")
    ax.set_xlim(xlim[0], xlim[1])
    ylim = ax.get_ylim()
    ax.minorticks_on()
    
    ax = fig.add_axes((0.76, 0.08, 0.07, 0.28))
    xlim = ax.get_xlim()
    for i in range(ncode):
      idx = np.where((line_code == code[i]))
      ax.errorbar(xlim[1]-(xlim[1]-xlim[0])/(ncode+4) * (i+2), 0.0, yerr=np.mean(dc[idx[0], 2]), color=cycle[np.mod(i, len(cycle), dtype=int)],\
                 elinewidth=1, capsize=1.5, zorder=1)
      ax.errorbar(xlim[1]-(xlim[1]-xlim[0])/(ncode+4) * (i+2), 0.0, yerr=np.mean(d[idx_line[idx[0]], 2])*line_mean_code[0]/line_mean_code[i]*10**(scale[i]), color=cycle[np.mod(i, len(cycle), dtype=int)],\
                 elinewidth=1, capsize=1.5, zorder=1)
    
    ax.set_xlim(xlim[0], xlim[1])
    ax.set_ylim(ylim[0], ylim[1])
    [xt.set_visible(False) for xt in ax.get_xticklabels()]
    [xt.set_visible(False) for xt in ax.get_yticklabels()]
    ax.minorticks_on()
    ax.axhline(y=0.0, linestyle='--', color='silver', lw=1, zorder=0)
    ax.axhline(y=-error_mean, linestyle='--', color='silver', lw=1, zorder=0)
    ax.axhline(y=error_mean, linestyle='--', color='silver', lw=1, zorder=0)
   
    ax = fig.add_axes((0.88, 0.08, 0.1, 0.28))
    ax.hist((dc[:, 1] - np.interp(dc[:, 0], line_full[:, 0], line_full[:, 1]))/dc[:, 2], orientation='horizontal', \
            density=True, bins=20, range=[-4, 4])
    y = np.linspace(-4, 4, 100)
    x = 1.0/np.sqrt(2.0*np.pi)*np.exp(-0.5*y*y)
    ax.plot(x, y)
    ax.set_ylim(-4, 4)
    
    #[yt.set_visible(False) for yt in ax.get_yticklabels()]
    ax.set_ylabel("Stardarized Residuals")
    ax.minorticks_on()
    
    fname = cfg.fline[j]
    fname = fname.replace("_", " ")
    fig.suptitle(r"\bf {0}".format(fname), x=0.5, y=1.0)
   
    pdf.savefig(fig)
    plt.close()
   
  #pdf.close()
  #exit()
  
  #===================================================================
  # now plot histograms
  #===================================================================
  if int(config["dump"]["fixed_scale"]) == 1:
    fig = corner.corner(sample[:, num_params_var+ncode+1:num_params_var+2*ncode], smooth=True, smooth1d = True, \
          levels=1.0-np.exp(-0.5*np.arange(1.0, 3.1, 1.0)**2), show_titles=True, title_fmt=".3f")
    
    ax = fig.get_axes()
    for i in range(ncode-1):
      xlim = ax[i*(ncode-1)+i].get_xlim()
      ylim = ax[i*(ncode-1)+i].get_ylim()
      ax[i*(ncode-1)+i].text(xlim[1]-0.2*(xlim[1]-xlim[0]), ylim[1] - 0.2*(ylim[1]-ylim[0]), r'$\bf {0}$'.format(code[i+1]))
    fig.suptitle(r"\bf Shift", fontsize=20)
    pdf.savefig(fig)
    plt.close()
   
  elif int(config["dump"]["fixed_shift"]) == 1:
    fig = corner.corner(sample[:, num_params_var+1:num_params_var+ncode], smooth=True, smooth1d = True,  \
          levels=1.0-np.exp(-0.5*np.arange(1.0, 3.1, 1.0)**2), show_titles=True, title_fmt=".3f")
    ax = fig.get_axes()
    for i in range(ncode-1):
      xlim = ax[i*(ncode-1)+i].get_xlim()
      ylim = ax[i*(ncode-1)+i].get_ylim()
      ax[i*(ncode-1)+i].text(xlim[1]-0.2*(xlim[1]-xlim[0]), ylim[1] - 0.2*(ylim[1]-ylim[0]), r'$\bf {0}$'.format(code[i+1]))
    fig.suptitle(r"\bf Scale", fontsize=20)
    pdf.savefig(fig)
    plt.close()
  else:
    for i in range(1, ncode):
      range_min = np.min(sample[:, [num_params_var+i,num_params_var+i+ncode]], axis=0)
      range_max = np.max(sample[:, [num_params_var+i,num_params_var+i+ncode]], axis=0)
      span = range_max - range_min
      range_interval = [[range_min[i]-0.3*span[i], range_max[i]+0.3*span[i]] for i in range(2)]
      fig = corner.corner(sample[:, [num_params_var+i,num_params_var+i+ncode]], smooth=True, smooth1d = True, labels=[r"$\log\varphi$", r"$G$"], 
            range=range_interval, \
            levels=1.0-np.exp(-0.5*np.arange(1.0, 3.1, 1.0)**2), show_titles=True, title_fmt=".3f")
      
      ax = fig.get_axes()
      ax[1].text(0.0, 0.5, r"\bf Scale \& Shift", fontsize=15)
      ax[1].text(0.0, 0.65, r"\bf"+r'$\bf {0}$'.format(code[i]), fontsize=15)
      #fig.suptitle(r"\bf Scale \& Shift  "+r'${0}$'.format(code[i][3:-4]), fontsize=20)
      pdf.savefig(fig)
      plt.close()
  
  if int(config["dump"]["fixed_syserr"]) == 0:
    fig = corner.corner(sample[:, num_params_var+2*ncode:num_params_var+3*ncode], smooth=True, smooth1d = True, \
        levels=1.0-np.exp(-0.5*np.arange(1.0, 3.1, 1.0)**2), show_titles=True, title_fmt=".3f")
    ax = fig.get_axes()
    for i in range(ncode):
      xlim = ax[i*ncode+i].get_xlim()
      ylim = ax[i*ncode+i].get_ylim()
      ax[i*ncode+i].text(xlim[1]-0.2*(xlim[1]-xlim[0]), ylim[1] - 0.2*(ylim[1]-ylim[0]), r'$\bf {0}$'.format(code[i]))
    fig.suptitle(r"\bf Systematic Error (Continuum)", fontsize=20)
    pdf.savefig(fig)
    plt.close()
  
  
  if int(config["dump"]["fixed_error_scale"]) == 0:
    fig = corner.corner(sample[:, num_params_var+3*ncode:num_params_var+4*ncode], smooth=True, smooth1d = True, show_titles=True, title_fmt=".3f")
    ax = fig.get_axes()
    for i in range(ncode):
      xlim = ax[i*ncode+i].get_xlim()
      ylim = ax[i*ncode+i].get_ylim()
      ax[i*ncode+i].text(xlim[1]-0.2*(xlim[1]-xlim[0]), ylim[1] - 0.2*(ylim[1]-ylim[0]), r'$\bf {0}$'.format(code[i]))
    fig.suptitle(r"\bf Error Scale", fontsize=20)
    pdf.savefig(fig)
    plt.close()
  
  if int(config["dump"]["fixed_syserr"]) == 0 and int(config["dump"]["fixed_error_scale"]) == 0:
  
    for i in range(ncode):
      fig = corner.corner(sample[:, [num_params_var+2*ncode+i,num_params_var+2*ncode+i+ncode]], smooth=True, smooth1d = True, labels=[r"$\epsilon$", r"$b$"], 
            levels=1.0-np.exp(-0.5*np.arange(1.0, 3.1, 1.0)**2), show_titles=True, title_fmt=".3f")
      
      ax = fig.get_axes()
      ax[1].text(0.0, 0.5, r"\bf Syserr \& Error Scale", fontsize=15)
      ax[1].text(0.0, 0.6, r"\bf"+r'${0}$'.format(code[i]), fontsize=15)
      #fig.suptitle(r"\bf Syserr \& Error Scale  "+code[i][3:-4], fontsize=20)
      pdf.savefig(fig)
      plt.close()
  
  for j in range(len(cfg.fline)):
    if int(config["dump"]["fixed_syserr"]) == 0:
      fig = corner.corner(sample[:, num_params_var+4*ncode+2*j*ncode:num_params_var+5*ncode+2*j*ncode], smooth=True, smooth1d = True, \
            levels=1.0-np.exp(-0.5*np.arange(1.0, 3.1, 1.0)**2), show_titles=True, title_fmt=".3f")
      ax = fig.get_axes()
      for i in range(ncode):
        xlim = ax[i*ncode+i].get_xlim()
        ylim = ax[i*ncode+i].get_ylim()
        ax[i*ncode+i].text(xlim[1]-0.2*(xlim[1]-xlim[0]), ylim[1] - 0.2*(ylim[1]-ylim[0]), r'$\bf {0}$'.format(code[i]))
      fig.suptitle(r"\bf Systematic Error (Line%d)"%j, fontsize=20)
      pdf.savefig(fig)
      plt.close()
  
    if int(config["dump"]["fixed_error_scale"]) == 0:
      fig = corner.corner(sample[:, num_params_var+5*ncode+2*j*ncode:num_params_var+6*ncode+2*j*ncode], smooth=True, smooth1d = True,\
        levels=1.0-np.exp(-0.5*np.arange(1.0, 3.1, 1.0)**2), show_titles=True, title_fmt=".3f")
      ax = fig.get_axes()
      for i in range(ncode):
        xlim = ax[i*ncode+i].get_xlim()
        ylim = ax[i*ncode+i].get_ylim()
        ax[i*ncode+i].text(xlim[1]-0.2*(xlim[1]-xlim[0]), ylim[1] - 0.2*(ylim[1]-ylim[0]), r'$\bf {0}$'.format(code[i]))
      fig.suptitle(r"\bf Error Scale (Line%d)"%j, fontsize=20)
      pdf.savefig(fig)
      plt.close()
      
    if int(config["dump"]["fixed_syserr"]) == 0 and int(config["dump"]["fixed_error_scale"]) == 0:
  
      for i in range(ncode):
        fig = corner.corner(sample[:, [num_params_var+4*ncode+i+2*j*ncode,num_params_var+4*ncode+i+ncode+2*j*ncode]], smooth=True, smooth1d = True, \
            labels=[r"$\epsilon$", r"$b$"], levels=1.0-np.exp(-0.5*np.arange(1.0, 3.1, 1.0)**2), show_titles=True, title_fmt=".3f")
      
        ax = fig.get_axes()
        ax[1].text(0.0, 0.5, r"\bf Syserr \& Error Scale", fontsize=15)
        ax[1].text(0.0, 0.65, r"\bf"+r'$\bf {0}$'.format(code[i]), fontsize=15)
        pdf.savefig(fig)
        plt.close()
  
    
  pdf.close()

if __name__=="__main__":
  # load configuration form param.txt
  cfg = Config("param.txt")
   
  # plot results to PyCALI_results.pdf
  plot_results(cfg)
  
  # a simple plot 
  simple_plot(cfg)