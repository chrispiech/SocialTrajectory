from helper import *
from git_helper import *
from moss_tool import *
from ta_stats import *
import matplotlib.colors as cl
import matplotlib.cm as cmx

# collaboration
uname_ind, grp_ind, num_sims_ind = 0, 1, 2
frac_sims_ind, b4_frac_sims_ind, after_frac_sims_ind = 3, 4, 5
max_t_ind, max_ps_ind, max_po_ind = 6, 7, 8
avg_t_ind, avg_ps_ind, avg_po_ind = 9, 10, 11
start_sim_posix_ind, end_sim_posix_ind = 12, 13
# all
start_posix_ind, end_posix_ind = 14, 15
commits_ind, hrs_ind = 16, 17
avg_work_ind, max_work_ind = 18, 19
# ta
ta_visits_ind, ta_hrs_ind = 20, 21
ta_v_during_ind, ta_h_during_ind = 22, 23
ta_v_b4_ind, ta_h_b4_ind = 24, 25
# grades
assgt1_g_ind, assgt1_r_ind = 26, 27
assgt2_g_ind, assgt2_r_ind = 28, 29
assgt3_g_ind, assgt3_r_ind = 30, 31
mt_g_ind, mt_r_ind = 32, 33
f_g_ind, f_r_ind = 34, 35
gr_st_ind = assgt3_g_ind # always have gr_end be the last in the list
last_ind = f_r_ind

titles = []
titles += ['uname', 'grp', 'n_sims']
titles += ['frac', 'b4_frac', 'after_frac']
titles += ['max_t', 'max_ps', 'max_po']
titles += ['avg_t', 'avg_ps', 'avg_po']
titles += ['st_sim', 'end_sim']
titles += ['st', 'end']
titles += ['commits', 'hrs']
titles += ['avg sess', 'max sess']
titles += ['ta visits', 'ta hrs']
titles += ['ta visits during', 'ta hrs during']
titles += ['ta visits before', 'ta hrs before']
titles += ['1_abs', '1_rnk', '2_abs', '2_rnk']
titles += ['3_abs', '3_rnk', 'mt_abs', 'mt_rnk', 'f_abs', 'f_rnk']

grade_list = [ASSGT_1, ASSGT_2, ASSGT_3, MT_IND, F_IND]

def component_stats_multi(output_dir):
  component_stats(output_dir, year_q=None)

TA_TYPE = B4_MT_TIME
TA_TYPE = BT_MT_FINAL_TIME
TA_TYPE = B4_ASSGT_TIME
def per_year_stats(year_q_list, info, non_info):
  for year_q in year_q_list:
    year, q = year_q.split('_')
    uname_yearq = '%s%02d' % (year, int(q))
    info_filt = filter(lambda info_uname: uname_yearq in str(info_uname[uname_ind]),
                    info)
    non_info_filt = filter(lambda info_uname: uname_yearq in str(info_uname[uname_ind]),
                    non_info)
    print year_q
    uniq_ = set(map(lambda x:x[0],info_filt))
    uniq_.update(set(map(lambda x:x[0],non_info_filt)))
    print "tot students", len(uniq_)
    print "num students", len(info_filt), len(non_info_filt)
    print "num commits", sum(map(lambda iu: iu[commits_ind], info_filt)), \
                         sum(map(lambda iu: iu[commits_ind], non_info_filt))
    info_filt_np = np.array(info_filt)
    non_info_filt_np = np.array(non_info_filt)
    all_info_np = np.array(info_filt + non_info_filt)
    print "max commits", np.amax(all_info_np[:,commits_ind])
    print "average commits", np.average(all_info_np[:,commits_ind])
    print "stdev commits", np.std(all_info_np[:,commits_ind])

def component_stats(output_dir, year_q=None):
  global titles
  year_q_list = []
  if not year_q:
    year_q_list = ['2012_1', '2013_1', '2014_1']
  else:
    year_q_list = [year_q]
  print "year_q_list", year_q_list
  for year_q in year_q_list:
    filter_process(output_dir, year_q)

  info, non_info = load_info_noninfo(output_dir, year_q_list)
  info_np = np.array(info)
  non_info_np = np.array(non_info)
  timesim_thresh = separate_kmeans_plot(output_dir, year_q_list,
      info_np, start_sim_posix_ind, frac_sims_ind, titles) 
  sim_thresh = separate_kmeans_plot(output_dir, year_q_list,
      info_np, start_sim_posix_ind, frac_sims_ind, titles, use_y=True) 
  
  # prints out some stats
  per_year_stats(year_q_list, info, non_info)

  print "verify: len info: %s, len non_info: %s" % (len(info), len(non_info))
  b4sim_thresh = separate_kmeans_plot(output_dir, year_q_list,
          info_np,
          # np.array(filter(filter_by_type(STUCK, sim_thresh, timesim_thresh), info) + \
          #     filter(filter_by_type(REFERENCE, sim_thresh, timesim_thresh), info)),
          b4_frac_sims_ind, frac_sims_ind, titles)
  time_thresh = separate_kmeans_plot(output_dir, year_q_list,
      np.concatenate((info_np, non_info_np)), start_posix_ind, f_r_ind, titles,
      plotstr='all')
  hrs_thresh = separate_kmeans_plot(output_dir, year_q_list,
      np.concatenate((info_np, non_info_np)), hrs_ind, f_r_ind, titles,
      plotstr='all')
  commits_thresh = separate_kmeans_plot(output_dir, year_q_list,
      np.concatenate((info_np, non_info_np)), commits_ind, f_r_ind, titles,
      plotstr='all')
  print "info threshes: time: (%s) %s, frac sim: %s" % (timesim_thresh, posix_to_datetime(timesim_thresh), sim_thresh)
  print "all info threshes: start time: (%s) %s, hrs worked: %s, commits: %s" % (time_thresh, posix_to_datetime(time_thresh), hrs_thresh, commits_thresh)

  print "with no fracsim thresh"
  prob_cheat(output_dir, year_q_list, info_np, non_info_np, include_point=time_thresh)
  print "with fracsim thresh"
  prob_cheat(output_dir, year_q_list, info_np, non_info_np, include_point=time_thresh, sim_thresh=sim_thresh)
  grade_over_time(output_dir, year_q_list, info_np, non_info_np, include_point=time_thresh)
  grade_over_ta_time(output_dir, year_q_list, info_np, non_info_np, include_point=time_thresh)
  scattergrade(output_dir, year_q_list, info, non_info, sim_thresh, time_thresh)

  draw_timerange(output_dir, year_q_list, info, non_info, sim_thresh, timesim_thresh)
  for stat_type in [STAT_GR, STAT_TA, STAT_TIME]:
    draw_bars(output_dir, year_q_list, [info_np], non_info_np, stat_type=stat_type)
    draw_bars(output_dir, year_q_list,
                [np.array(filter(filter_by_sim(True,  sim_thresh), info)),
                 np.array(filter(filter_by_sim(False, sim_thresh), info))],
              non_info_np,
              typestr='sim', stat_type=stat_type)
    draw_bars(output_dir, year_q_list,
                [np.array(filter(filter_by_time(True,  timesim_thresh, True), info)),
                 np.array(filter(filter_by_time(False, timesim_thresh, True), info))],
              non_info_np,
              typestr='timesim', stat_type=stat_type)
    draw_bars(output_dir, year_q_list,
                [np.array(filter(filter_by_time(True,  time_thresh, False), info)),
                 np.array(filter(filter_by_time(False, time_thresh, False), info))],
              non_info_np,
              typestr='timereg', stat_type=stat_type)
    all_info = info + non_info
    draw_bars(output_dir, year_q_list,
              [np.array(filter(filter_by_time(True,  time_thresh, False), all_info))],
              np.array(filter(filter_by_time(False, time_thresh, False), all_info)),
              typestr='timeregall2', stat_type=stat_type)
    draw_bars(output_dir, year_q_list,
                [np.array(filter(filter_by_work(True,  hrs_thresh), info)),
                 np.array(filter(filter_by_work(False, hrs_thresh), info))],
              non_info_np,
              typestr='worksim', stat_type=stat_type)
    draw_bars(output_dir, year_q_list,
              [np.array(filter(filter_by_work(False,  hrs_thresh), all_info))],
              np.array(filter(filter_by_work(True, hrs_thresh), all_info)),
              typestr='workregall2', stat_type=stat_type)
    draw_bars(output_dir, year_q_list,
              [np.array(filter(filter_by_gr(True,  mt_r_ind), all_info))],
              np.array(filter(filter_by_gr(False, mt_r_ind), all_info)),
              typestr='mtregall2', stat_type=stat_type)
    draw_bars(output_dir, year_q_list,
              [np.array(filter(filter_by_gr(True, f_r_ind), all_info))],
              np.array(filter(filter_by_gr(False, f_r_ind), all_info)),
              typestr='fregall2', stat_type=stat_type)
    draw_bars(output_dir, year_q_list,
                [np.array(filter(filter_by_time(True,  time_thresh, False),  info)),
                 np.array(filter(filter_by_time(False, time_thresh, False), info)),
                 np.array(filter(filter_by_time(True,  time_thresh, False), non_info)),
                 np.array(filter(filter_by_time(False, time_thresh, False), non_info))],
              non_info_np,
              typestr='timeregall', stat_type=stat_type)
    draw_bars(output_dir, year_q_list,
                [np.array(filter(filter_by_online(True), info)),
                 np.array(filter(filter_by_online(False), info))],
              non_info_np,
              typestr='online', stat_type=stat_type)
    # draw_bars(output_dir, year_q_list,
    #             [np.array(filter(filter_by_type(PREMEDITATED, sim_thresh, timesim_thresh), info)),
    #              np.array(filter(filter_by_type(STUCK,        sim_thresh, timesim_thresh), info)),
    #              np.array(filter(filter_by_type(PANICKER,     sim_thresh, timesim_thresh), info)),
    #              np.array(filter(filter_by_type(REFERENCE,    sim_thresh, timesim_thresh), info))],
    #           non_info_np, stat_type=stat_type)
  print "exiting component stats"
  return

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
    global grade_list
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
      return info_uname[grp_ind] == 0 # assume grp 0 is the online one
    return info_uname[grp_ind] != 0
  return filt

