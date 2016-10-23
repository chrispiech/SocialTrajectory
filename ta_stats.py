from helper import *
from git_helper import *
from time import strptime
from datetime import date
from scipy.interpolate import interp1d
from scipy.interpolate import UnivariateSpline
from scipy.misc import derivative
from scipy.signal import argrelextrema

COMMIT_TYPE = 0
GRADE_TYPE = 1
START_TYPE = 2
END_TYPE = 3

NO_GRADE = 0
MT_GRADE = 1
MT_RANK = 2
F_GRADE = 3
F_RANK = 4
ASSGT_GRADE = 5
ASSGT_RANK = 6

def plot_ta_stats(output_dir, year_q):
  #plot_ta_service_times(output_dir, year_q)
  plot_ta_deviation_stats(output_dir, year_q)

def plot_ta_stats_multi(output_dir):
  #plot_ta_service_times(output_dir)
  plot_ta_deviation_stats(output_dir)

ALL_TA_TIME = 0
ASSGT_ONLY_TA_TIME = 1
B4_ASSGT_DEAD_TA_TIME = 2
B4_MT_TIME = 3
BT_MT_FINAL_TIME = 4
LATE_ASSGT_TA_TIME = 5
B4_ASSGT_TIME = 6
ta_bounds_str = ['allta', 'onlyassgt3', 'untilassgt3deadline', 'beforemt', 'btexams', 'lateta', 'b4assgt']

def get_ta_stats(output_dir, year_q=None, ta_bounds=ALL_TA_TIME, work_limit=0):
  year_q_list = []
  lair_dict = {}
  posix_lookup = {}
  gr = {}
  if not year_q:
    for year_q_dirname in os.listdir(output_dir):
      try:
        year, q = year_q_dirname.split('_')
        int(year), int(q)
      except: continue

      year_q = year_q_dirname
      all_grades = load_all_grades(output_dir, year_q)
      if not all_grades: continue
      lair_dict.update(load_student_lair(output_dir, year_q))
      print "num students gotten help in %s:" % year_q, len(load_student_lair(output_dir, year_q).keys())
      posix_lookup.update(load_posix_to_commit_ind(output_dir, year_q))

      gr.update(get_graderank_dict(all_grades))
      year_q_list.append(year_q)
    year_q_list.sort()
    print "year_q_list:", year_q_list
    year_q = '2014_1'
  else:
    lair_dict = load_student_lair(output_dir, year_q)
    posix_lookup = load_posix_to_commit_ind(output_dir, year_q)

    all_grades = load_all_grades(output_dir, year_q)
    gr = get_graderank_dict(all_grades)
    print "year_q:", year_q
  if not gr:
    print "\tno grades"
    return

  all_stats = []
  uname_stats = []
  # default bounds are assignment only ASSGT_ONLY_TA_TIME
  start_time_bound = all_startend_times[year_q][START_TIME]
  end_time_bound = all_startend_times[year_q][END_TIME] + 2*day_length
  if ta_bounds == B4_ASSGT_DEAD_TA_TIME:
    start_time_bound = 0
    end_time_bound = all_startend_times[year_q][END_TIME] + 2*day_length
  elif ta_bounds == B4_MT_TIME:
    start_time_bound = 0 # no bound...
    end_time_bound = all_exam_times[year_q][MT_TIME]
  elif ta_bounds == BT_MT_FINAL_TIME:
    start_time_bound = all_exam_times[year_q][MT_TIME]
    end_time_bound = all_exam_times[year_q][FINAL_TIME]
  elif ta_bounds == LATE_ASSGT_TA_TIME:
    start_time_bound = all_startend_times[year_q][END_TIME] - 3.5*day_length
    end_time_bound = all_startend_times[year_q][END_TIME] + 2*day_length
  elif ta_bounds == B4_ASSGT_TIME:
    start_time_bound = 0
    end_time_bound = all_startend_times[year_q][START_TIME]
  elif ta_bounds == ALL_TA_TIME:
    start_time = 0
    end_time_bound = all_exam_times[year_q][FINAL_TIME]
  # for uname in lair_dict:
  #   if uname not in posix_lookup:
  #     # could be possible if uname is in holdout set
  #     continue
  for uname in lair_dict:
    uname_year, uname_q = uname[:4], uname[4:6]
    uname_year_q = '%s_%s' % (int(uname_year), int(uname_q))
    start_posix, end_posix, num_commits = 0, 0, 0
    if uname in posix_lookup:
      all_posix = np.array(posix_lookup[uname].keys())
      all_posix = scale_days(all_posix, uname_year_q, year_q)
      start_posix, end_posix, num_commits = np.amin(all_posix), np.amax(all_posix), len(all_posix)

    if uname not in gr:
      continue
    gr_uname_abs = list(gr[uname][G_IND])
    gr_uname_rank = list(gr[uname][R_IND])

    ta_length = 0
    ta_posix_length = 0
    if uname in lair_dict:
      for start_ta_time, end_ta_time, ta_uname in lair_dict[uname]:
        start_ta_time = scale_days(start_ta_time, uname_year_q, year_q)
        end_ta_time = scale_days(end_ta_time, uname_year_q, year_q)
        if ta_bounds != 0:
          if end_ta_time <= start_time_bound:
            continue
          if start_ta_time >= end_time_bound:
            continue
          # ta help was outside of assignment time limit
        if work_limit:
          # work limit supplied in addition to ta bounds
          if start_ta_time >= work_limit:
            continue
          if end_ta_time >= work_limit:
            end_ta_time = work_limit-1 # idk why off by one here, but i'm doing it
        all_stats.append([start_ta_time, end_ta_time,
                            start_posix, end_posix, num_commits,
                            int(uname), int(ta_uname)] + \
                            gr_uname_abs + \
                            gr_uname_rank)
        ta_length += 1
        ta_posix_length += end_ta_time - start_ta_time
    #if ta_length == 0: continue
    uname_stats.append([ta_length, ta_posix_length,
                        start_posix, end_posix, num_commits,
                        int(uname)] + \
                        gr_uname_abs + \
                        gr_uname_rank)
  all_stats_np = np.array(all_stats)
  uname_stats_np = np.array(uname_stats)

  return lair_dict, year_q_list, all_stats_np, uname_stats_np, 

