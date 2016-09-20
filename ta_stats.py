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
  plot_ta_service_times(output_dir, year_q)

def plot_ta_stats_multi(output_dir):
  plot_ta_service_times(output_dir)

def plot_ta_service_times(output_dir, year_q=None):
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
  start_time_bound = all_startend_times[year_q][START_TIME]
  end_time_bound = all_startend_times[year_q][END_TIME]
  # for uname in lair_dict:
  #   if uname not in posix_lookup:
  #     # could be possible if uname is in holdout set
  #     continue
  for uname in posix_lookup:
    uname_year, uname_q = uname[:4], uname[4:6]
    uname_year_q = '%s_%s' % (int(uname_year), int(uname_q))
    all_posix = np.array(posix_lookup[uname].keys())
    all_posix = scale_days(all_posix, uname_year_q, year_q)
    start_posix, end_posix, num_commits = np.amin(all_posix), np.amax(all_posix), len(all_posix)

    if uname not in gr: continue
    gr_uname_abs = list(gr[uname][G_IND])
    gr_uname_rank = list(gr[uname][R_IND])

    ta_length = 0
    ta_posix_length = 0
    if uname in lair_dict:
      for start_ta_time, end_ta_time, ta_uname in lair_dict[uname]:
        start_ta_time = scale_days(start_ta_time, uname_year_q, year_q)
        end_ta_time = scale_days(end_ta_time, uname_year_q, year_q)
        if start_ta_time >= start_time_bound and start_ta_time <= end_time_bound:
        #if True:
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

  start_ta_ind, end_ta_ind = 0, 1
  start_ind, end_ind, length_ind = 2, 3, 4
  uname_ind, ta_uname_ind = 5, 6
  grade_ind_st = 7

  ta_len_ind, ta_hrs_ind = 0, 1
  grade_uname_ind_st = 6

  # plot stuff
  numplots = 10 # even number
  num_half = numplots/2
  if not all_grades:
    numplots = 1
    num_half = 1

  graph_options = list(itertools.product([ASSGT_3, ASSGT_6, MT_IND, F_IND],range(2), (True, False)))#,
                      #(GRADE_TYPE, COMMIT_TYPE, START_TYPE, END_TYPE)))
  for grade_name, grade_type, normalize_flag in graph_options:
    print "norm flag: %s, assgt: %s, grade type: %s" % \
        (GRADE_NAMES[grade_name], GRADE_TYPES[grade_type], normalize_flag)#, sort_type)
        #, sort type: %s" % \
    if not all_grades:
      print "Skipping grade-based figure."
      continue
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
    max_len = np.amax(uname_stats_np[:,ta_len_ind])
    max_hrs = np.amax(uname_stats_np[:,ta_hrs_ind])
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

      len_hist, len_bin_edges = np.histogram(ta_len_sub, bins=len_bins)
      hrs_hist, hrs_bin_edges = np.histogram(ta_hrs_sub, bins=hrs_bins)

      #c = m.to_rgba(plt_ind/float(numplots))
      c = m.to_rgba(np.average(uname_stats_np[sort_inds_sub,grade_uname_ind]))
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
    grade_bins[-1] = max(np.amax(no_ta_grades), 1.0)
    print "no ta bins", grade_bins
    no_ta_hist, no_ta_edges = np.histogram(no_ta_grades, bins=grade_bins)
    ax_hist[0,-1].bar(grade_bins[:-1],
                      no_ta_hist,
                      width=0.1,
                      color=color_plots)
    ax_hist[0,-1].set_xlim(1.0,0.0)
    ax_hist[0,-1].set_title('No TA hours')

    print "no ta hours hist", no_ta_hist
                     

    title_str = "%s TA aggregate stats "
    grade_tup_str = (GRADE_NAMES[grade_name], GRADE_TYPES[grade_type])
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


