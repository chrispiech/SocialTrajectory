from helper import *
from git_helper import *
from git_tool import *
from time import strptime
from datetime import date
from scipy.interpolate import interp1d
from scipy.interpolate import UnivariateSpline
from scipy.misc import derivative
from scipy.signal import argrelextrema
from general_stats import *

output_stats_dir = "stats"
output_diffs_dir = "diffs"
  
"""
Called after all_diffs.
"""
def process_diffs(output_dir, year_q):
  plot_diffs(output_dir, year_q)
  #plot_diffs_over_time(output_dir, '2012_1')
  #line_changes(code_dir, output_dir)

"""
"""
def loline_changes(code_dir, output_dir):
  uname_lookup = load_uname_lookup_by_year_q()
  count = 10

  for student in os.listdir(code_dir):
    student_dir = os.path.join(code_dir, student)
    year_q = get_submit_time(student_dir)
    if not year_q: continue
    lines = git_log(git_dir=student_dir,
                format_str="%h %ct",
                extra_str="--date=local --shortstat").split('\n')
    lines_iter = iter(lines)
    if student not in uname_lookup[year_q]: continue
    student_id = uname_lookup[year_q][student]
    student_log_name = "%s" % student_id
    for line in lines_iter:
      print line
      # split_spaces = line.split(' ')
      # if len(split_spaces) == 2:
      #   commit, posix_time = split_spaces
      #   line = next(lines_iter)
      pass
    count -=1
    if count == 0: break
  pass

"""
Does the actual diffing.
Gets the progress of each commit and saves it in the output dir.
"""
def all_diffs(code_dir, output_dir):
  uname_lookup = load_uname_lookup_by_year_q()

  for student in os.listdir(code_dir):
    student_dir = os.path.join(code_dir, student)
    year_q = get_submit_time(student_dir)
    if not year_q: continue
    lines = git_log(git_dir=student_dir,
                format_str="%h %ct",
                extra_str="--date=local --shortstat").split('\n')
    lines_iter = iter(lines)
    if student not in uname_lookup[year_q]: continue
    student_id = uname_lookup[year_q][student]
    student_log_name = "%s" % student_id
    all_stats = []
    for line in lines_iter:
      split_spaces = line.split(' ')
      if len(split_spaces) == 2:
        commit, posix_time = split_spaces
        line = next(lines_iter)
        split_spaces = line.split(' ')
        if len(split_spaces) > 2:
          file_count = int(split_spaces[1])
          insert_avail = 'insertion' in line
          delete_avail = 'deletion' in line
          insertion, deletion = 0, 0
          if insert_avail:
            if not delete_avail:
              insertion = int(split_spaces[-2])
            else:
              insertion = int(split_spaces[-4])
          if delete_avail:
            deletion = int(split_spaces[-2])
          commit_str = '%s_%s_%s' %  (student_id, commit, posix_time)

          all_stats.append((commit_str, file_count, insertion, deletion))

    if not os.path.exists(os.path.join(output_dir, year_q, output_diffs_dir)):
      os.makedirs(os.path.join(output_dir, year_q, output_diffs_dir))
    student_log_file = os.path.join(output_dir, year_q, output_diffs_dir,
              student_log_name)
    print student_log_file
    with open(student_log_file, 'w') as f:
      f.write('\n'.join(['%s\t%s\t%s\t%s' % stat_line for stat_line in all_stats]))
    print

def load_diffs(output_dir, year_q):
  diffs_dir = os.path.join(output_dir, year_q, output_diffs_dir)
  all_diffs = {}
  for uname in os.listdir(diffs_dir):
    uname_diff_file = os.path.join(diffs_dir, uname)
    all_diffs[uname] = {}
    with open(uname_diff_file, 'r') as f:
      line = f.readline()
      while line:
        line = line.strip()
        commit, num_files, insertions, deletions = line.split('\t')
        posix_time = commit.split('_')[-1]
        all_diffs[uname][posix_time] = (int(num_files), int(insertions), int(deletions), commit)
        line = f.readline()
  return all_diffs