"""
start_type:
    True: late start
    False: regular start
"""
def filter_by_time(start_type, late_thresh, sim_start):
  def filt(info_uname):
    if sim_start:
      late_start = bool(info_uname[start_sim_posix_ind] >= late_thresh)
    else: # regular start, not sim
      late_start = bool(info_uname[start_posix_ind] >= late_thresh)
    return late_start == start_type
  return filt

def filter_by_work(work_type, hrs_thresh):
  def filt(info_uname):
    work_hard = bool(info_uname[hrs_ind] >= hrs_thresh)
    return work_type == work_hard
  return filt

def filter_by_gr(gr_type, gr_ind, gr_thresh=0.25):
  def filt(info_uname):
    low_score = bool(info_uname[gr_ind] <= gr_thresh)
    return low_score == gr_type
  return filt

"""
sim_type:
  True: >= sim_thresh
  False: < sim_thresh
"""
def filter_by_sim(sim_type, sim_thresh):
  def filt(info_uname):
    exceeds_thresh = bool(info_uname[frac_sims_ind] >= sim_thresh)
    return exceeds_thresh == sim_type
  return filt

REFERENCE = 0
STUCK = 1
PREMEDITATED = 2
PANICKER = 3
b4_sim_thresh = 0.413791565712
def filter_by_type(type_ind, sim_thresh, late_thresh):
  def filt(info_uname):
    large_sim = bool(info_uname[frac_sims_ind] >= sim_thresh)
    # around 3am on T-3 day
    late_start = bool(info_uname[start_sim_posix_ind] >= late_thresh)
    b4_sim = bool(info_uname[b4_frac_sims_ind] >= b4_sim_thresh)
    poss_type = int(large_sim)*2 + int(late_start)
    if large_sim:
      poss_type = int(large_sim)*2 + int(late_start)
    else:
      poss_type = int(large_sim)*2 + int(b4_sim)
    #poss_type = int(large_sim)*2 + int(b4_sim)
    # print "type check?", info_uname[uname_ind], large_sim, late_start, poss_type, \
    #     "typeind", type_ind, "equal?", poss_type == type_ind
    return poss_type == type_ind
  return filt

COLOR_TYPES = ['m', 'g', 'r', 'c']
NONCOLOR_TYPE = 'b'
def color_by_type(info_uname, sim_thresh, late_thresh):
  if filter_by_type(REFERENCE, sim_thresh, late_thresh)(info_uname):
    return COLOR_TYPES[REFERENCE]
  if filter_by_type(STUCK, sim_thresh, late_thresh)(info_uname):
    return COLOR_TYPES[STUCK]
  if filter_by_type(PREMEDITATED, sim_thresh, late_thresh)(info_uname):
    return COLOR_TYPES[PREMEDITATED]
  if filter_by_type(PANICKER, sim_thresh, late_thresh)(info_uname):
    return COLOR_TYPES[PANICKER]

