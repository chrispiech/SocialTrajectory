from helper import *
from git_helper import *
from moss_tool import *
from ta_stats import *
import matplotlib.colors as cl
import matplotlib.cm as cmx

uname_ind, grp_ind, num_sims_ind, frac_sims_ind = 0, 1, 2, 3
max_t_ind, max_ps_ind, max_po_ind = 4, 5, 6
avg_t_ind, avg_ps_ind, avg_po_ind = 7, 8, 9
start_sim_posix_ind, end_sim_posix_ind = 10, 11
start_posix_ind, end_posix_ind = 12, 13
commits_ind, days_ind, hrs_ind = 14, 15, 16
assgt3_g_ind, assgt3_r_ind = 17, 18
mt_g_ind, mt_r_ind = 19, 20
f_g_ind, f_r_ind = 21, 22

titles = []
titles += ['uname\t', 'grp', 'n_sims', 'frac']
titles += ['max_t', 'max_ps', 'max_po']
titles += ['avg_t', 'avg_ps', 'avg_po']
titles += ['st_sim', 'end_sim']
titles += ['st\t', 'end\t']
titles += ['commits', 'days', 'hrs']
titles += ['3_abs', '3_rnk', 'mt_abs', 'mt_rnk', 'f_abs', 'f_rnk']

def component_stats_multi(output_dir):
  component_stats(output_dir, year_q=None)