def plot_diffs_over_time(output_dir, year_q):
  all_diffs = load_diffs(output_dir, year_q)
  all_diffs_list = []
  all_timeseries = {}
  max_commits = 0
  for uname in all_diffs:
    posix_times = all_diffs[uname].keys()
    posix_times.sort()
    temp_list = [(int(posix_times[i]),
                  i, 
                  all_diffs[uname][posix_times[i]][0],
                  all_diffs[uname][posix_times[i]][1],
                  all_diffs[uname][posix_times[i]][2]) \
                for i in range(len(posix_times))]
    all_diffs_list += temp_list
    all_timeseries[uname] = np.array(temp_list)
    max_commits = max(max_commits, len(temp_list))

  all_diffs_np = np.array(all_diffs_list)
  all_times_np = all_diffs_np[:,0]
  all_commits_np = all_diffs_np[:,1]
  all_filecounts_np = all_diffs_np[:,2]
  fc_min, fc_max = np.percentile(all_filecounts_np, [0,100])
  all_insertions_np = all_diffs_np[:,3]
  all_deletions_np = all_diffs_np[:,4]

  max_commits = np.amax(all_commits_np)
  insertions_bins = np.percentile(all_insertions_np, [10,50,70,80,90,95,99,100])
  deletions_bins = np.percentile(all_deletions_np, [10,50,70,80,90,95,99,100])
  print "insertion", insertions_bins
  print "deletion", deletions_bins

  # med calc for black line stuff
  temp_np = med_calc(all_commits_np, all_filecounts_np,med_thresh=99)
  med_times_fc, meds_fc = temp_np[:,0], temp_np[:,1]
  temp_np = med_calc(all_commits_np, all_insertions_np,med_thresh=99)
  med_times_i, meds_i = temp_np[:,0], temp_np[:,1]
  temp_np = med_calc(all_commits_np, all_deletions_np,med_thresh=99)
  med_times_d, meds_d = temp_np[:,0], temp_np[:,1]
  
  num_plots = 3 # 0: file counts, 1: insertions, 2: deletions
  fig_x, fig_y = 40, 10
  fig, ax_all = plt.subplots(num_plots, 1, figsize=(fig_x, num_plots*fig_y))
  fc_ind, i_ind, d_ind = 0, 1, 2
  thresh_unames = [[],[],[]]
  for uname in all_timeseries:
    time_array, commit_strs = all_timeseries[uname]
    posix_times = time_array[:,0]
    commits = time_array[:,1]
    filecounts = time_array[:,2]
    insertions = time_array[:,3]
    deletions = time_array[:,4]

    # file counts
    ax_std = ax_all[fc_ind]
    ax_std.scatter(commits, filecounts, c='b', edgecolors='none')
    max_ind, max_sim, thresh_perc = \
      get_label_if_thresh(commits, filecounts,
        dict([(med_times_fc[i], meds_fc[i]) for i in range(len(med_times_fc))]))
    if max_sim != -1:
      ax_std.annotate(uname[6:], xy=(max_ind, max_sim), size=10, textcoords='data')
      thresh_unames[fc_ind].append((uname[6:], thresh_perc))

    # insertions
    ax_std = ax_all[i_ind]
    ax_std.scatter(commits, insertions, c='b', edgecolors='none')
    max_ind, max_sim, thresh_perc = \
      get_label_if_thresh(commits, insertions,
        dict([(med_times_i[i], meds_i[i]) for i in range(len(med_times_i))]))
    if max_sim != -1:
      ax_std.annotate(uname[6:], xy=(max_ind, max_sim), size=10, textcoords='data')
      thresh_unames[i_ind].append((uname[6:], thresh_perc))
    
    # deletions
    ax_std = ax_all[d_ind]
    ax_std.scatter(commits, deletions, c='b', edgecolors='none')
    max_ind, max_sim, thresh_perc = \
      get_label_if_thresh(commits, deletions,
        dict([(med_times_d[i], meds_d[i]) for i in range(len(med_times_d))]))
    if max_sim != -1:
      ax_std.annotate(uname[6:], xy=(max_ind, max_sim), size=10, textcoords='data')
      thresh_unames[d_ind].append((uname[6:], thresh_perc))
    
  ax_fc = ax_all[fc_ind]
  ax_fc.plot(med_times_fc, meds_fc, c='k')
  ax_fc.set_xlabel('Commits')
  ax_fc.set_ylabel('Files modified')
  ax_fc.set_title('Files modified vs Commits')

  ax_i = ax_all[i_ind]
  ax_i.plot(med_times_i, meds_i, c='k')
  #ax_i.set_yticks(insertions_bins)
  ax_i.set_yscale('log')
  ax_i.set_xlim((0,max_commits))
  ax_i.set_xlabel('Commits')
  ax_i.set_ylabel('Lines inserted')
  ax_i.set_title('Lines inserted vs Commits')

  ax_d = ax_all[d_ind]
  ax_d.plot(med_times_d, meds_d, c='k')
  #ax_d.set_yticks(deletions_bins)
  ax_d.set_yscale('log')
  ax_d.set_xlim((0,max_commits))
  ax_d.set_xlabel('Commits')
  ax_d.set_ylabel('Lines deleted')
  ax_d.set_title('Lines deleted vs Commits')

  fig_dest = os.path.join(output_dir, '%s_fc_insertions_deletions.png' % year_q)
  print "Saving insertions and deletions figure", fig_dest
  fig.savefig(fig_dest)
  plt.close(fig)