STAT_GR = 0
STAT_TA = 1
STAT_TIME = 2
def draw_bars(output_dir, year_q_list, info_np_list, non_info_np, typestr=None, stat_type=0):
  avg_lists, med_lists, std_lists = [], [], []
  t_lists, p_lists = [], []
  x_lists = []
  for info_np in info_np_list:
    avg_lists.append([])
    med_lists.append([])
    std_lists.append([])
    x_lists.append([])
    t_lists.append([])
    p_lists.append([])
  if stat_type == STAT_TA:
    # remove all the zeros in each set first!
    nz_info_np_list = []
    for info_np in info_np_list:
      nz_info_np = info_np[np.nonzero(info_np[:,ta_visits_ind])[0],:]
      nz_info_np_list.append(nz_info_np)
    nz_non_info_np = non_info_np[np.nonzero(non_info_np[:,ta_visits_ind])[0],:]

    info_np_list = nz_info_np_list
    non_info_np = nz_non_info_np

  print "num people in each set", map(lambda info_np: info_np.shape[0], info_np_list), \
      "baseline", non_info_np.shape[0]
  non_avgs, non_meds, non_stds = [], [], []
  non_xs = []
  labels, label_xs = [], []

  stat_str = ''
  bar_indices = []
  if stat_type == STAT_GR:
    bar_indices = range(-6, 0)
    stat_str = 'grade'
  elif stat_type == STAT_TA:
    bar_indices = [ta_visits_ind, ta_hrs_ind]
    stat_str = 'ta'
  elif stat_type == STAT_TIME:
    bar_indices = [commits_ind, hrs_ind, avg_work_ind, max_work_ind]
    stat_str = 'time'
  else:
    print "error: stat type not recognized for bar"
    return

  compare_other = bool(typestr and 'sim' in typestr) and stat_type == STAT_GR # or len(info_np_list) == 2
  if compare_other:
    print "comparing to each other, not to baseline"
  for bar_index in bar_indices:
    for i, info_np in enumerate(info_np_list):
      avg_lists[i].append(np.average(info_np[:,bar_index], axis=0))
      med_lists[i].append(np.median(info_np[:,bar_index], axis=0))
      std_lists[i].append(np.std(info_np[:,bar_index], axis=0)/np.sqrt(info_np.shape[0]))
      if compare_other:
        t, p = spstats.ttest_ind(info_np[:,bar_index], info_np_list[int(not i)][:,bar_index], axis=0, equal_var=False)
      else:
        t, p = spstats.ttest_ind(info_np[:,bar_index], non_info_np[:,bar_index], axis=0, equal_var=False)
      t_lists[i].append(t)
      p_lists[i].append(p)


    non_avgs.append(np.average(non_info_np[:,bar_index], axis=0))
    non_meds.append(np.median(non_info_np[:,bar_index], axis=0))
    non_stds.append(np.std(non_info_np[:,bar_index], axis=0)/np.sqrt(non_info_np.shape[0]))

    if len(info_np_list) % 2 == 0:
      label_xs.append(2 + (2+len(info_np_list))*len(label_xs))
      non_xs.append(label_xs[-1]+len(info_np_list)/2)
    else:
      label_xs.append(2.5 + (2+len(info_np_list))*len(label_xs))
      non_xs.append(label_xs[-1]+len(info_np_list)/2+1)
    labels.append(titles[bar_index])
    for i, info_np in enumerate(info_np_list):
      shift = i - len(info_np_list)/2
      if len(info_np_list) % 2 == 0:
        x_lists[i].append(label_xs[-1]+shift)
      else:
        x_lists[i].append(label_xs[-1]+shift)

  # start drawing
  if stat_type == STAT_GR: # draw on one plot
    fig = plt.figure()
    ax1 = plt.gca()
  else:
    fig, axs = plt.subplots(1, len(bar_indices))
  # plot bars
  b_list = []
  color_list = ['r', 'g', 'c', 'm']
  for bar_index, _ in enumerate(bar_indices): # the stat type iterator
    if stat_type != STAT_GR or bar_index in [3,5]:
      print labels[bar_index]
      print "avg:", map(lambda j: avg_lists[j][bar_index], range(len(info_np_list))), "vs:", non_avgs[bar_index]
      print "med:", map(lambda j: med_lists[j][bar_index], range(len(info_np_list))), "vs:", non_meds[bar_index]
      print "std:", map(lambda j: std_lists[j][bar_index], range(len(info_np_list))), "vs:", non_stds[bar_index]
      print "t  :", map(lambda j:   t_lists[j][bar_index], range(len(info_np_list)))
      print "p  :", map(lambda j:   p_lists[j][bar_index], range(len(info_np_list)))
    for i, info_np in enumerate(info_np_list): # the data set iterator
      if stat_type == STAT_GR:
        b_list.append(ax1.bar(
          x_lists[i][bar_index], avg_lists[i][bar_index], width=1,
          color=color_list[i], yerr=std_lists[i][bar_index], ecolor='k'))
      else: # use the first set of x locations for each axis.
        b_list.append(axs[bar_index].bar(
          x_lists[i][0], avg_lists[i][bar_index], width=1,
          color=color_list[i], yerr=std_lists[i][bar_index], ecolor='k'))
    if stat_type == STAT_GR:
      b_list.append(ax1.bar(
        non_xs[bar_index], non_avgs[bar_index], width=1,
        color='b', yerr=non_stds[bar_index], ecolor='k'))
    else: # use the first set of x locations for each axis.
      b_list.append(axs[bar_index].bar(
        non_xs[0], non_avgs[bar_index], width=1,
        color='b', yerr=non_stds[bar_index], ecolor='k'))

  # set labels
  if stat_type == STAT_GR:
    ax1.set_xticks(np.array(label_xs)+0.5)
    ax1.set_xticklabels(labels)
  else:
    for bar_index, _ in enumerate(bar_indices):
      # axs[bar_index].set_xticks(np.array(label_xs)+0.5)
      # axs[bar_index].set_xticklabels(labels[bar_index])
      axs[bar_index].set_xlabel(labels[bar_index])

  if stat_type == STAT_GR:
    ax1.set_ylabel('Average %s on each assignment' % stat_str)
    ax1.set_title('%s Average %s comparison' % ('_'.join(year_q_list), stat_str))
  else:
    fig.suptitle('%s Average %s comparison' % ('_'.join(year_q_list), stat_str))
    for bar_index, label in enumerate(labels):
      axs[bar_index].set_ylabel('Average %s' % label)

  # add legend
  fig.tight_layout()
  fig.subplots_adjust(bottom=0.08)
  legend_names = []
  if len(info_np_list) == 1:
    legend_names = ['cheating', 'baseline']
  if len(info_np_list) == 2:
    if typestr and 'time' in typestr:
      if 'sim' in typestr:
        legend_names = ['late start sim', 'early start sim', 'baseline']
      else:
        legend_names = ['late start', 'early start', 'baseline']
        late_times = info_np_list[0][:, (start_sim_posix_ind, frac_sims_ind)]
        early_times = info_np_list[1][:,(start_sim_posix_ind, frac_sims_ind)]

    else:
      if typestr and 'sim' in typestr:
        legend_names = ['high sim', 'low sim', 'baseline']
      else:
        legend_names = ['online sim', 'offline sim', 'baseline']
  if len(info_np_list) == 4:
    if typestr and 'time' in typestr:
      legend_names = ['"cheating" late start', '"cheating" early start', 'baseline late start', 'baseline early start', 'baseline']
    else:
      legend_names = ['premeditated', 'stuck', 'panicker', 'reference', 'baseline']

  # for the entire plot, so use fig
  fig.legend(b_list, legend_names,
      bbox_to_anchor=(0.5,0), # praise be I don't have to use this
      ncol=len(legend_names), loc='lower center', fontsize=8)

  fig_dest_prefix = "%s_group_histogram_%s" % ('_'.join(year_q_list), stat_str)
  if typestr:
    fig_dest_prefix += "_%s" % typestr
  else:
    if len(info_np_list) == 2:
      fig_dest_prefix += "_online"
    if len(info_np_list) == 4:
      fig_dest_prefix += "_type"
  # if stat_type == STAT_TA:
  #   fig_dest_prefix += "%s" % ta_bounds_str[TA_TYPE]
  fig_dest = os.path.join(output_dir, '%s.png' % fig_dest_prefix)
  print "Saving a histogram of scores", fig_dest
  fig.savefig(fig_dest)
  plt.close(fig)