def plot_ta_service_times(output_dir, year_q=None):
  try:
    lair_dict, year_q_list, all_stats_np, uname_stats_np = get_ta_stats(output_dir, year_q=year_q)
  except:
    print "no grades, probably"
    return
  if len(year_q_list) > 0:
    year_q = '2014_1'

  start_ta_ind, end_ta_ind = 0, 1
  start_ind, end_ind, length_ind = 2, 3, 4
  uname_ind, ta_uname_ind = 5, 6
  grade_ind_st = 7

  ta_len_ind, ta_hrs_ind = 0, 1
  grade_uname_ind_st = 6

  # plot stuff
  numplots = 10 # even number
  num_half = numplots/2
  # if not all_grades:
  #   numplots = 1
  #   num_half = 1

  graph_options = list(itertools.product([ASSGT_3, ASSGT_6, MT_IND, F_IND],range(2), (True, False)))#,
                      #(GRADE_TYPE, COMMIT_TYPE, START_TYPE, END_TYPE)))
  for grade_name, grade_type, normalize_flag in graph_options:
    print "norm flag: %s, assgt: %s, grade type: %s" % \
        (GRADE_NAMES[grade_name], GRADE_TYPES[grade_type], normalize_flag)#, sort_type)
        #, sort type: %s" % \
    # if not all_grades:
    #   print "Skipping grade-based figure."
    #   continue
    grade_tup_str = (GRADE_NAMES[grade_name], GRADE_TYPES[grade_type])

    grade_offset = NUM_GRADES*grade_type + grade_name
    grade_ind = grade_ind_st + grade_offset
    grade_uname_ind = grade_uname_ind_st + grade_offset

    # sort
    col_to_sort = -all_stats_np[:,grade_ind] # need reverse rank/grade
    col_to_sort_uname_stats = -uname_stats_np[:,grade_uname_ind]
    sort_inds = np.argsort(col_to_sort)
    sort_inds_uname_stats = np.argsort(col_to_sort_uname_stats)
    sort_col = col_to_sort[sort_inds]
    set_size = len(sort_inds)/numplots
    set_size_uname_stats = len(sort_inds_uname_stats)/numplots
    print "size of each sort set", set_size_uname_stats, "total students", len(sort_inds_uname_stats)

    m = set_colormap([0.0, 1.0])

    ########### histogram plots
    fig_hist, ax_hist = plt.subplots(2, numplots+1, figsize=(20,10))
    fig_ch, ax_ch = plt.subplots(2,1,figsize=(10,8))
    max_len = np.amax(uname_stats_np[:,ta_len_ind])
    max_hrs = np.amax(uname_stats_np[:,ta_hrs_ind])
    print "max len", max_len, "max hrs", max_hrs
    num_bins = 5
    # len_bins = np.zeros(num_bins+1)
    # hrs_bins = np.zeros(num_bins+1)
    len_bins = np.linspace(0.01, max_len, num_bins+1)
    hrs_bins = np.linspace(0.01, max_hrs, num_bins+1)
    # len_labels = ['None']
    # hrs_labels = ['None']
    len_labels = []
    hrs_labels = []
    for i in range(0,num_bins):
      if i == 0:
        len_labels.append('>0 - %.2f' % (len_bins[i+1]))
        hrs_labels.append('>0 - %.2f' % (hrs_bins[i+1]/3600.0))
      else:
        len_labels.append('%.2f - %.2f' % (len_bins[i], len_bins[i+1]))
        hrs_labels.append('%.2f - %.2f' % (hrs_bins[i]/3600.0, hrs_bins[i+1]/3600.0))

    widths = np.linspace(0, 10, num_bins+1)
    print "len bins", len_bins
    print "hrs bins", hrs_bins
    len_ymax = 0
    hrs_ymax = 0
    color_plots = np.zeros((numplots,4))
    for plt_ind in xrange(numplots):
      if plt_ind == numplots - 1:
        sort_inds_sub = sort_inds_uname_stats[plt_ind*set_size_uname_stats:]
      else:
        sort_inds_sub = sort_inds_uname_stats[plt_ind*set_size_uname_stats:(plt_ind+1)*set_size_uname_stats]
      ta_len_sub = uname_stats_np[sort_inds_sub, ta_len_ind]
      ta_hrs_sub = uname_stats_np[sort_inds_sub, ta_hrs_ind]
      grades_sub = uname_stats_np[sort_inds_sub, grade_uname_ind]

      len_hist, len_bin_edges = np.histogram(ta_len_sub, bins=len_bins)
      hrs_hist, hrs_bin_edges = np.histogram(ta_hrs_sub, bins=hrs_bins)

      #c = m.to_rgba(plt_ind/float(numplots))
      c = m.to_rgba(np.average(grades_sub))
      print "%d grade average" % plt_ind ,np.average(uname_stats_np[sort_inds_sub,grade_uname_ind])
      color_plots[numplots-1-plt_ind,:] = c

      len_plt_tup = (0, plt_ind)
      hrs_plt_tup = (1, plt_ind)
      if numplots == 1:
        len_plt_tup = 0
        hrs_plt_tup = 1

      ax_hist[len_plt_tup].bar(widths[:-1],
                     len_hist,
                     width=widths[1] - widths[0],
                     color=c)

      ax_hist[hrs_plt_tup].bar(widths[:-1],
                     hrs_hist,
                     width=widths[1] - widths[0],
                     color=c)
      ax_hist[len_plt_tup].set_title('# sessions')
      ax_hist[hrs_plt_tup].set_title('# hours')
      ax_hist[len_plt_tup].set_xlim(np.amin(widths), np.amax(widths))
      ax_hist[len_plt_tup].set_xticks(widths+0.5*(widths[1]-widths[0]))
      ax_hist[len_plt_tup].set_xticklabels(len_labels, rotation=90, fontsize=10)
      ax_hist[hrs_plt_tup].set_xlim(np.amin(widths), np.amax(widths))
      ax_hist[hrs_plt_tup].set_xticks(widths+0.5*(widths[1]-widths[0]))
      ax_hist[hrs_plt_tup].set_xticklabels(hrs_labels, rotation=90, fontsize=10)

      ax_ch[0].scatter(grades_sub, ta_len_sub, lw=0, alpha=0.5) #, color=m.to_rgba(grades_sub))
      ax_ch[1].scatter(grades_sub, ta_hrs_sub, lw=0, alpha=0.5) #, color=m.to_rgba(grades_sub))

      len_ymax = max(len_ymax, np.amax(len_hist))
      hrs_ymax = max(hrs_ymax, np.amax(hrs_hist))

    for plt_ind in xrange(numplots):
      len_plt_tup = (0, plt_ind)
      hrs_plt_tup = (1, plt_ind)
      if numplots == 1:
        len_plt_tup = 0
        hrs_plt_tup = 1
      ax_hist[len_plt_tup].set_ylim(0, len_ymax)
      ax_hist[hrs_plt_tup].set_ylim(0, hrs_ymax)

    # the last plot is distribution of people who have no hours at all
    ta_len = uname_stats_np[:,ta_len_ind]
    ta_hrs = uname_stats_np[:,ta_hrs_ind]
    no_ta_inds = np.nonzero(uname_stats_np[:,ta_len_ind] == 0)
    no_ta_grades = uname_stats_np[no_ta_inds,grade_uname_ind]
    grade_bins = np.arange(0.0, 1.1, 0.1)
    if len(no_ta_grades[0]) != 0:
      grade_bins[-1] = max(np.amax(no_ta_grades), 1.0)
      print "no ta bins", grade_bins
      no_ta_hist, no_ta_edges = np.histogram(no_ta_grades, bins=grade_bins)
      ax_hist[0,-1].bar(grade_bins[:-1],
                        no_ta_hist,
                        width=0.1,
                        color=color_plots)
    ax_hist[0,-1].set_xlim(1.0,0.0)
    ax_hist[0,-1].set_title('No TA hours')

    ax_ch[0].set_ylim(0.0, max_len)
    ax_ch[1].set_ylim(0.0, max_hrs)
    ax_ch[0].set_ylabel('Number of sessions')
    ax_ch[1].set_ylabel('Hours')
    ax_ch[1].set_yticklabels(['%.2f' % (x/3600.0) for x in np.linspace(0.0, max_hrs, 10)])

    ax_ch[0].set_xlim(0.0, 1.1)
    ax_ch[1].set_xlim(0.0, 1.1)
    ax_ch[0].set_xlabel('%s, %s' % grade_tup_str)
    ax_ch[1].set_xlabel('%s, %s' % grade_tup_str)

    ax_ch[0].set_title('Number of sessions vs (%s, %s)' % grade_tup_str)
    ax_ch[1].set_title('Number of hours vs (%s, %s)' % grade_tup_str)

                     

    title_str = "%s TA aggregate stats "
    title_str += "(%s, %s)" % grade_tup_str
    fig_hist.suptitle(title_str)

    fig_prefix = '%s_lair_histogram' % year_q
    if len(year_q_list) > 0:
      fig_prefix = '%s_lair_histogram' % ('_'.join(year_q_list))
    fig_prefix += "_%s_%s" % grade_tup_str
    fig_dest = os.path.join(output_dir, '%s.png' % fig_prefix)
    print "Saving", fig_dest
    fig_hist.tight_layout()
    fig_hist.savefig(fig_dest)
    plt.close(fig_hist)

    fig_prefix_ch = "%s_lair_scatter" % year_q
    if len(year_q_list) > 0:
      fig_prefix_ch = '%s_lair_scatter' % ('_'.join(year_q_list))
    fig_prefix_ch += "_%s_%s" % grade_tup_str
    fig_dest_ch = os.path.join(output_dir, '%s.png' % fig_prefix_ch)
    print "Saving", fig_dest_ch
    fig_ch.tight_layout()
    fig_ch.savefig(fig_dest_ch)
    plt.close(fig_ch)


    ########### grade-based plots

    fig_aggr = plt.figure(figsize=(6,6))
    ax_aggr = plt.gca()
    incr = incr_length
    posix_range_aggr = get_day_range(year_q, plus_minus=[-0.5, 0.5], incr=incr)
    xlabels_aggr = [posix_to_datetime(posix_t) for posix_t in posix_range_aggr]
    ylabels_aggr = np.arange(0.0, 1.0, 0.1)

    # point sizing
    max_ms = 100 
    max_ta_time = np.amax(all_stats_np[:,end_ta_ind] - all_stats_np[:,start_ta_ind])
    min_ta_time = np.amin(all_stats_np[:,end_ta_ind] - all_stats_np[:,start_ta_ind])
    print "max", max_ta_time, "min", min_ta_time
    for plt_ind in xrange(numplots):
      y_spacing_aggr = numplots - plt_ind - 1

      if plt_ind == numplots - 1:
        sort_inds_sub = sort_inds[plt_ind*set_size:]
      else:
        sort_inds_sub = sort_inds[plt_ind*set_size:(plt_ind+1)*set_size]

      start_ta_times_sub = all_stats_np[sort_inds_sub, start_ta_ind]
      end_ta_times_sub = all_stats_np[sort_inds_sub, end_ta_ind]
      grades_sub = all_stats_np[sort_inds_sub, grade_ind]

      lengths_sub = end_ta_times_sub - start_ta_times_sub
      norm_gran = 3 # decimal granularity
      if normalize_flag:
        pass
        # times = np.around(uname_points_np[:,commit_ind]/uname_stat[length_ind],
        #                   decimals=norm_gran)
      print "distr of lengths for %s" % y_spacing_aggr, np.percentile(lengths_sub, range(0,100,10))
      
      #c = m.to_rgba(y_spacing_aggr/float(numplots))
      c = m.to_rgba(np.average(grades_sub))
      colors = np.tile(c, start_ta_times_sub.shape)
      msizes = max_ms * np.maximum(lengths_sub, 2*min_ta_time)/float(max_ta_time)
      ax_aggr.scatter(start_ta_times_sub,
                      y_spacing_aggr*np.ones(start_ta_times_sub.shape),
                      c=colors,
                      s=msizes,
                      lw=0,
                      alpha=0.5)

    title_str = "%s TA help times by grade."
    grade_tup_str = (GRADE_NAMES[grade_name], GRADE_TYPES[grade_type])
    title_str += "(%s, %s)" % grade_tup_str
    ax_aggr.set_title("%s (aggr)" % title_str)

    if not normalize_flag:
      ax_aggr.set_label('Date')
      ax_aggr.set_xlim(posix_range_aggr[0], posix_range_aggr[-1])
      ax_aggr.set_xticks(posix_range_aggr[0::2])
      ax_aggr.set_xticklabels(xlabels_aggr[0::2], rotation=45, fontsize=8)
    else:
      ax_aggr.set_label('Normalized progress over commits')
      ax_aggr.set_xlim(0.0, 1.0)

    ax_aggr.set_ylim(-1, numplots+1)
    ax_aggr.set_yticks(range(numplots))
    ax_aggr.set_yticklabels(ylabels_aggr)
    ax_aggr.xaxis.grid(True)

    fig_aggr_prefix = "%s_lair" % year_q
    if len(year_q_list) > 0:
      fig_aggr_prefix = '%s_lair' % ('_'.join(year_q_list))
    fig_aggr_prefix += "_%s_%s" % grade_tup_str
    fig_aggr_dest = os.path.join(output_dir, '%s.png' % fig_aggr_prefix)
    print "Saving", fig_aggr_dest
    fig_aggr.savefig(fig_aggr_dest)
    plt.close(fig_aggr)