def component_stats(output_dir, year_q=None):
  global titles
  year_q_list = []
  if not year_q:
    year_q_list = ['2012_1', '2013_1', '2014_1']
  else:
    year_q_list = [year_q]

  print "year_q_list", year_q_list
  edges, comps = {}, {}
  top_sims = {}
  gr = {}
  for year_q in year_q_list:
    filter_process(output_dir, year_q)
    top_sims.update(load_top_sims_from_log(output_dir, year_q, add_str='both'))

    all_grades = load_all_grades(output_dir, year_q)
    gr.update(get_graderank_dict(all_grades))

    comps_yq, edges_yq = load_components_info(output_dir, year_q)
    comps.update(comps_yq)
    edges.update(edges_yq)


  lair_dict, _, ta_all_stats_np, ta_uname_stats_np = get_ta_stats(output_dir, year_q=year_q)
  cross_sims, cross_names = load_top_sims_by_uname(top_sims)
  grps = get_grps(comps, edges)
  grp_comp_ind, indeg_ind, outdeg_ind = 0, 1, 2
  grade_list = [ASSGT_3, MT_IND, F_IND]
  info = []
  non_info = []
  unames_grp = [uname for grp in grps for uname in sorted(grp)] # flatten

  for uname in sorted(top_sims.keys()):
    info_uname = []
    num_commits = len(top_sims[uname].keys())

    # moss
    num_sims, frac_sims = 0, 0.0
    max_token, max_p_self, max_p_other = 0.0, 0.0, 0.0
    avg_token, avg_p_self, avg_p_other = 0.0, 0.0, 0.0
    start_sim_posix, end_sim_posix = 0.0, 0.0
    grp_i = -1
    if uname in unames_grp:
      if comps[uname][outdeg_ind] == 0:
        print "sink", uname, comps[uname]
        continue # ignore all sinks!!!!!!
      else:
        tot_cross_np = []
        for uname_other in edges[uname]:
          num_sims += len(edges[uname][uname_other].keys())
          cross_np = cross_sims[uname][uname_other]
          tot_cross_np.append(cross_np)
        frac_sims = float(num_sims)/num_commits

        # todo: include stats on type of commit? like max token, avg token, these things
        tot_cross_np = np.concatenate(tot_cross_np)
        _, _, max_token, max_p_self, max_p_other = np.amax(tot_cross_np, axis=0).tolist()
        _, _, avg_token, avg_p_self, avg_p_other = np.average(tot_cross_np, axis=0).tolist()
        start_sim_posix = np.amin(tot_cross_np[:,0])
        end_sim_posix = np.amax(tot_cross_np[:,0])

      grp_i = comps[uname][grp_comp_ind]

    info_uname += [int(uname), grp_i, num_sims, frac_sims]
    info_uname += [max_token, max_p_self, max_p_other]
    info_uname += [avg_token, avg_p_self, avg_p_other]
    info_uname += [start_sim_posix, end_sim_posix]

    # hours/commits on task
    min_posix, max_posix = int(min(top_sims[uname].keys())), int(max(top_sims[uname].keys()))
    num_days = (max_posix - min_posix)/float(day_length)
    num_hrs = (max_posix - min_posix)/float(day_length/24)
    info_uname +=  \
        [min_posix, #posix_to_datetime(float(min_posix)),
         max_posix, #posix_to_datetime(float(max_posix)),
         #min_posix, max_posix,
         num_commits,
         num_days, num_hrs]

    # grades
    if uname not in gr:
      print "no grade", uname
      continue
    for grade_name in grade_list:
      info_uname += [gr[uname][G_IND][grade_name], gr[uname][R_IND][grade_name]]

    if uname in unames_grp:
      info.append(info_uname)
    else:
      non_info.append(info_uname)
  

  info_np = np.array(info)
  non_info_np = np.array(non_info)
  draw_bars(output_dir, year_q_list, info_np, non_info_np)
  draw_bars(output_dir, year_q_list,
      np.array(filter(filter_by_online(True), info)),
      non_info_np,
      extra_info_np=np.array(filter(filter_by_online(False), info)))
  draw_timerange(output_dir, year_q_list, info, non_info)

  tot_grps = len(grps)
  def process_info(info_filtered):
    for info_uname in info_filtered:
      printout = []
      for x in info_uname:
        try:
          printout.append(float("{0:.2f}".format(x)))
        except:
          printout.append(x)
      print '\t'.join(map(str, printout))
    make_histograms(info_filtered)
    print

  ###### separate by group
  def filter_by_grp(grp_ind):
    def filt(info_uname):
      return info_uname[1] == grp_ind
    return filt

  # for grp_i in range(tot_grps):
  #   print ">>>>>>>>> grp ind %d (size: %d)" % (grp_i, len(grps[grp_i]))
  #   print '\t'.join(titles)
  #   info_by_grp = filter(filter_by_grp(grp_i), info)
  #   process_info(info_by_grp)
  #   plot_things(output_dir, year_q_list, info_filtered, group_name='grp')

  ###### separate by f_rank
  def filter_by_grade(less_than, thresh=0.5, grade_name=2, grade_type=R_IND):
    grade_ind = -2*len(grade_list)+len(grade_list)*grade_type+grade_name
    def filt(info_uname):
      if less_than:
        return info_uname[grade_ind] < thresh
      return info_uname[grade_ind] >= thresh
    return filt

  for compar, marker, lw in [(False, '^', 1), (True, 'o', 0)]:
    compar_str = 'fgrade_%s' % 'greater'
    if compar:
      compar_str = 'fgrade_%s' % 'less'

    print '\t'.join(titles)
    info_by_grade = filter(filter_by_grade(compar), info)
    plot_things(output_dir, year_q_list, info,
        group_name=compar_str, filter_fn=filter_by_grade,
        filter_args=[(compar, marker, lw)])

  plot_things(output_dir, year_q_list, info,
      group_name='fgrade', filter_fn=filter_by_grade,
      filter_args=[(True, '^', 1), (False, 'o', 0)])

  #[item for sublist in l for item in sublist] # flatten

  ###### separate by online/offline
  for online, marker, lw in [(True, '^', 1), (False, 'o', 0)]:
    print ">>>>>>>>> online: %s" % online
    print '\t'.join(titles)
    info_by_online = filter(filter_by_online(online), info)
    process_info(info_by_online)
    plot_things(output_dir, year_q_list, info,
        group_name='online%s' % online, filter_fn=filter_by_online,
        filter_args=[(online, marker, lw)])

  plot_things(output_dir, year_q_list, info,
      group_name='online', filter_fn=filter_by_online,
      filter_args=[(True, '^', 1), (False, 'o', 0)])
  
  plot_things(output_dir, year_q_list, info, group_name='all')

def filter_by_online(online):
  def filt(info_uname):
    if online:
      return info_uname[1] == 0 # assume grp 0 is the online one
    return info_uname[1] != 0
  return filt