def scattergrade(output_dir, year_q_list, info, non_info, sim_thresh, time_thresh, stat_type=0):
  x_indices = []
  stat_str = ''
  if stat_type == STAT_TA:
    x_indices = [ta_visits_ind, ta_hrs_ind]
    stat_str = 'ta'
  else:
    x_indices = [frac_sims_ind]

  y_indices = range(-6, 0)[1::2]

  fig, axs = plt.subplots(len(y_indices)+1, len(x_indices), figsize=(10,10))
  non_info_np = np.array(non_info)
  # for type_ind in [REFERENCE, STUCK, PREMEDITATED, PANICKER]:
  #   if type_ind not in [STUCK, PANICKER]: continue
    #info_type_np = np.array(filter(filter_by_type(type_ind, sim_thresh, time_thresh), info))
  for type_ind in [0, 1]:
    info_type_np = np.array(filter(filter_by_time(bool(type_ind), time_thresh, False), info))
    print "shapes info", info_type_np.shape, "noninfo", non_info_np.shape
    color_type = COLOR_TYPES[type_ind]
    for x, x_index in enumerate(x_indices):
      for y, y_index in enumerate(y_indices):
        if len(x_indices) > 1:
          axs[y, x].scatter(info_type_np[:,x_index], info_type_np[:,y_index],
              c=color_type, lw=0)
        else:
          axs[y].scatter(info_type_np[:,x_index], info_type_np[:,y_index],
              c=color_type, lw=0)
      if len(x_indices) > 1:
        axs[-1, x].scatter(info_type_np[:,x_index],
          info_type_np[:,f_r_ind] - info_type_np[:,mt_r_ind], c=color_type, lw=0)
      else:
        axs[-1].scatter(info_type_np[:,x_index],
          info_type_np[:,f_r_ind] - info_type_np[:,mt_r_ind], c=color_type, lw=0)

  for y, y_index in enumerate(y_indices):
    for x, x_index in enumerate(x_indices):
      x_tup = (y,x)
      if len(x_indices) == 1:
        x_tup = y
      axs[x_tup].set_ylim(0.0, 1.0)
      axs[x_tup].set_ylabel('%s grade' % titles[y_index])
      axs[x_tup].set_xlabel(titles[x_index])
      axs[x_tup].set_xlim(0.0, axs[x_tup].get_xlim()[1])

  # difference graph, the last one
  for x, x_index in enumerate(x_indices):
    x_tup = (-1,x)
    if len(x_indices) == 1: x_tup = -1
    axs[x_tup].set_ylabel('Final - MT Delta')
    axs[x_tup].set_xlabel(titles[x_index])
    axs[x_tup].set_xlim(0.0, axs[x_tup].get_xlim()[1])
    axs[x_tup].axhline(y=0, ls='dashed', color='k', alpha=0.5)

  fig.tight_layout()
  fig_prefix = '%s_group_gradescatter_%s' % ('_'.join(year_q_list), stat_str)
  if stat_type == STAT_TA:
    print "TA BOUNDS STR", ta_bounds_str[TA_TYPE]
    fig_prefix += "%s" % ta_bounds_str[TA_TYPE]
  fig_dest = os.path.join(output_dir, '%s.png' % fig_prefix)
  print "Saving scatter vs grade", fig_dest
  fig.savefig(fig_dest)
  plt.close(fig)

def draw_timerange(output_dir, year_q_list, info, non_info, sim_thresh=None, time_thresh =None):
  if not sim_thresh or not time_thresh:
    print "did not call with time or sim thresh, sad"
    return
  global day_length
  fig, axs = plt.subplots(2,2)
  starts = []
  for info_uname in info:
    uname = str(info_uname[uname_ind])
    uname_year, uname_q = uname[:4], uname[4:6]
    old_year_q = '%s_%s' % (int(uname_year), int(uname_q))
    # the frac of work before the first sim commit
    b4_frac_sims = info_uname[b4_frac_sims_ind]
    after_frac_sims = info_uname[after_frac_sims_ind]
    frac_sims = info_uname[frac_sims_ind]
    #min_posix, max_posix = info_uname[start_posix_ind], info_uname[end_posix_ind]
    # when the similarities start
    sim_min_posix = info_uname[start_sim_posix_ind]
    sim_max_posix = info_uname[end_sim_posix_ind]
    sim_scale_min_posix, sim_scale_max_posix = sim_min_posix, sim_max_posix
    # sim_scale_min_posix = scale_days(sim_min_posix, old_year_q, new_year_q=max(year_q_list))
    # sim_scale_max_posix = scale_days(sim_max_posix, old_year_q, new_year_q=max(year_q_list))

    min_posix = info_uname[start_posix_ind]
    max_posix = info_uname[end_posix_ind]
    scale_min_posix, scale_max_posix = min_posix, max_posix
    # scale_min_posix = scale_days(min_posix, old_year_q, new_year_q=max(year_q_list))
    # scale_max_posix = scale_days(max_posix, old_year_q, new_year_q=max(year_q_list))
    starts.append(scale_min_posix)
    
    #print uname, sim_min_posix, sim_max_posix, frac_sims
    # if frac_sims > 1.0:
    #   axs[0,0].plot([sim_scale_min_posix, sim_scale_max_posix],
    #          [frac_sims, frac_sims], c='b', alpha=0.4)
    # else:
    #   # axs[0,0].plot([sim_scale_min_posix, sim_scale_max_posix],
    #   #        [frac_sims, frac_sims], c='r', alpha=0.4)
    #   pass
    # axs[0,0].plot([scale_min_posix, sim_scale_min_posix],
    #     [frac_sims]*2, c='r', marker='.', alpha=0.4, ls='-')
    # axs[0,0].plot([sim_scale_max_posix, scale_max_posix],
    #     [frac_sims]*2, c='r', marker='.', alpha=0.4, ls='--')
                  
    # adjust colors
    color_type = color_by_type(info_uname, sim_thresh, time_thresh)
    #print "types?", uname, types

    #axs[0,0].scatter(sim_scale_max_posix, frac_sims, lw=0, c=color_type)
    axs[0,0].scatter(b4_frac_sims, frac_sims, lw=0, c=color_type)
    axs[1,0].scatter(after_frac_sims, frac_sims, lw=0, c=color_type)
    #axs[1,0].scatter(scale_min_posix, frac_sims, lw=0, c=color_type)
    #axs[1,1].scatter((sim_scale_min_posix-scale_min_posix)/float(day_length/24), frac_sims, lw=0, c=color_type)
    axs[1,1].scatter(sim_scale_min_posix, frac_sims, lw=0, c=color_type)

  # non_starts = []
  # for info_uname in non_info:
  #   uname = str(info_uname[uname_ind])
  #   uname_year, uname_q = uname[:4], uname[4:6]
  #   old_year_q = '%s_%s' % (int(uname_year), int(uname_q))
  #   min_posix, max_posix = info_uname[start_posix_ind], info_uname[end_posix_ind]
  #   scale_min_posix = scale_days(min_posix, old_year_q, new_year_q=max(year_q_list))
  #   scale_max_posix = scale_days(max_posix, old_year_q, new_year_q=max(year_q_list))
  #   non_starts.append(scale_min_posix)
  non_starts = np.array(non_info)[:,start_posix_ind].tolist()

  # histogram of start times
  posix_range = get_day_range(max(year_q_list),plus_minus=[0,2], incr=day_length) # daily
  start_hist, _ = np.histogram(starts, bins=posix_range)
  norm_start_hist = start_hist/float(len(info))#+len(non_info))
  non_start_hist, _ = np.histogram(non_starts, bins=posix_range)
  norm_non_start_hist = non_start_hist/float(len(non_info))#+len(info))
  bar_width = day_length/4
  print "sum hist", np.sum(norm_start_hist), "sum non hist", np.sum(norm_non_start_hist)
  b = axs[0,1].plot(posix_range[:-1], norm_start_hist, color='r', marker='^')
  axs[0,1].set_ylabel('% students in collab. group')
  axs[0,1].set_ylim(0.0, 0.20)
  axs[0,1].set_yticks(np.linspace(0.0, 0.20, 5))
  ax2 = axs[0,1].twinx()
  non_b = ax2.plot(posix_range[:-1], norm_non_start_hist, color='b', marker='o')
  ax2.set_ylabel('% students in baseline group')
  ax2.set_ylim(0.0, 0.20)
  ax2.set_yticks(np.linspace(0.0, 0.20, 5))
  # b = axs[0,1].plot(posix_range[:-1], np.cumsum(norm_start_hist), color='r', marker='o')
  # non_b = axs[0,1].plot(posix_range[:-1], np.cumsum(norm_non_start_hist), color='b', marker='o')
  # b = axs[1].bar(posix_range[:-1], norm_start_hist,
  #           width=bar_width, color='r')
  # non_b = axs[1].bar(np.array(posix_range[:-1])+bar_width, norm_non_start_hist,
  #           width=bar_width, color='b')
  axs[0,1].spines['top'].set_visible(False)
  ax2.spines['top'].set_visible(False)
  axs[0,1].tick_params(axis='x',which='both',top='off')
  ax2.tick_params(axis='x',which='both',top='off')
  axs[0,1].set_xticks(posix_range)
  ax2.set_xticks(posix_range)
  #axs[0,1].set_xticklabels(map(lambda x: posix_to_datetime(x, format_str='%m/%d'), posix_range), fontsize=8, rotation=45)
  axs[0,1].set_xticklabels(map(lambda x: get_t_minus(x, max(year_q_list)), posix_range), fontsize=8, rotation=45)
  axs[0,1].set_xlabel('Start time')
  #fig.subplots_adjust(bottom=0.05)
  axs[0,1].legend([b[0],non_b[0]], ["collaboration", "baseline"],
      bbox_to_anchor=(0.5,1.05),ncol=2,loc='upper center', fontsize=8)
  #axs[0,1].legend([b[0], non_b[0]], ["collaboration", 'baseline'], fontsize=8)

  #posix_range_half = get_day_range(max(year_q_list),) # twice a day
  posix_range_half = posix_range
  # axs[0,0].set_xlim(posix_range_half[0], posix_range_half[-1])
  # axs[0,0].set_xticks(posix_range_half)
  # axs[0,0].set_xticklabels(map(lambda x: posix_to_datetime(x, format_str='%m/%d'), posix_range), fontsize=8, rotation=45)
  axs[0,0].set_xlim(0.0, 1.0)
  #axs[0,0].set_xlabel('Last similarity time')
  axs[0,0].set_xlabel('Fraction commits before first cheat')
  axs[0,0].set_ylim(0.0, 1.0)
  axs[0,0].set_ylabel('Similarity fraction')

  # axs[1,0].set_xlim(posix_range[0], posix_range[1])
  # axs[1,0].set_xticks(posix_range)
  # axs[1,0].set_xticklabels(map(lambda x: posix_to_datetime(x, format_str='%m/%d'), posix_range), fontsize=8, rotation=45)
  # axs[1,0].set_xlabel('Overall start time')
  axs[1,0].set_xlim(0.0, 1.0)
  axs[1,0].set_xlabel('Fraction commits after last cheat')
  axs[1,0].set_ylim(0.0, 1.0)
  axs[1,0].set_ylabel('Similarity fraction')

  #axs[1,1].set_xlim(0,250)
  axs[1,1].set_xlabel('Time bt start and cheat start')
  axs[1,1].set_xlim(posix_range[0], posix_range[1])
  axs[1,1].set_xticks(posix_range)
  axs[1,1].set_xticklabels(map(lambda x: posix_to_datetime(x, format_str='%m/%d'), posix_range), fontsize=8, rotation=45)
  axs[1,1].set_xlabel('Start cheat time')
  axs[1,1].set_ylabel('Similarity fraction')

  fig.tight_layout()
  fig_dest_prefix = "%s_group_timerange" % ('_'.join(year_q_list))
  fig_dest = os.path.join(output_dir, '%s.png' % fig_dest_prefix)
  print "Saving a time range of stuff", fig_dest
  fig.savefig(fig_dest)
  plt.close(fig)

  with open(os.path.join('%s.csv'), 'w') as f:
    cols = []
    cols.append(posix_range[:-1])
    cols.append(norm_start_hist.tolist())
    cols.append(norm_non_start_hist.tolist())
    rows = []
    for i in range(len(cols[0])):
      row_str = ','.join(map(lambda j: str(cols[j][i]), range(len(cols))))
      rows.append(row_str)
    f.write('\n'.join(row_str))
    print "Saving csv", f.name

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