"""
Histogram of data with bin size bin_size.

Finds and returns a spline function spline_f of the data.
  The knot factor is 5 for insertions (hardcoded)
                  and 6 for deletions.

Returns critical points of the spline function, where a 
  zero first-derivative is those that fall below the deriv_thresh threshold.
"""
def hist_and_split(data, insert=True, bin_size=10, deriv_thresh=0.1):
  hist, bin_edges = np.histogram(data,
        bins=range(0,np.amax(data),bin_size))
  nz_hist_ind = np.nonzero(hist)
  nz_hist_log = np.log10(hist[nz_hist_ind][1:]) # ignore "0-bin_size" bin
  nz_bins_log = np.log10(bin_edges[nz_hist_ind][1:]) # ignore "0-bin_size" bin

  knot_factor = 33
  if insert: knot_factor = 20

  spline_f = UnivariateSpline(nz_bins_log, nz_hist_log,
                              s=len(nz_hist_log)/knot_factor)

  newx = np.linspace(min(nz_bins_log), max(nz_bins_log), num=10000)
  derivs = spline_f(newx, nu=1) # find the first derivative of newx points
  critpoint_inds = np.nonzero(np.abs(derivs) < deriv_thresh)
  cp_counts, cp_bins = np.histogram(newx[critpoint_inds])
  nz_cp_bins = cp_bins[cp_counts.nonzero()]
  nz_cp_counts = cp_counts[cp_counts.nonzero()]
  if insert: print "insert"
  else: print "delete"
  print nz_cp_bins
  
  critpoint_x = 0
  if len(nz_cp_bins) > 0:
    critpoint_x = nz_cp_bins[1]
  critpoint_y = spline_f(critpoint_x, nu=1)
  print "critpoint", critpoint_x, critpoint_y, spline_f(critpoint_x)
  
  return nz_hist_log, nz_bins_log, spline_f, critpoint_x
  