def draw_bars(output_dir, year_q_list, info_np, non_info_np, extra_info_np=None):
  fig = plt.figure()
  ax1 = plt.gca()
  avgs, meds, stds = [], [], []
  non_avgs, non_meds, non_stds = [], [], []
  extra_avgs, extra_meds, extra_stds = [], [], []
  labels, label_xs = [], []
  xs, extra_xs, non_xs = [], [], []

  for gr_type in range(-6,0):
    avgs.append(np.average(info_np[:,gr_type], axis=0))
    meds.append(np.median(info_np[:,gr_type], axis=0))
    stds.append(np.std(info_np[:,gr_type], axis=0)/np.sqrt(info_np.shape[0]))
    if extra_info_np is not None:
      extra_avgs.append(np.average(extra_info_np[:,gr_type], axis=0))
      extra_meds.append(np.median(extra_info_np[:,gr_type], axis=0))
      extra_stds.append(np.std(extra_info_np[:,gr_type],axis=0)/np.sqrt(extra_info_np.shape[0]))

    non_avgs.append(np.average(non_info_np[:,gr_type], axis=0))
    non_meds.append(np.median(non_info_np[:,gr_type], axis=0))
    non_stds.append(np.std(non_info_np[:,gr_type], axis=0)/np.sqrt(non_info_np.shape[0]))

    if extra_info_np is not None:
      label_xs.append(2.5 +4*len(label_xs))
      labels.append(titles[gr_type])

      xs.append(label_xs[-1]-1)
      extra_xs.append(label_xs[-1])
      non_xs.append(label_xs[-1]+1)
    else:
      label_xs.append(2 +3*len(label_xs))
      labels.append(titles[gr_type])

      xs.append(label_xs[-1]-0.5)
      non_xs.append(label_xs[-1]+0.5)

  b = plt.bar(xs, avgs, width=1, color='r', yerr=stds, ecolor='k')
  if extra_info_np is not None:
    extra_b = plt.bar(extra_xs, extra_avgs, width=1, color='g', yerr=extra_stds, ecolor='k')
  non_b = plt.bar(non_xs, non_avgs, width=1, color='b', yerr=non_stds, ecolor='k')
  if extra_info_np is not None:
    ax1.legend([b[0], extra_b[0], non_b[0]], ['online sim', 'offline sim', 'baseline'])
  else:
    ax1.legend([b[0], non_b[0]], ['"cheating"', 'baseline'])

  ax1.set_xticks(np.array(label_xs)+0.5)
  ax1.set_xticklabels(labels)
  ax1.set_ylabel('Average grade on each assignment')

  ax1.set_title('%s Average grade comparison' % ('_'.join(year_q_list)))
  fig.tight_layout()
  fig_dest_prefix = "%s_group_histogram" % ('_'.join(year_q_list))
  if extra_info_np is not None:
    fig_dest_prefix += "_extra"
  fig_dest = os.path.join(output_dir, '%s.png' % fig_dest_prefix)
  print "Saving a histogram of scores", fig_dest
  fig.savefig(fig_dest)
  plt.close(fig)