def filter_process(output_dir, year_q):
  time_ind, commit_ind = 0, 1
  token_ind, p_self_ind, p_other_ind = 2, 3, 4
  meds = load_meds(output_dir)

  #write_online_stats(output_dir, year_q)
  online_sims = load_online_stats(output_dir, year_q)
  for uname in online_sims:
    online_np = online_sims[uname][2]

  # max token, max p other
  not_pass_list = []
  pass_list = []
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
    pass_result = set()
    for uname in unames:
      #print uname
      # if str(uname) == '2014010364':
      #   print cross_sims[uname]
      uname_others = cross_sims[uname].keys()
      uname_others.sort()
      for uname_other in uname_others:
        if add_str == '' and 'online' in uname_other:
          continue
        cross_np = cross_sims[uname][uname_other]
        _, max_commit_ind, max_token_ind, max_p_self_ind, max_p_other_ind = \
                  np.argmax(cross_np,axis=0).tolist()
        max_commit = cross_np[max_commit_ind,1]
        _, _, max_token, max_p_self, max_p_other = np.amax(cross_np,axis=0).tolist()
        _, _, avg_token, avg_p_self, avg_p_other = np.average(cross_np,axis=0).tolist()
        # print '\t', uname_other, cross_np.shape[0]
        # print '\t\t', max_token, max_p_other
        #if max_p_other < 20 and max_token < 250: continue
        if check_thresh(cross_np[max_p_other_ind,2],cross_np[max_p_other_ind,3], cross_np[max_p_other_ind,4]):
          pass_result.add(uname)
          pass_list.append((max_token, max_p_other))
        else:
          not_pass_list.append((max_token, max_p_other))
          continue

        if (uname, uname_other) not in uname_edges:
          uname_edges[(uname, uname_other)] = []
          for commit_hash, moss_line in zip(cross_names[uname][uname_other], cross_np.tolist()):
            uname_edges[(uname, uname_other)].append('%s,%s,%s,%s' % \
                (uname, uname_other, commit_hash, ','.join(map(str,moss_line))))
        num_sims.append(cross_np.shape[0])
        num_maxes.append((max_token, max_p_self, max_p_other))
        num_avgs.append((avg_token, avg_p_self, avg_p_other))
    print "usernames passed (%d)" % (len(pass_result)), pass_result
    if add_str == 'both':
      not_pass_np = np.array(not_pass_list)
      pass_np = np.array(pass_list)
      from scipy import stats as spstats
      print "T-test for not pass vs pass", \
          spstats.ttest_ind(not_pass_np, pass_np, equal_var=False)
      print "Wilcoxon test for not pass vs pass", \
          spstats.ranksums(not_pass_np, pass_np)
      print "chi stats, not pass: %s, pass: %s" % \
          (spstats.normaltest(not_pass_np),
              spstats.normaltest(pass_np))

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

def prob_cheat(output_dir, year_q_list, info_np, non_info_np, include_point=None, sim_thresh=None):
  if not sim_thresh:
    sim_thresh = 0.0
  pc_time_ind = start_posix_ind

  posix_range = get_day_range(max(year_q_list), plus_minus=[0,2], incr=day_length, include_point=include_point)

  info_np_filt = info_np[np.nonzero(info_np[:,frac_sims_ind] >= sim_thresh)]
  cheat_hist, _ = np.histogram(info_np_filt[:,pc_time_ind],
                                bins=posix_range)
  info_np_else = info_np[np.nonzero(info_np[:,frac_sims_ind] < sim_thresh)]
  infoelse_hist, _ = np.histogram(info_np_else[:,pc_time_ind],
                                bins=posix_range)
  noninfo_hist, _ = np.histogram(non_info_np[:,pc_time_ind],
                                bins=posix_range)
  tot_counts = (cheat_hist + infoelse_hist + noninfo_hist).astype(float)
  print "cheat hist\t", cheat_hist
  print "else hist\t", infoelse_hist
  print "non hist\t", noninfo_hist

  fig, axs = plt.subplots(2,1)
  br0 = axs[0].bar(posix_range[:-1], cheat_hist, color='r', width=day_length)
  bb0 = axs[0].bar(posix_range[:-1], infoelse_hist+noninfo_hist,
      bottom=cheat_hist, color='b', width=day_length)
  br1 = axs[1].bar(posix_range[:-1], cheat_hist/tot_counts, color='r', width=day_length)

  axs[0].set_xticks(posix_range)
  axs[0].set_xticklabels(map(posix_to_datetime, posix_range), fontsize=8, rotation=45)
  axs[0].set_ylabel('Number of students')
  axs[0].set_xlabel('%s time' % titles[pc_time_ind])
  axs[0].legend([br0[0], bb0[0]], ['cheating', 'baseline'], fontsize=8)
  axs[1].set_xticks(posix_range)
  axs[1].set_xticklabels(map(posix_to_datetime, posix_range), fontsize=8, rotation=45)
  axs[1].set_ylim(0.0, 1.0)
  axs[1].set_ylabel('Percentage of students')
  axs[1].set_xlabel('%s time' % titles[pc_time_ind])

  fig.tight_layout()
  fig_prefix = '%s_probcheat' % ('_'.join(year_q_list))
  if sim_thresh:
    fig_prefix += '_%.2f' % (sim_thresh)
  fig_dest = os.path.join(output_dir, '%s.png' % fig_prefix)
  print "Saving probcheat thing to", fig_dest
  fig.savefig(fig_dest)
  plt.close(fig)