def plot_ta_deviation_stats(output_dir, year_q=None):
  try:
    lair_dict, year_q_list, all_stats_np, uname_stats_np = get_ta_stats(output_dir, year_q=year_q)
  except:
    print "no grades, probably"
    return
  if len(year_q_list) > 0:
    year_q = '2014_1'

  start_ta_ind, end_ta_ind = 0, 1
  start_ind, end_ind, length_ind = 2, 3, 4
  uname_ind, ta_uname_ind = 5, 6
  grade_ind_st = 7

  ta_len_ind, ta_hrs_ind = 0, 1
  start_uname_ind, end_uname_ind = 2, 3
  num_commits_ind = 4
  uname_uname_ind = 5
  grade_uname_ind_st = 6
  hrs_per_ta = grade_uname_ind_st + NUM_GRADES*2
  mt_z_ind = hrs_per_ta + 1
  f_z_ind = hrs_per_ta + 2

  mt_ind = grade_uname_ind_st + NUM_GRADES*R_IND+MT_IND
  f_ind = grade_uname_ind_st + NUM_GRADES*R_IND+F_IND

  ##### calculate expected outs/run (z score per TA hours)
  # all_stats.append([start_ta_time, end_ta_time,
  #                   start_posix, end_posix, num_commits,
  #                   int(uname), int(ta_uname)] + \
  #                   gr_uname_abs + \
  #                   gr_uname_rank)
  z_scores_per_hr = []

  ta_dict = get_ta_teaching_times(lair_dict)

  x_data_points = []
  y_data_points = []
  data_points = {}
  for ta_uname in ta_dict:
    time_worked = 0.0
    data_point = []
    for uname in ta_dict[ta_uname]:
      ta_info = ta_dict[ta_uname][uname]
      student_hrs_per_ta = np.sum(ta_info[:,end_ta_ind]) - \
                          np.sum(ta_info[:,start_ta_ind])
      time_worked += student_hrs_per_ta

      uname_stat = uname_stats_np[np.nonzero(int(uname) == uname_stats_np[:,uname_uname_ind]),:].flatten()
      if len(uname_stat) == 0: # if final grade DNE
        continue
      mt_g, f_g = uname_stat[mt_ind], uname_stat[f_ind]
      mt_z_score = get_z_scores(uname_stats_np, mt_ind, mt_g)
      f_z_score = get_z_scores(uname_stats_np, f_ind, f_g)
      extra_info = [student_hrs_per_ta, mt_z_score, f_z_score]
      data_point.append(uname_stat.tolist() + extra_info)
      z_scores_per_hr.append((mt_z_score/student_hrs_per_ta,
                               f_z_score/student_hrs_per_ta))
    if len(data_point) != 0:
      data_points[(ta_uname, time_worked)] = data_point

  z_scores_per_hr = np.array(z_scores_per_hr)
  mean_z_score_per_hr = (np.average(z_scores_per_hr[:,0]), np.average(z_scores_per_hr[:,1]))
  delta_mean_z_score_per_hr = mean_z_score_per_hr[1] - mean_z_score_per_hr[0]
  print "average mean z score per TA hr:", delta_mean_z_score_per_hr

  ##### Student variation figure :)
  fig_dev, ax_dev = plt.subplots(7, 1, figsize=(10,20))
  ta_offset = 0
  sorted_ver = sorted(data_points.keys(), key=lambda tup: tup[1])
  num_boxplots = 6
  boundaries = np.linspace(0,len(sorted_ver)-1, num_boxplots).astype(int)
  #timework_range = np.percentile(np.array([x[1] for x in sorted_ver]),percentiles.tolist())
  timework_range = [sorted_ver[i][1] for i in boundaries]
  commit_boxes = [[] for i in range(num_boxplots)]
  time_boxes = [[] for i in range(num_boxplots)]
  z_boxes = [[] for i in range(num_boxplots)]
  value_added = [[] for i in range(num_boxplots)]

  grade_names = [ASSGT_3, MT_IND, F_IND]
  grade_boxes = [[[] for j in range(num_boxplots)] for i, _ in enumerate(grade_names)]
  bin_x_vals = [[] for i in range(num_boxplots)]
  x_vals = []
  nz_x_vals = []

  
  for ta_offset, (ta_uname, time_worked) in enumerate(sorted_ver):
    #ta_offset = time_worked/3600
    x_val = time_worked
    stat_np = np.array(data_points[(ta_uname, time_worked)])
    bin_cat = get_bins(time_worked, timework_range)
    student_nz = np.nonzero(stat_np[:,num_commits_ind])
    if len(student_nz[0]) != 0:
      nz_commits = stat_np[student_nz,num_commits_ind][0]
      nz_starts = stat_np[student_nz,start_uname_ind][0]
      nz_ends = stat_np[student_nz,end_uname_ind][0]

      commit_boxes[bin_cat] += nz_commits.tolist()
      time_boxes[bin_cat] += (nz_ends - nz_starts).tolist()
      nz_x_vals.append(x_val)

    x_vals.append(x_val)
    bin_x_vals[bin_cat].append(x_val)
    z_boxes[bin_cat] += (stat_np[:,f_z_ind] - stat_np[:,mt_z_ind]).tolist()
    value_added_ta = (np.average(stat_np[:,f_z_ind] - stat_np[:,mt_ind])) - 0.5*(delta_mean_z_score_per_hr)*time_worked
    value_added[bin_cat].append(value_added_ta)

    grade_type = R_IND
    for ind, grade_name in enumerate(grade_names):
      grade_offset = NUM_GRADES*grade_type + grade_name
      grade_ind = grade_uname_ind_st + grade_offset
      grades = stat_np[:,grade_ind]
      min_grades, max_grades = np.amin(grades), np.amax(grades)
      grade_boxes[ind][bin_cat] += grades.tolist()
      #ax_dev[plt_ind].errorbar(x_val, np.average(grades), yerr=(max_grades - min_grades))
  print "bins", timework_range
  num_steps = 10
  nz_label_locs = range(0, len(nz_x_vals), len(nz_x_vals)/num_steps)
  nz_labels = ['%.2f' % (nz_x_vals[loc]/3600) for loc in nz_label_locs]
  nz_x_vals = np.array(range(len(nz_x_vals)))

  label_locs = range(0, len(x_vals), len(x_vals)/num_steps)
  labels = ['%.2f' % (x_vals[loc]/3600) for loc in label_locs]
  labels = []
  for i in range(num_boxplots-1):
    labels.append('%.2f - <%.2f\n(%d)' % (timework_range[i]/3600, timework_range[i+1]/3600,len(bin_x_vals[i])))
  labels.append('>=%.2f\n(%d)' % (timework_range[-1]/3600,len(bin_x_vals[-1])))

  x_vals = np.array(range(len(x_vals)))
  med_x_vals = filter(lambda i: len(bin_x_vals[i]) != 0, range(num_boxplots))
  med_timework_range = np.array([timework_range[i] for i, _ in enumerate(med_x_vals)])

  bp = ax_dev[0].boxplot(commit_boxes, positions=range(num_boxplots))
  meds = np.array([medline.get_ydata()[0] for medline in bp['medians']])
  #ax_dev[0].set_xlim(min(x_vals)-100, max(x_vals)+100)
  ax_dev[0].set_title('Commits per student vs. TA')
  ax_dev[0].set_ylabel('Commits per student')
  ax_dev[0].set_xticklabels(labels,rotation=30)

  m, b = np.polyfit(med_timework_range, meds, 1)
  print "commits: y = %s x + %s" % (m, b)
  ax_dev[0].plot(med_x_vals, m*med_timework_range+b, 'o--', c='g')

  bp = ax_dev[1].boxplot(time_boxes, positions=range(num_boxplots))
  meds = np.array([medline.get_ydata()[0] for medline in bp['medians']])
  min_time = min([min(timebox) for timebox in filter(lambda x: len(x) != 0, time_boxes)])
  max_time = max([max(timebox) for timebox in filter(lambda x: len(x) != 0, time_boxes)])*0.1
  hrs_range = np.linspace(min_time, max_time, 10)
  ax_dev[1].set_xticklabels(labels, rotation=30)
  ax_dev[1].set_ylim(min_time, max_time)
  ax_dev[1].set_yticks(hrs_range)
  ax_dev[1].set_yticklabels(['%.2f' % (hrs/3600) for hrs in hrs_range])
  ax_dev[1].set_ylabel('Hours student worked')
  ax_dev[1].set_title('Time per student vs. TA total work length')
  m, b = np.polyfit(med_timework_range, meds, 1)
  print "hours worked: y = %s x + %s" % (m, b)
  ax_dev[1].plot(med_x_vals, m*med_timework_range+b, 'o--', c='g')

  bp = ax_dev[2].boxplot(z_boxes, positions=range(num_boxplots))#nz_x_vals)
  meds = np.array([medline.get_ydata()[0] for medline in bp['medians']])
  #ax_dev[2].set_xlim(min(x_vals)-100, max(x_vals)+100)
  #delta_avgs = [np.average(z_box) for z_box in z_boxes]
  #ax_dev[2].plot(x_vals, delta_avgs)
  # ax_dev[2].set_xticks(label_locs)
  ax_dev[2].set_xticklabels(labels,rotation=30)
  ax_dev[2].set_ylabel('Z score (F - MT)')
  ax_dev[2].set_xlabel('Hours TA has worked with any student')
  ax_dev[2].set_title('Z score difference vs. TA total work length')
  #m, b = np.polyfit(x_vals, delta_avgs, 1)
  #ax_dev[2].plot(x_vals, m*x_vals+b, c='r')
  #print "z: y = %s x + %s" % (m, b)
  m, b = np.polyfit(med_timework_range, meds, 1)
  print "z score difference: y = %s x + %s" % (m, b)
  ax_dev[2].plot(med_x_vals, m*med_timework_range+b, 'o--', c='g')

  #ax_dev[3].scatter(x_vals, value_added)
  bp = ax_dev[3].boxplot(value_added, positions=range(num_boxplots))
  meds = np.array([medline.get_ydata()[0] for medline in bp['medians']])
  #m, b = np.polyfit(x_vals, value_added, 1)
  #ax_dev[3].plot(x_vals, m*x_vals+b, c='r')
  #ax_dev[3].set_xlim(0, max(x_vals))
  #ax_dev[3].set_xticks(label_locs)
  ax_dev[3].set_xticklabels(labels,rotation=30)
  ax_dev[3].set_ylabel('mean Z score (F - MT)')
  ax_dev[3].set_ylim(-3, 3)
  ax_dev[3].set_title('mean Z score difference vs TA total work length')
  m, b = np.polyfit(med_timework_range, meds, 1)
  print "z score difference: y = %s x + %s" % (m, b)
  ax_dev[3].plot(med_x_vals, m*med_timework_range+b, 'o--', c='g')

  plt_ind = 4
  for ind, grade_name in enumerate(grade_names):
    grade_sub = grade_boxes[ind]
    bp = ax_dev[plt_ind].boxplot(grade_sub,positions=range(num_boxplots))#x_vals)
    meds = np.array([medline.get_ydata()[0] for medline in bp['medians']])
    grade_tup_str = (GRADE_NAMES[grade_name], GRADE_TYPES[grade_type])
    #delta_avgs = [np.average(g_sub) for g_sub in grade_sub]
    #ax_dev[2].plot(x_vals, delta_avgs)
    ax_dev[plt_ind].set_title('%s, %s' % grade_tup_str)
    #ax_dev[plt_ind].set_xticks(label_locs)
    ax_dev[plt_ind].set_xticklabels(labels,rotation=30)
    #ax_dev[plt_ind].set_xlim(min(x_vals)-100, max(x_vals)+100)
    m, b = np.polyfit(med_timework_range, meds, 1)
    print "(%s,%s): y = %s x + %s" % (grade_tup_str[0], grade_tup_str[1], m, b)
    ax_dev[plt_ind].plot(med_x_vals, m*med_timework_range+b, 'o--', c='g')
    plt_ind += 1
  ax_dev[-1].set_xlabel('Hours TA has worked with any student')

  fig_dev.tight_layout()
  fig_dev_prefix = "%s_lair_dev" % year_q
  if len(year_q_list) > 0:
    fig_dev_prefix = '%s_lair_dev' % ('_'.join(year_q_list))
  fig_dev_dest = os.path.join(output_dir, '%s.png' % fig_dev_prefix)
  print "Saving", fig_dev_dest
  fig_dev.savefig(fig_dev_dest)
  plt.close(fig_dev)