def draw_timerange(output_dir, year_q_list, info, non_info):
  global day_length
  fig, axs = plt.subplots(2,2)
  starts = []
  for info_uname in info:
    uname = str(info_uname[uname_ind])
    uname_year, uname_q = uname[:4], uname[4:6]
    old_year_q = '%s_%s' % (int(uname_year), int(uname_q))
    #min_posix, max_posix = info_uname[start_posix_ind], info_uname[end_posix_ind]
    # when the similarities start
    sim_min_posix = info_uname[start_sim_posix_ind]
    sim_max_posix = info_uname[end_sim_posix_ind]
    sim_scale_min_posix = scale_days(sim_min_posix, old_year_q, new_year_q=max(year_q_list))
    sim_scale_max_posix = scale_days(sim_max_posix, old_year_q, new_year_q=max(year_q_list))

    min_posix = info_uname[start_posix_ind]
    max_posix = info_uname[end_posix_ind]
    scale_min_posix = scale_days(min_posix, old_year_q, new_year_q=max(year_q_list))
    scale_max_posix = scale_days(max_posix, old_year_q, new_year_q=max(year_q_list))
    starts.append(scale_min_posix)


    frac_sims = info_uname[3]
    axs[0,0].plot([sim_scale_min_posix, sim_scale_max_posix],
           [frac_sims, frac_sims], c='r', alpha=0.4)
    axs[0,0].plot([scale_min_posix, sim_scale_min_posix],
        [frac_sims]*2, c='r', marker='.', alpha=0.4, ls='--')
    axs[0,0].plot([sim_scale_max_posix, scale_max_posix],
        [frac_sims]*2, c='r', marker='.', alpha=0.4, ls='--')
                  

    axs[1,0].scatter(scale_min_posix, frac_sims, lw=0, c='r')
    # axs[1,0].plot([scale_min_posix, scale_max_posix],
    #          [frac_sims, frac_sims], c='r', marker='.', ls='--',alpha=0.4)
    axs[1,1].scatter(scale_max_posix, frac_sims, lw=0, c='r')

  non_starts = []
  for info_uname in non_info:
    uname = str(info_uname[uname_ind])
    uname_year, uname_q = uname[:4], uname[4:6]
    old_year_q = '%s_%s' % (int(uname_year), int(uname_q))
    min_posix, max_posix = info_uname[start_posix_ind], info_uname[end_posix_ind]
    scale_min_posix = scale_days(min_posix, old_year_q, new_year_q=max(year_q_list))
    scale_max_posix = scale_days(max_posix, old_year_q, new_year_q=max(year_q_list))
    non_starts.append(scale_min_posix)

  # histogram of start times
  posix_range = get_day_range(max(year_q_list),incr=day_length) # daily
  start_hist, _ = np.histogram(starts, bins=posix_range)
  norm_start_hist = start_hist/float(len(info))
  non_start_hist, _ = np.histogram(non_starts, bins=posix_range)
  norm_non_start_hist = non_start_hist/float(len(non_info))
  bar_width = day_length/4
  b = axs[0,1].plot(posix_range[:-1], norm_start_hist, color='r', marker='o')
  non_b = axs[0,1].plot(posix_range[:-1], norm_non_start_hist, color='b', marker='o')
  # b = axs[1].bar(posix_range[:-1], norm_start_hist,
  #           width=bar_width, color='r')
  # non_b = axs[1].bar(np.array(posix_range[:-1])+bar_width, norm_non_start_hist,
  #           width=bar_width, color='b')
  axs[0,1].set_xticks(posix_range)
  axs[0,1].set_xticklabels(map(lambda x: posix_to_datetime(x, format_str='%m/%d'), posix_range), fontsize=8, rotation=45)
  axs[0,1].set_xlabel('Start time')
  axs[0,1].set_ylabel('% students')
  axs[0,1].legend([b[0], non_b[0]], ['"cheating"', 'baseline'], fontsize=8)

  posix_range_half = get_day_range(max(year_q_list)) # twice a day
  axs[0,0].set_xlim(posix_range_half[0], posix_range_half[-1])
  axs[0,0].set_xticks(posix_range_half)
  axs[0,0].set_xticklabels(map(posix_to_datetime, posix_range_half), fontsize=8, rotation=45)
  axs[0,0].set_xlabel('Assignment work time.')
  axs[0,0].set_ylabel('Similarity fraction')

  axs[1,0].set_xlim(posix_range[0], posix_range[1])
  axs[1,0].set_xticks(posix_range)
  axs[1,0].set_xticklabels(map(lambda x: posix_to_datetime(x, format_str='%m/%d'), posix_range), fontsize=8, rotation=45)
  axs[1,0].set_xlabel('Start time')
  axs[1,0].set_ylabel('Similarity fraction')

  axs[1,1].set_xlim(posix_range[0], posix_range[1])
  axs[1,1].set_xticks(posix_range)
  axs[1,1].set_xticklabels(map(lambda x: posix_to_datetime(x, format_str='%m/%d'), posix_range), fontsize=8, rotation=45)
  axs[1,1].set_xlabel('End time')
  axs[1,1].set_ylabel('Similarity fraction')

  fig.tight_layout()
  fig_dest_prefix = "%s_group_timerange" % ('_'.join(year_q_list))
  fig_dest = os.path.join(output_dir, '%s.png' % fig_dest_prefix)
  print "Saving a time range of stuff", fig_dest
  fig.savefig(fig_dest)
  plt.close(fig)