def grade_over_time(output_dir, year_q_list, info_np, non_info_np, include_point=None):
  pc_time_ind = start_posix_ind

  if include_point:
    print "include point", posix_to_datetime(include_point)
  posix_range = get_day_range(max(year_q_list), plus_minus=[0,2], incr=day_length, include_point=include_point)
  posix_range = get_day_range(max(year_q_list), plus_minus=[0,2], incr=day_length)

  grades_hist = []
  y_indices = range(-6, 0)[1::2]
  fig, axs = plt.subplots(len(y_indices), 1, figsize=(10,10))
  for posix_st, posix_end in zip(posix_range[:-1], posix_range[1:]):
    info_np_filt = info_np[np.nonzero(np.logical_and(\
                        info_np[:,start_posix_ind] >= posix_st,
                        info_np[:,start_posix_ind] <= posix_end))]
    non_info_np_filt = non_info_np[np.nonzero(np.logical_and(\
                        non_info_np[:,start_posix_ind] >= posix_st,
                        non_info_np[:,start_posix_ind] <= posix_end))]
    grades_hist.append((info_np_filt, non_info_np_filt))
  print "grades", len(grades_hist)
  print "posix", len(posix_range)
  for y, y_index in enumerate(y_indices):
    info_grades_avg = map(lambda thing: np.average(thing[0][:,y_index]), grades_hist)
    info_grades_err = map(lambda thing: np.std(thing[0][:,y_index])/np.sqrt(thing[0].shape[0]), grades_hist)
    non_info_grades_avg = map(lambda thing: np.average(thing[1][:,y_index]), grades_hist)
    non_info_grades_err = map(lambda thing: np.std(thing[1][:,y_index])/np.sqrt(thing[1].shape[0]), grades_hist)
    b0 = axs[y].errorbar(posix_range[:-1], info_grades_avg, color='r', yerr=info_grades_err, ecolor='r', fmt='^-')
    b1 = axs[y].errorbar(np.array(posix_range[:-1]), non_info_grades_avg, color='b', yerr=non_info_grades_err, ecolor='b',fmt='o-')
    # b0 = axs[y].bar(posix_range[:-1], info_grades_avg, color='r', width=day_length/3, yerr=info_grades_err, ecolor='k')
    # b1 = axs[y].bar(np.array(posix_range[:-1])+day_length/3, non_info_grades_avg, color='b', width=day_length/3, yerr=non_info_grades_err, ecolor='k')
    axs[y].set_xticks(posix_range)
    axs[y].set_xticklabels(map(lambda x: get_t_minus(x, max(year_q_list)), posix_range), fontsize=8, rotation=45)
    #axs[y].set_xticklabels(map(posix_to_datetime, posix_range), fontsize=8, rotation=45)
    axs[y].set_xlabel('%s time' % titles[pc_time_ind])
    axs[y].set_ylabel('Average for %s' % titles[y_index])
    if y == 1:
      axs[y].set_ylabel('Midterm average')
      axs[y].set_xlabel('Start time')
    elif y == 2:
      axs[y].set_ylabel('Final average')
      axs[y].set_xlabel('Start time')
    axs[y].set_ylim(0.0, 1.0)
    axs[y].legend([b0[0], b1[0]], ['cheating', 'baseline'], fontsize=8)

  fig.tight_layout()
  fig_prefix = '%s_goodgrade_by_stttime' % ('_'.join(year_q_list))
  fig_dest = os.path.join(output_dir, '%s.png' % fig_prefix)
  print "Saving gradesthing to", fig_dest
  fig.savefig(fig_dest)
  plt.close(fig)