"""
Plots the file counts, insertions, and deletions as a histogram.
From this, fits a curve to the insertions/deletions.
Record the insert/deletes that are over a given threshold (the
  "critical point" in each fitted curve) and ...
Writes the commits that are above this insert/delete critical point.
"""
def plot_diffs(output_dir, year_q):
  all_diffs = load_diffs(output_dir, year_q)
  all_diffs_list = []
  all_timeseries = {}
  max_commits = 0
  for uname in all_diffs:
    posix_times = all_diffs[uname].keys()
    posix_times.sort()
    temp_list = [(int(posix_times[i]),
                  i, 
                  all_diffs[uname][posix_times[i]][0],
                  all_diffs[uname][posix_times[i]][1],
                  all_diffs[uname][posix_times[i]][2]) \
                for i in range(len(posix_times))]
    commit_list = [all_diffs[uname][posix_times[i]][3] \
                for i in range(len(posix_times))]
    all_diffs_list += temp_list
    all_timeseries[uname] = [np.array(temp_list), commit_list]
    max_commits = max(max_commits, len(temp_list))

  all_diffs_np = np.array(all_diffs_list)
  all_times_np = all_diffs_np[:,0]
  all_commits_np = all_diffs_np[:,1]
  all_filecounts_np = all_diffs_np[:,2]
  fc_min, fc_max = np.percentile(all_filecounts_np, [0,100])
  all_insertions_np = all_diffs_np[:,3]
  all_deletions_np = all_diffs_np[:,4]
  insert_min_max = np.percentile(all_insertions_np, [0,99])
  delete_min_max = np.percentile(all_deletions_np, [0,99])
  id_min = min(insert_min_max[0], delete_min_max[0])
  id_max = max(insert_min_max[1], delete_min_max[1])
  print "fc bounds", fc_min, fc_max
  print "insert delete bounds", id_min, id_max
  print "max delete bound", np.percentile(all_deletions_np, [99, 100])
  print "max insert bound", np.percentile(all_insertions_np, [99, 100])

  insertions_bins = np.percentile(all_insertions_np, [10,50,70,80,90,95,99,100])
  deletions_bins = np.percentile(all_deletions_np, [10,50,70,80,90,95,99,100])

  num_plots = 3 # 0: file counts, 1: insertions (g), 2: deletions (r)
  fig_x, fig_y = 8, 6
  fig, ax_all = plt.subplots(num_plots, 1, figsize=(fig_x, num_plots*fig_y))
  fc_ind, i_ind, d_ind = 0, 1, 2

  # per commit
  ax_std = ax_all[fc_ind]
  #fc_n, fc_bins, fc_patches = ax_std.hist(all_filecounts_np, np.amax(all_filecounts_np), normed=0)
  hist, bin_edges = np.histogram(all_filecounts_np, bins=range(0,1000,100))
  ax_std.set_title('Files modified')
  ax_std.set_xlabel('File counts changed')

  # insertions and deletions
  print insertions_bins
  print deletions_bins
  ax_std = ax_all[i_ind]
  #in_n, in_bins, in_patches = ax_std.hist(all_insertions_np, insertions_bins)
  hist, bin_edges = np.histogram(all_insertions_np, bins=range(0,1000,10))
  print "insert", all_insertions_np
  for i in range(len(hist)):
    print '%d\t%d' % (bin_edges[i], hist[i])
  nz_hist_log_i, nz_bins_log_i, spline_f_i, critpoint_log_i = \
    hist_and_split(all_insertions_np, insert=True)
  newx = np.linspace(min(nz_bins_log_i), max(nz_bins_log_i), num=1000)
  ax_std.plot(nz_bins_log_i, nz_hist_log_i, 'o',
              newx, spline_f_i(newx), '--')
  ax_std.plot([critpoint_log_i], spline_f_i([critpoint_log_i]), 'o', c='r')
  ax_std.set_title('Lines inserted')
  ax_std.set_ylabel('# commits (log)')
  ax_std.set_xlabel('insertions over time (log)')

  ax_std = ax_all[d_ind]
  #de_n, de_bins, de_patches = ax_std.hist(all_deletions_np, deletions_bins)
  #ax_std.set_xticks(deletions_bins)
  hist, bin_edges = np.histogram(all_deletions_np, bins=range(0,1000,10))
  for i in range(len(hist)):
    print '%d\t%d' % (bin_edges[i], hist[i])
  nz_hist_log_d, nz_bins_log_d, spline_f_d, critpoint_log_d = \
    hist_and_split(all_deletions_np, insert=False)
  newx = np.linspace(min(nz_bins_log_d), max(nz_bins_log_d), num=1000)
  ax_std.plot(nz_bins_log_d, nz_hist_log_d, 'o',
              newx, spline_f_d(newx), '--')
  ax_std.plot([critpoint_log_d], spline_f_d([critpoint_log_d]), 'o', c='r')
  ax_std.set_title('Lines deleted')
  ax_std.set_ylabel('# commits (log)')
  ax_std.set_xlabel('deletions over time (log)')

  # file counts
  fig.suptitle('Histograms of file counts and insertions/deletions')
  # ax_std.set_ylim(fc_min, fc_max)
  file_count_dest = os.path.join(output_dir, '%s_fc_insertions_deletions_hist.png' % year_q)
  print "Saving file count figure", file_count_dest
  fig.savefig(file_count_dest)
  plt.close(fig)

  many_inserts = set()
  many_deletes = set()
  critpoint_i, critpoint_d = np.exp(critpoint_log_i), np.exp(critpoint_log_d)
  for uname in all_timeseries:
    time_array, commit_strs = all_timeseries[uname]
    posix_times = time_array[:,0]
    commits = time_array[:,1]
    filecounts = time_array[:,2]
    insertions = time_array[:,3]
    deletions = time_array[:,4]

    i_past_crit = np.nonzero(insertions > critpoint_i)
    for i in i_past_crit[0].tolist():
      many_inserts.add(commit_strs[i])
    numi_past_crit = np.sum(np.nonzero(insertions > critpoint_i))

    d_past_crit = np.nonzero(deletions > critpoint_d)
    numd_past_crit = np.sum(np.nonzero(deletions > critpoint_d))
    for d in d_past_crit[0].tolist():
      many_deletes.add(commit_strs[i])

  inserts = list(many_inserts)
  deletes = list(many_deletes)
  with open(os.path.join(output_dir, year_q, 'commits_inserts'), 'w') as f:
    inserts.sort()
    f.write('\n'.join(inserts))
  with open(os.path.join(output_dir, year_q, 'commits_deletes'), 'w') as f:
    deletes.sort()
    f.write('\n'.join(deletes))