def make_histograms(info, ignore_cols=[0,]):
  global titles
  new_info = []
  for info_uname in info:
    new_info.append([info_uname[i] \
                for i in range(len(titles)) \
                if i not in ignore_cols])
  info_np = np.array(new_info)
  print info_np.shape
  inds = [i for i in range(len(titles)) if i not in ignore_cols]
  print inds
  for i, title_i in enumerate(inds):
    hist, bin_edges = np.histogram(info_np[:,i],bins=20)
    print "%d: %s" % (title_i, titles[title_i])
    print bin_edges
    print hist

def plot_things(output_dir, year_q_list, info, 
    group_name=None, filter_fn=None, filter_args=None,
    x_inds=None, y_inds=None, c_inds=None):
  global titles
  if not group_name:
    group_name = 'all'
  if not x_inds:
    x_inds = range(1,17)
  if not y_inds:
    y_inds = range(1,17)
  if not c_inds:
    c_inds = range(17,23)
  for c_ind in c_inds:
    fig_all, ax_all = plt.subplots(len(y_inds), len(x_inds), figsize=(40, 40))
    c_info = np.array(map(lambda info_uname: info_uname[c_ind], info))
    max_c = max(np.amax(c_info), 1)
    m = set_colormap([0.0, 1.0]) # for coloring
    colors = m.to_rgba(c_info/float(max_c))
    ctitle = ''.join(titles[c_ind].split('\t'))
    for x_i, x_ind in enumerate(x_inds):
      for y_i, y_ind in enumerate(y_inds):
        plt_tup = (y_i, x_i)
        if len(x_inds) == 1: plt_tup = y_i
        if len(y_inds) == 1: plt_tup = x_i
        if filter_fn:
          for marker_i, marker, lw in filter_args:
            info_filter = filter(filter_fn(marker_i), info)
            x_info = np.array(map(lambda info_uname: info_uname[x_ind], info_filter))
            y_info = np.array(map(lambda info_uname: info_uname[y_ind], info_filter))
            ax_all[plt_tup].scatter(x_info, y_info, lw=lw, marker=marker, c=colors, alpha=0.4)
        else:
          x_info = np.array(map(lambda info_uname: info_uname[x_ind], info))
          y_info = np.array(map(lambda info_uname: info_uname[y_ind], info))
          ax_all[plt_tup].scatter(x_info, y_info, lw=0, c=colors, alpha=0.7)

        if x_ind >= 15:
          ax_all[plt_tup].set_xlim(0, 1)
        else:
          ax_all[plt_tup].set_xlim(np.amin(x_info), np.amax(x_info))
        ax_all[plt_tup].set_xticklabels(ax_all[plt_tup].get_xticks(), fontsize=8)
        ax_all[plt_tup].set_xlabel(''.join(titles[x_ind].strip().split('\t')), fontsize=6)

        if y_ind >= 15:
          ax_all[plt_tup].set_ylim(0, 1)
        else:
          ax_all[plt_tup].set_ylim(np.amin(y_info), np.amax(y_info))
        ax_all[plt_tup].set_yticklabels(ax_all[plt_tup].get_yticks(), fontsize=8)
        ax_all[plt_tup].set_ylabel(''.join(titles[y_ind].strip().split('\t')), fontsize=6)

    for x_i, x_ind in enumerate(x_inds):
      plt_tup = (-1,x_i) 
      if len(y_inds) == 1: plt_tup = x_i
      ax_all[plt_tup].set_xlabel(''.join(titles[x_ind].strip().split('\t')), fontsize=8)
      ax_all[plt_tup].set_xticklabels(map(int, ax_all[plt_tup].get_xticks()), fontsize=8)
    for y_i, y_ind in enumerate(y_inds):
      plt_tup = (y_i, 0) 
      if len(x_inds) == 1: plt_tup = y_i
      ax_all[plt_tup].set_ylabel(''.join(titles[y_ind].strip().split('\t')), fontsize=8)
      ax_all[plt_tup].set_yticklabels(map(int, ax_all[plt_tup].get_yticks()), fontsize=8)

    fig_all.suptitle('%s comparison' % ctitle)
    fig_all.tight_layout()
    fig_dest_prefix = "%s_group_info_%s_%s" % ('_'.join(year_q_list), group_name, ctitle)
    fig_dest = os.path.join(output_dir, '%s.png' % fig_dest_prefix)
    print "Saving a filtered fig", fig_dest
    fig_all.savefig(fig_dest)
    plt.close(fig_all)
  