def grade_over_ta_time(output_dir, year_q_list, info_np, non_info_np, include_point=None):
  pc_time_ind = start_posix_ind

  posix_range = get_day_range(max(year_q_list), plus_minus=[0,2], incr=day_length, include_point=include_point)

  ta_hrs_hist = []
  ta_visits_hist = []
  ta_hr_max = max(np.amax(info_np[:,ta_hrs_ind]), np.amax(non_info_np[:,ta_hrs_ind])) + 1 # inclusive
  ta_visit_max = max(np.amax(info_np[:,ta_visits_ind]), np.amax(non_info_np[:,ta_visits_ind])) + 1 # inclusive
  nbins = 10
  ta_hr_range = np.linspace(0,ta_hr_max,num=nbins+1).astype(int)
  ta_visit_range = np.linspace(0,ta_visit_max,num=nbins+1).astype(int)
  ta_hr_width = ta_hr_range[1] - ta_hr_range[0]
  ta_visit_width = ta_visit_range[1] - ta_visit_range[0]
  num_students = float(info_np.shape[0])
  non_num_students = float(non_info_np.shape[0])
  for i in range(nbins):
    info_np_filt = info_np[np.nonzero(np.logical_and(
                        info_np[:,ta_hrs_ind] >= ta_hr_range[i],
                        info_np[:,ta_hrs_ind] < ta_hr_range[i+1]))]
    non_info_np_filt = non_info_np[np.nonzero(np.logical_and(
                        non_info_np[:,ta_hrs_ind] >= ta_hr_range[i],
                        non_info_np[:,ta_hrs_ind] < ta_hr_range[i+1]))]
    if not info_np_filt.tolist():
      info_np_filt = np.zeros((2,last_ind))
    if not non_info_np_filt.tolist():
      non_info_np_filt = np.zeros((2,last_ind))
    ta_hrs_hist.append((info_np_filt, non_info_np_filt))

    info_np_filt = info_np[np.nonzero(np.logical_and(
                        info_np[:,ta_visits_ind] >= ta_visit_range[i],
                        info_np[:,ta_visits_ind] < ta_visit_range[i+1]))]
    non_info_np_filt = non_info_np[np.nonzero(np.logical_and(
                        non_info_np[:,ta_visits_ind] >= ta_visit_range[i],
                        non_info_np[:,ta_visits_ind] < ta_visit_range[i+1]))]
    if not info_np_filt.tolist():
      info_np_filt = np.zeros((2,last_ind))
    if not non_info_np_filt.tolist():
      non_info_np_filt = np.zeros((2,last_ind))
    ta_visits_hist.append((info_np_filt, non_info_np_filt))

  y_indices = range(-6, 0)[1::2] + [0]
  fig, axs = plt.subplots(len(y_indices), 2, figsize=(10,10))
  for y, y_index in enumerate(y_indices):
    if y == 3:
      info_counts = map(lambda thing: thing[0].shape[0]/num_students, ta_hrs_hist)
      non_info_counts = map(lambda thing: thing[1].shape[0]/non_num_students, ta_hrs_hist)
      b0 = axs[y,0].bar(ta_hr_range[:-1], info_counts, color='r', width=ta_hr_width/3)
      b1 = axs[y,0].bar(ta_hr_range[:-1]+ta_hr_width/3, non_info_counts, color='b', width=ta_hr_width/3)
      axs[y,0].set_xticks(ta_hr_range)
      axs[y,0].set_ylabel('Number of students')
      axs[y,0].set_xlabel('%s' % titles[ta_visits_ind])
      axs[y,0].legend([b0[0], b1[0]], ['cheating', 'baseline'], fontsize=8)

      info_counts = map(lambda thing: thing[0].shape[0]/num_students, ta_visits_hist)
      non_info_counts = map(lambda thing: thing[1].shape[0]/non_num_students, ta_visits_hist)
      b0 = axs[y,1].bar(ta_visit_range[:-1], info_counts, color='r', width=ta_visit_width/3)
      b1 = axs[y,1].bar(ta_visit_range[:-1]+ta_visit_width/3, non_info_counts, color='b', width=ta_visit_width/3)
      axs[y,1].set_xticks(ta_visit_range)
      axs[y,1].set_ylabel('Number of students')
      axs[y,1].set_xlabel('%s' % titles[ta_visits_ind])
      axs[y,1].legend([b0[0], b1[0]], ['cheating', 'baseline'], fontsize=8)
    else:
      info_grades_avg = map(lambda thing: np.average(thing[0][:,y_index]), ta_hrs_hist)
      info_grades_err = map(lambda thing: np.std(thing[0][:,y_index])/np.sqrt(thing[0].shape[0]), ta_hrs_hist)
      non_info_grades_avg = map(lambda thing: np.average(thing[1][:,y_index]), ta_hrs_hist)
      non_info_grades_err = map(lambda thing: np.std(thing[1][:,y_index])/np.sqrt(thing[1].shape[0]), ta_hrs_hist)
      b0 = axs[y,0].bar(ta_hr_range[:-1], info_grades_avg, color='r', width=ta_hr_width/3, yerr=info_grades_err, ecolor='k')
      b1 = axs[y,0].bar(ta_hr_range[:-1]+ta_hr_width/3, non_info_grades_avg, color='b', width=ta_hr_width/3, yerr=non_info_grades_err, ecolor='k')
      axs[y,0].set_xticks(ta_hr_range)
      axs[y,0].set_ylabel('Average for %s' % titles[y_index])
      axs[y,0].set_xlabel('%s' % titles[ta_hrs_ind])
      axs[y,0].set_ylim(0.0, 1.0)
      axs[y,0].legend([b0[0], b1[0]], ['cheating', 'baseline'], fontsize=8)

      info_grades_avg = map(lambda thing: np.average(thing[0][:,y_index]), ta_visits_hist)
      info_grades_err = map(lambda thing: np.std(thing[0][:,y_index])/np.sqrt(thing[0].shape[0]), ta_visits_hist)
      non_info_grades_avg = map(lambda thing: np.average(thing[1][:,y_index]), ta_visits_hist)
      non_info_grades_err = map(lambda thing: np.std(thing[1][:,y_index])/np.sqrt(thing[1].shape[0]), ta_visits_hist)
      b0 = axs[y,1].bar(ta_visit_range[:-1], info_grades_avg, color='r', width=ta_visit_width/3, yerr=info_grades_err, ecolor='k')
      b1 = axs[y,1].bar(ta_visit_range[:-1]+ta_visit_width/3, non_info_grades_avg, color='b', width=ta_visit_width/3, yerr=non_info_grades_err, ecolor='k')
      axs[y,1].set_xticks(ta_visit_range)
      axs[y,1].set_ylabel('Average for %s' % titles[y_index])
      axs[y,1].set_xlabel('%s' % titles[ta_visits_ind])
      axs[y,1].set_ylim(0.0, 1.0)
      axs[y,1].legend([b0[0], b1[0]], ['cheating', 'baseline'], fontsize=8)



  fig.tight_layout()
  fig_prefix = '%s_goodgrade_by_ta' % ('_'.join(year_q_list))
  fig_dest = os.path.join(output_dir, '%s.png' % fig_prefix)
  print "Saving gradesthing to", fig_dest
  fig.savefig(fig_dest)
  plt.close(fig)

def process_baseline(output_dir, year_q):
  baseline_sims = load_baseline_sims(output_dir, year_q)
  short_dict = {}
  for uname in sorted(baseline_sims.keys()):
    for match in baseline_sims[uname]:
      uname_other, num_tokens, p_self, p_other = match
      if check_thresh(num_tokens, p_self, p_other):
        if uname not in short_dict:
          short_dict[uname] = []
        short_dict[uname].append(uname_other)
  comps_with_edges, tot_groups = get_reachable_nodes(short_dict)
  print "baseline %s" % year_q, comps_with_edges, tot_groups


def load_baseline_sims(output_dir, year_q):
  baseline_name = 'baseline_%s' % year_q
  baseline_sims = {}
  baseline_path = os.path.join(output_dir, '%s.csv' % baseline_name)
  with open(baseline_path, 'r') as f:
    line = f.readline()
    while line:
      line = line.strip()
      line_commas = line.split(',')
      uname = line_commas[0]
      other_f_path, other_f_html, tokens_matched, \
          percent_self, percent_other = line_commas[1:]
      if uname not in baseline_sims:
        baseline_sims[uname] = []
      baseline_sims[uname].append(\
          (get_uname_from_f(other_f_path), int(tokens_matched),
            float(percent_self), float(percent_other)))
      baseline_sims[uname][-1]
      line = f.readline()
  return baseline_sims

