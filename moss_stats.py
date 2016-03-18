from helper import *
from git_helper import *
from time import strptime
from datetime import date
from moss_tool import *
import matplotlib.colors as cl
import matplotlib.cm as cm

def make_moss_graphs(output_dir, year_q):
  all_sims = load_all_sims_from_log(output_dir, year_q)
  all_output_f = get_all_output_f(all_sims)
  top_sims = {}
  for uname in all_sims:
    top_sims[uname] = {}
    for commit in all_sims[uname]:
      if len(all_sims[uname][commit]) == 0: continue
      other_f_path, _, _, percent, _ = all_sims[uname][commit][0]
      top_sims[uname][commit] = (get_uname_from_f(other_f_path), percent)
  graph_moss_all_student(all_sims, all_output_f, output_dir, year_q) 
  graph_aggr_top_moss(top_sims, all_output_f, output_dir, year_q)

def get_uname_from_f(output_f):
  # format: final_submissions/year_q_username_num
  # return add username_num
  if "final_submissions" in output_f:
    return '_'.join((output_f.split('/')[-1]).split('_')[2:])
  else:
    # format online/username
    return output_f.split('/')[-1]

def get_all_output_f(all_sims):
  all_output_f = set()
  for uname in all_sims:
    print "username", uname
    for commit in all_sims[uname]:
    #other_f_path, other_f_html, tokens_matched, percent_self, percent_other 
      commit_output_f = [sim[0] for sim in all_sims[uname][commit]]
      for full_f in commit_output_f:
        all_output_f.add(get_uname_from_f(full_f))
  return all_output_f

"""
Creates one graph per student for moss similarities.
"""
def graph_moss_all_student(all_sims, y_labels, output_dir, year_q):
  y_labels = list(y_labels)
  y_labels.sort()
  y_ref_dict = dict([(y_labels[i], i) for i in range(len(y_labels))])
  for uname in all_sims:
    all_times = []
    for posix_time in all_sims[uname]:
      for sim in all_sims[uname][posix_time]:
        other_path, other_html, tokens, percent_self, percent_other = sim
        y_ind = y_ref_dict[get_uname_from_f(other_path)]
        
        all_times.append((int(posix_time), y_ind, float(percent_self)/100))
    if not all_times: continue
    x_scatter, y_scatter, z_colors = zip(*all_times)
    
    print "Making plot."
    fig = plt.figure(figsize=(7,max(int(len(y_labels)/7), 7)))
    ax1 = plt.gca()
    marker_size = 100
    print "Graphing scatter."
    plt.rcParams['image.cmap'] = 'gray'
    sc = plt.scatter(x_scatter, y_scatter, marker_size, c=z_colors)
    plt.colorbar()

    # put students on y axis
    #y_real_labels = [''] +  y_labels + ['']
  
    ax1.set_ylim(0, len(y_labels)-1)
    ax1.set_yticks(np.arange(len(y_labels)))
    ytickNames = plt.setp(ax1, yticklabels=y_labels)
    plt.setp(ytickNames, fontsize=8)

    # put times on x axis
    xlims = ax1.get_xlim()
    incr = (xlims[1] - xlims[0])/10
    posix_range = np.arange(xlims[0], xlims[1], step=incr)
    x_labels = [(date.fromtimestamp(posix_t)).strftime('%m/%d %H:%M') \
                    for posix_t in posix_range]
    xtickNames = plt.setp(ax1, xticklabels=x_labels)
    plt.setp(xtickNames, rotation=45, fontsize=8)

    ax1.set_title('%s, %s Moss similarity' % (year_q, uname))
    # resize
    plt.tight_layout()

    fig_dest = os.path.join(output_dir, 'moss_%s_%s.png' % (year_q, uname))
    print "Saving", fig_dest
    fig.savefig(fig_dest)
    plt.close()

"""
Creates one graph per class for moss similarities...?
"""
def graph_aggr_moss(similarities, ):
  pass

"""
Creates one graph per class for only the top moss
similarity per commit.
"""
def graph_aggr_top_moss(top_sims, y_labels, output_dir, year_q):
  y_labels = list(y_labels)
  y_labels.sort()
  y_ref_dict = dict([(y_labels[i], i) for i in range(len(y_labels))])
  print y_ref_dict
  fig = plt.figure()
  ax1 = plt.gca()
  jet = plt.get_cmap('jet')
  cNorm = cl.Normalize(vmin=0, vmax=len(y_labels))
  uname_scalarMap = cm.ScalarMappable(norm=cNorm, cmap=jet)
  print uname_scalarMap.get_clim()
  for uname in top_sims:
    all_times = []
    for posix_time in top_sims[uname]:
      other_f, percent = top_sims[uname][posix_time]
      all_times.append((int(posix_time), y_ref_dict[other_f], float(percent)/100))
    x_scatter, y_scatter, gray_colors = zip(*all_times)
    
    marker_size = 100
    uname_color = uname_scalarMap.to_rgba(y_ref_dict[uname])
    uname_color_norm = [float(0.5*uc)/max(uname_color) for uc in uname_color]
    colors=[map(lambda x: 0.25+x*gc, uname_color_norm) \
                for gc in gray_colors]
    sc = plt.scatter(x_scatter, y_scatter, marker_size, c=colors)
    plt.show()

  # put students on y axis
  #y_real_labels = [''] +  y_labels + ['']
  
  ax1.set_ylim(0, len(y_labels)-1)
  ytickNames = plt.setp(ax1, yticklabels=y_labels)
  plt.setp(ytickNames, rotation=45, fontsize=8)

  # put times on x axis
  xlims = ax1.get_xlim()
  incr = (xlims[1] - xlims[0])/10
  posix_range = np.linspace(xlims[0], xlims[1], 10)
  x_labels = [(date.fromtimestamp(posix_t)).strftime('%m/%d %H:%M') \
                  for posix_t in posix_range]
  xtickNames = plt.setp(ax1, xticklabels=x_labels)
  plt.setp(xtickNames, rotation=45, fontsize=8)

  ax1.set_title('All %s Moss similarity' % (year_q))
  # resize
  plt.tight_layout()

  fig_dest = os.path.join(output_dir, 'all_moss_%s.png' % (year_q))
  print "Saving aggregate figure", fig_dest
  fig.savefig(fig_dest)
  plt.close()
  pass