def get_grps(comps, edges):
  components = {}
  for uname, (grp, ind, outd) in comps.iteritems():
    grp_uname = '%s_%s' % (grp, uname[:6])
    if grp == 0: # the online one
      grp_uname = "0"
    if grp_uname not in components:
      components[grp_uname] = []

    components[grp_uname].append(uname)

  components_list = []
  grp_nums = sorted(components.keys())
  for grp in grp_nums:
    print sorted(components[grp])
    components_list.append(components[grp])
  return components_list

def filter_process(output_dir, year_q):
  time_ind, commit_ind = 0, 1
  token_ind, p_self_ind, p_other_ind = 2, 3, 4

  #write_online_stats(output_dir, year_q)
  online_sims = load_online_stats(output_dir, year_q)
  for uname in online_sims:
    online_np = online_sims[uname][2]

  for add_str in ['both']:#, '', 'online_']:
    #print "top_sims type: %s" % add_str
    top_sims = load_top_sims_from_log(output_dir, year_q, add_str=add_str)
    cross_sims, cross_names = load_top_sims_by_uname(top_sims)
    num_sims = []
    num_maxes = []
    num_avgs = []
    uname_edges = {}
    unames = cross_sims.keys()
    unames.sort()
    for uname in unames:
      #print uname
      uname_others = cross_sims[uname].keys()
      uname_others.sort()
      for uname_other in uname_others:
        if add_str == '' and 'online' in uname_other:
          continue
        cross_np = cross_sims[uname][uname_other]
        _, _, max_token_ind, max_p_self_ind, max_p_other_ind = \
                  np.argmax(cross_np,axis=0).tolist()
        _, _, max_token, max_p_self, max_p_other = np.amax(cross_np,axis=0).tolist()
        _, _, avg_token, avg_p_self, avg_p_other = np.average(cross_np,axis=0).tolist()
        # print '\t', uname_other, cross_np.shape[0]
        # print '\t\t', max_token, max_p_other
        #if max_p_other < 20 and max_token < 250: continue
        if not check_thresh(max_token, max_p_self, max_p_other):
          continue
        #if max_p_other < 30: continue
        # print "%s->%s (%d)\tmax_token: %d (p_self+other: %s), max_p_other: %.2f (p_self+token: %s)" % \
        #     (uname, uname_other, cross_np.shape[0],
        #         max_token, cross_np[max_token_ind,[3,4]].tolist(),
        #         max_p_other, cross_np[max_p_other_ind,[3,2]].tolist())
        if (uname, uname_other) not in uname_edges:
          uname_edges[(uname, uname_other)] = []
          for commit_hash, moss_line in zip(cross_names[uname][uname_other], cross_np.tolist()):
            uname_edges[(uname, uname_other)].append('%s,%s,%s,%s' % \
                (uname, uname_other, commit_hash, ','.join(map(str,moss_line))))
        if (uname, uname_other) in [('2012010066', '2012010110'),('2012010026', '2012010235')]:
          #print top_sims[uname]
          pass
        # if max_p_other > 30:
        num_sims.append(cross_np.shape[0])
        num_maxes.append((max_token, max_p_self, max_p_other))
        num_avgs.append((avg_token, avg_p_self, avg_p_other))
        # if uname_other in online_sims:
        #   #print '\t', np.average(cross_np[:,token_ind]), np.average(cross_np[:,p_self_ind]), np.average(cross_np[:,p_other_ind])
        #   print '\t', np.amax(cross_np[:,token_ind]), np.amax(cross_np[:,p_self_ind]), np.amax(cross_np[:,p_other_ind])
    #histogram things
    if add_str == 'both':
      edge_f_name = '%s_edges.csv' % year_q
      with open(os.path.join(output_dir, edge_f_name), 'w') as f:
        uname_pairs = uname_edges.keys()
        uname_pairs.sort()
        for uname, uname_other in uname_pairs:
          edge_info_list = uname_edges[(uname, uname_other)]
          f.write('\n'.join(edge_info_list))
          f.write('\n')
        print "wrote", f.name
      short_dict = {}
      for uname, uname_other in uname_edges:
        if uname not in short_dict:
          short_dict[uname] = []
        short_dict[uname].append(uname_other)
      comps_with_edges, tot_grps = get_reachable_nodes(short_dict)

      comps_f_name = '%s_components.csv' % year_q
      with open(os.path.join(output_dir, comps_f_name), 'w') as f:
        unames = top_sims.keys()
        unames.sort()
        output_list = []
        for uname in unames:
          if uname not in comps_with_edges:
            # don't write "single" nodes
            # output_list.append(','.join((uname, str(tot_grps), '0', '0')))
            # tot_grps += 1
            pass
          else:
            output_list.append('%s,%s' % (uname, ','.join(map(str, comps_with_edges[uname]))))

        f.write('\n'.join(output_list))
        print "wrote", f.name

    # hist, bin_edges = np.histogram(num_sims, bins=np.linspace(0,100,num=10))
    # together = zip(hist.tolist(), bin_edges.tolist())
    # print "number of sims to each "
    # print '\n'.join(map(str, together))