def load_info_noninfo(output_dir, year_q_list,work_limit=0):
  edges, comps = {}, {}
  top_sims = {}
  posix_lookup = {}
  gr = {}
  # if not work_limit:
  #   work_limit = all_startend_times[max(year_q_list)][END_TIME]
  # affected by work_limit:
  #   num_commits
  #   ta_num_visits, ta_num_hrs,
  #   ta_num_v_during, ta_num_h_during,
  #   num_days, num_hrs
  # ** min_posix, max_posix NOT affected!!!!

  for year_q in year_q_list:
    #process_baseline(output_dir, year_q)
    top_sims.update(load_top_sims_from_log(output_dir, year_q, add_str='both'))
    posix_lookup.update(load_posix_to_commit_ind(output_dir, year_q))

    all_grades = load_all_grades(output_dir, year_q)
    gr.update(get_graderank_dict(all_grades))

    comps_yq, edges_yq = load_components_info(output_dir, year_q)
    comps.update(comps_yq)
    edges.update(edges_yq)

  _, _, _, during_ta_uname_stats_np = get_ta_stats(output_dir, year_q=year_q, ta_bounds=ASSGT_ONLY_TA_TIME, work_limit=work_limit)
  _, _, _, b4_ta_uname_stats_np = get_ta_stats(output_dir, year_q=year_q, ta_bounds=B4_ASSGT_TIME)
  _, _, _, all_ta_uname_stats_np = get_ta_stats(output_dir, year_q=year_q, ta_bounds=ALL_TA_TIME)
  cross_sims, cross_names = load_top_sims_by_uname(top_sims)
  grps = get_grps(comps, edges)
  info = []
  non_info = []
  unames_grp = [uname for grp in grps for uname in sorted(grp)] # flatten

  for uname in sorted(top_sims.keys()):
    info_uname = []
    uname_year, uname_q = uname[:4], uname[4:6]
    old_year_q = '%s_%s' % (int(uname_year), int(uname_q))
    num_commits = len(top_sims[uname].keys()) # by default, the entire
    times_during = map(lambda k: scale_days(int(k), old_year_q,
                                            new_year_q=max(year_q_list)),
                      top_sims[uname].keys())
    if work_limit: # commits until this time
      times_during = filter(lambda k: int(k) < work_limit, times_during)
      num_commits = len(times_during)


    # moss
    grp_ind_tmp, id_ind_tmp, od_ind_tmp = 0, 1, 2
    num_sims, frac_sims = 0, 0.0
    b4_frac_sims, after_frac_sims = 0.0, 0.0
    max_token, max_p_self, max_p_other = 0.0, 0.0, 0.0
    avg_token, avg_p_self, avg_p_other = 0.0, 0.0, 0.0
    start_sim_posix, end_sim_posix = 0.0, 0.0
    grp_i = -1
    if uname in unames_grp:
      tot_cross_np = []
      if comps[uname][od_ind_tmp] == 0:
        #print "sink", uname, comps[uname]
        pass
      else:
        for uname_other in edges[uname]:
          #num_sims += len(edges[uname][uname_other].keys())
          cross_np = cross_sims[uname][uname_other]
          if work_limit:
            # do some filtering here, if needed
            cross_np_keep = np.nonzero(cross_np[:,0] < work_limit)[0]
            if len(cross_np_keep) > 0:
              tot_cross_np.append(cross_np[cross_np_keep,:])
          else:
            # regular, all of cross_np
            tot_cross_np.append(cross_np)

      if len(tot_cross_np) and num_commits:
        # todo: include stats on type of commit? like max token, avg token, these things
        tot_cross_np = np.concatenate(tot_cross_np)
        orig_num_sims = tot_cross_np.shape[0]
        #num_sims = tot_cross_np.shape[0]
        # if str(uname) == '2014010364':
        #   print tot_cross_np
        thresh_inds = map(lambda i: i if \
            check_thresh(tot_cross_np[i,2], tot_cross_np[i,3], tot_cross_np[i,4]) else -1, range(orig_num_sims))
        above_thresh_inds = filter(lambda i: i != -1, thresh_inds)

        # above_thresh_inds_2 = np.nonzero(np.logical_or(
        #                 tot_cross_np[:,2] >= thresh_token,
        #                 tot_cross_np[:,4] >= thresh_p_other))[0]
        # print uname, "diff", len(above_thresh_inds), len(above_thresh_inds_2)

        tot_cross_np = tot_cross_np[above_thresh_inds,:]
        num_sims = tot_cross_np.shape[0]
        if num_sims:
          #print "%s\t%.2f\t%.2f\t%d" % (uname, orig_num_sims/float(num_commits), num_sims/float(num_commits), num_sims)
          frac_sims = float(num_sims)/num_commits
          _, _, max_token, max_p_self, max_p_other = np.amax(tot_cross_np, axis=0).tolist()
          _, _, avg_token, avg_p_self, avg_p_other = np.average(tot_cross_np, axis=0).tolist()
          earliest_start_time = all_startend_times[old_year_q][START_TIME] 
          start_sim_posix = int(min(filter(lambda posix_time: int(posix_time) >= earliest_start_time,tot_cross_np[:,0].tolist())))
          end_sim_posix = np.amax(tot_cross_np[:,0])
          b4_frac_sims = float(posix_lookup[uname][start_sim_posix])/num_commits
          after_frac_sims = 1-float(posix_lookup[uname][end_sim_posix])/num_commits

          grp_i = comps[uname][grp_ind_tmp]

          # scale days.
          start_sim_posix = scale_days(start_sim_posix, old_year_q,
                              new_year_q=max(year_q_list))
          end_sim_posix = scale_days(end_sim_posix, old_year_q,
                              new_year_q=max(year_q_list))
      # this cond: no tot_cross_np

    info_uname += [int(uname), grp_i, num_sims]
    info_uname += [frac_sims, b4_frac_sims, after_frac_sims]
    info_uname += [max_token, max_p_self, max_p_other]
    info_uname += [avg_token, avg_p_self, avg_p_other]
    info_uname += [start_sim_posix, end_sim_posix]

    # first do this before any processing to weed out people we don't care about
    if uname not in gr:
      #print "no grade", uname
      continue

    # hours/commits on task
    # some students take the class earlier and drop it, so account for this
    earliest_start_time = all_startend_times[old_year_q][START_TIME] 
    min_posix = int(min(filter(lambda posix_time: int(posix_time) >= earliest_start_time,
                                top_sims[uname].keys())))

    max_posix = int(max(top_sims[uname].keys()))
    num_hrs, work_times = get_hours(top_sims[uname].keys())
    num_hrs_filt, work_times_filt = get_hours(top_sims[uname].keys(),work_limit=work_limit)
    work_times = np.array(work_times)
    avg_work_time = 0.0
    max_work_times = 0.0
    if len(work_times) != 0:
      work_durs = work_times[:,1] - work_times[:,0]
      avg_work_time = np.average(work_durs)/float(day_length/24)
      max_work_time = np.amax(work_durs)/float(day_length/24)

    # scale days.
    min_posix = scale_days(min_posix, old_year_q, new_year_q=max(year_q_list))
    max_posix = scale_days(max_posix, old_year_q, new_year_q=max(year_q_list))
    info_uname +=  \
        [min_posix, #posix_to_datetime(float(min_posix)),
         max_posix, #posix_to_datetime(float(max_posix)),
         #min_posix, max_posix,
         num_commits,
         num_hrs, avg_work_time, max_work_time]

    # ta info
    ta_num_visits, ta_num_hrs = 0.0, 0.0
    ta_num_v_during, ta_num_h_during = 0.0, 0.0
    ta_num_v_b4, ta_num_h_b4 = 0.0, 0.0
    ta_v_ind_tmp, ta_posix_ind_tmp = 0, 1
    ta_uname_ind_tmp = 5 # index of student uname in the ta array
    all_ta_index = np.nonzero(int(uname) == all_ta_uname_stats_np[:,ta_uname_ind_tmp])[0]
    if len(all_ta_index) > 0:
      uname_lair_stat = all_ta_uname_stats_np[all_ta_index[0],:]
      ta_num_visits = uname_lair_stat[ta_v_ind_tmp]
      ta_num_hrs = uname_lair_stat[ta_posix_ind_tmp]/float(day_length/24)
    during_ta_index = np.nonzero(int(uname) == during_ta_uname_stats_np[:,ta_uname_ind_tmp])[0]
    if len(during_ta_index) > 0:
      uname_lair_stat = during_ta_uname_stats_np[during_ta_index[0],:]
      ta_num_v_during = uname_lair_stat[ta_v_ind_tmp]
      ta_num_h_during = uname_lair_stat[ta_posix_ind_tmp]/float(day_length/24)
    b4_ta_index = np.nonzero(int(uname) == b4_ta_uname_stats_np[:,ta_uname_ind_tmp])[0]
    if len(b4_ta_index) > 0:
      uname_lair_stat = b4_ta_uname_stats_np[b4_ta_index[0],:]
      ta_num_v_b4 = uname_lair_stat[ta_v_ind_tmp]
      ta_num_h_b4 = uname_lair_stat[ta_posix_ind_tmp]/float(day_length/24)
    info_uname += [ta_num_visits, ta_num_hrs]
    #print ta_num_visits, ta_num_hrs
    info_uname += [ta_num_v_during, ta_num_h_during]
    info_uname += [ta_num_v_b4, ta_num_h_b4]

    # grades
    global grade_list
    for grade_name in grade_list:
      info_uname += [gr[uname][G_IND][grade_name], gr[uname][R_IND][grade_name]]

    if uname in unames_grp and comps[uname][od_ind_tmp] != 0:
      info.append(info_uname)
    else:
      non_info.append(info_uname)
  return info, non_info
  