def load_filter_edges(output_dir):
  filter_info = {}
  for year_q in ['2012_1', '2013_1', '2014_1']:
    edge_f_name = '%s_edges.csv' % year_q
    with open(os.path.join(output_dir, edge_f_name), 'w') as f:
      line = f.readline()
      line.strip()
      while line:
        if len(','.split(line)) == 2:
          uname, uname_other= ','.split(line)
          if uname not in filter_info:
            filter_info[uname] = {}
          commits, data = [], []
          line = f.readline()
          line.strip()
          while line and len(','.split(line)) > 2:
            commits.append(','.split(line)[0])
            data.append(map(float, ','.split(line)[1:]))
            line = f.readline()
          filter_info[uname][uname_other] = (commits, np.array(data))
  return filter_info

"""
DFS.
"""
def get_reachable_nodes(filter_info):
  connected_comps = []
  visited = set()
  edges_forward = {}
  edges_reverse = {}
  for uname in filter_info:
    try:
      edges_forward[uname] = filter_info[uname].keys()
    except: # filter_info is a simple list
      edges_forward[uname] = filter_info[uname]
    for uname_other in filter_info[uname]:
      if uname_other not in edges_reverse:
        edges_reverse[uname_other] = []
      edges_reverse[uname_other].append(uname)

  edges = {}
  for uname in edges_forward:
    edges[uname] = list(edges_forward[uname]) # copy list
  for uname in edges_reverse:
    if uname in edges:
      edges[uname] += edges_reverse[uname]
    else:
      edges[uname] = list(edges_reverse[uname])

  def dfs(uname, new_set):
    visited.add(uname)
    if uname not in edges: return
    for uname_other in edges[uname]:
      if uname_other not in visited:
        new_set.add(uname_other)
        dfs(uname_other, new_set)

  for uname in edges:
    if uname not in visited:
      new_comp = set([uname])
      dfs(uname, new_comp)
      connected_comps.append(new_comp)

  # calculate number of edges that nodes share
  comps_with_edge_count = {}
  connected_comps = map(list, connected_comps)
  #comp_lens = map(len, connected_comps)
  #for comp_ind in [i[0] for i in sorted(enumerate(comp_lens), key=lambda x:-x[1])]:

  for comp_ind, comp in enumerate(connected_comps):
    comp_ind += 1 # all off by one to indicate not online
    comp_list = list(comp)
    if 'online' in ','.join(comp_list):
      comp_ind = 0 # online group is grp_ind == 0

    comp_list.sort()
    print "comp in order", comp_ind, len(comp), comp_list
    for uname in comp_list:
      in_degree, out_degree = 0, 0
      if uname in edges_forward:
        out_degree = len(edges_forward[uname])
      if uname in edges_reverse:
        in_degree = len(edges_reverse[uname])
      comps_with_edge_count[uname] = (comp_ind, in_degree, out_degree)

  # for comp_edge in comps_with_edge_count:
  #   print comp_edge
  return comps_with_edge_count, len(connected_comps)
