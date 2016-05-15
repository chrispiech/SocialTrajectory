from helper import *
from git_helper import *
from time import strptime
from datetime import date

output_stats_dir = "stats"
output_diffs_dir = "diffs"

# Turns a month, year date into a quarter id. Decides on the quarter based
# on the month.
def get_quarter(month, year):
  month_int = strptime(month,'%b').tm_mon
  if(month_int <= strptime('Mar','%b').tm_mon):
    return year + '_2'
  if(month_int <= strptime('Jun','%b').tm_mon):
    return year + '_3'
  if(month_int <= strptime('Aug','%b').tm_mon):
    return year + '_4'
  return year + '_1'

def get_quarter_unix(unix_string):
  date_str = unix_to_human_time(unix_time)
  tokens = date_str.split(' ')
  month, year = tokens[1], tokens[4]
  return get_quarter(month, year)

# This runs a git command line that gets the timestamp of the last commit.
# It then uses a helper method to turn that into a quarter id. Can easily
# be extended to get a more precise time.
def get_submit_time(student_dir):
  print student_dir
  # use --date local for user timezone, vs committer timezone
  date_str = git_log(git_dir=student_dir,
             lines=1,
             format_str='%cd',
             extra_str ='--date=local')
  if not date_str:
    print "get_submit_time: %s ignored, corrupt git" % student_dir.split('/')[-1]
    return ''
  tokens = date_str.split(' ')
  if len(tokens) < 5: return -1
  month, year = tokens[1], tokens[4]
  quarter = get_quarter(month, year)
  return str(quarter)

# For each student dir in the code_dir, check the timestamp of their last
# commit.
def check_timestamps(code_dir):
  uname_quarters = {}
  orig_all_unames = 0
  all_year_q = set()
  for f in os.listdir(code_dir):
    uname = f.split('/')[-1].split('_')[0]
    orig_all_unames += 1
    if uname not in uname_quarters:
      uname_quarters[uname] = []
    student_dir = os.path.join(code_dir, f)
    year_q = get_submit_time(student_dir)
    all_year_q.add(year_q)
    date_str = git_log(git_dir=student_dir,
             lines=1,
             format_str='%h %ct',
             extra_str ='--date=local')
    if not date_str:
    #   print "expand: %s ignored, corrupt git" % (student_dir)
      continue
    uname_quarters[uname].append((f, date_str))
  all_unames = 0
  valid_unames = 0
  for uname in uname_quarters:
    all_unames += 1
    if uname_quarters[uname]:
      valid_unames += 1
  print "valid names", valid_unames, "all names", all_unames, "all in listdir", orig_all_unames
  print "all quarters", all_year_q
  return uname_quarters

"""
Returns the directory of each user with a valid git repo.
Students sometimes submit several times, so take the last submit
of each student.
"""
def get_unique_unames(code_dir):
  uname_quarters = check_timestamps(code_dir)
  unique_unames = []
  for uname in uname_quarters:
    if not uname_quarters[uname]: continue
    uname_submits = [int(x[0].split('_')[-1]) for x in uname_quarters[uname]]
    unique_unames.append('%s_%d' % (uname, max(uname_submits)))
  print '\n'.join(unique_unames)
  print "sanity check num unames", len(unique_unames)
  return unique_unames

"""
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

"""
For each student dir in the code_dir, save a log of
the timestamps and commit number in the output_dir.
"""
def all_timestamps(code_dir, output_dir):
  for student in os.listdir(code_dir):
    student_dir = os.path.join(code_dir, student)
    year_q = get_submit_time(student_dir)
    if not year_q: continue
    log_dir = os.path.join(output_dir, year_q, output_stats_dir)
    if not os.path.exists(log_dir):
      os.makedirs(log_dir)

    # commit_hash\tPOSIX(unix)_time\tReadable Date
    all_commits = git_log(git_dir=student_dir,
      format_str="%h\t%ct\t%cd", extra_str="--date=local")

    student_log_name = "%s.txt" % student
    student_log_file = os.path.join(output_dir, year_q, output_stats_dir,
              student_log_name)
    with open(student_log_file, 'w') as f:
      f.write(all_commits)
    print "Wrote student log file", student_log_file

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
        all_diffs[uname][posix_time] = (int(num_files), int(insertions), int(deletions))
        line = f.readline()
  return all_diffs

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
  insert_min_max = np.percentile(all_insertions_np, [0,99])
  delete_min_max = np.percentile(all_deletions_np, [0,99])
  id_min = min(insert_min_max[0], delete_min_max[0])
  id_max = max(insert_min_max[1], delete_min_max[1])
  print "fc bounds", fc_min, fc_max
  print "insert delete bounds", id_min, id_max
  print "max delete bound", np.percentile(all_deletions_np, [99, 100])
  print "max insert bound", np.percentile(all_insertions_np, [99, 100])

  plts = 2 # 0: file counts, 1: insertions (g), 1: deletions (r)
  fig_all, ax_all = [0]*plts, [0]*plts
  for plt_ind in range(plts):
    if plt_ind == 1:
      fig_all[plt_ind] = plt.figure(figsize=(40,10))
    else:
      fig_all[plt_ind] = plt.figure(figsize=(10,10))
    ax_all[plt_ind] = plt.gca()

  # per commit
  plt.figure(0)
  ax_std = ax_all[0]
  fc_n, fc_bins, fc_patches = ax_std.hist(all_filecounts_np, np.amax(all_filecounts_np), normed=0)

  # insertions and deletions
  plt.figure(1)
  ax_std = ax_all[1]
  capped_insert = all_insertions_np[np.nonzero(all_insertions_np < id_max)]
  # in_n, in_bins, in_patches = ax_std.hist(all_insertions_np, id_max, normed=0, label='insert')
  # de_n, de_bins, de_patches = ax_std.hist(all_deletions_np, id_max, normed=0, label='delete')
  in_n, in_bins, in_patches = ax_std.hist([all_insertions_np, all_deletions_np], id_max, normed=0)
  uname_ind = 0
  # for uname in all_timeseries:
  #   if uname_ind % 50 == 1: print uname_ind
  #   uname_ind += 1
  #   time_array = all_timeseries[uname]
  #   posix_times = time_array[:,0]
  #   commit_inds = time_array[:,1]
  #   filecounts = time_array[:,2]
  #   insertions = time_array[:,3]
  #   deletions = time_array[:,4]

  #   # file counts
  #   plt.figure(0)
  #   ax_std = ax_all[0]
  #   #ax_std.scatter(commit_inds, filecounts, marker='.', lw=0)
  #   fc_n, fc_bins, fc_patches = ax_std.hist(filecounts, max(filecounts), normed=1)

  #   # insertions and deletions
  #   plt.figure(1)
  #   ax_std = ax_all[1]
  #   in_n, in_bins, in_patches = ax_std.hist(insertions, max(insertions), normed=1)
  #   de_n, de_bins, de_patches = ax_std.hist(deletions, max(deletions), normed=1)
  #   #ax_std.scatter(commit_inds, insertions, marker='.', c='g', lw=0, alpha=0.08)
  #   #ax_std.scatter(commit_inds, deletions, marker='.', c='r', lw=0, alpha=0.08)

  # file counts
  title_str = "%s file counts over commit" % (year_q)
  plt.figure(0)
  ax_std = ax_all[0]
  # ax_std.set_xlim(0, max_commits)
  # ax_std.set_ylim(fc_min, fc_max)
  # ax_std.set_xlabel('commit')
  # ax_std.set_ylabel('file counts changed')
  file_count_dest = os.path.join(output_dir, '%s_file_counts.png' % year_q)
  print "Saving file count figure", file_count_dest
  fig_all[0].savefig(file_count_dest)
  plt.close(fig_all[0])

  # insertions and deletions
  title_str = "%s insertions and deletions over commit" % (year_q)
  plt.figure(1)
  ax_std = ax_all[1]
  print "id max", id_max
  # ax_std.set_ylim(id_min, id_max)
  # ax_std.set_xlabel('commit')
  # ax_std.set_ylabel('insertions over time')
  insert_delete_dest = os.path.join(output_dir, '%s_insertions_deletions.png' % year_q)
  print "Saving insertions and deletions figure", insert_delete_dest
  fig_all[1].savefig(insert_delete_dest)
  plt.close(fig_all[1])

def plot_times(output_dir, zoom=False):
  # POSIX time difference in seconds.
  for year_q in os.listdir(output_dir):
    if not os.path.isdir(os.path.join(output_dir, year_q, output_stats_dir)):
      continue
    output_stats_path = os.path.join(output_dir, year_q, output_stats_dir)
    all_students_f = os.listdir(output_stats_path)
    all_students_f.sort()

    graph_size = 100
    tot_graphs = 0
    plot_graph = True
    while plot_graph:
      print "%s: Graph %d" % (year_q, tot_graphs)
      all_times = []
      students = []
      last_submit_hash = []
      curr_k = 0
      for k in range(graph_size):
        student_ind = k + tot_graphs*graph_size
        if student_ind >= len(all_students_f):
          plot_graph = False
          break
        student = all_students_f[student_ind]
        student_log_file = os.path.join(output_stats_path, student)
        with open(student_log_file, 'r') as f:
          lines = f.readlines()
          student_times = np.array([int(line.split('\t')[1]) \
                              for line in lines])
          last_submit_hash.append(lines[-1].split('\t')[0])
          all_times.append(student_times)
          students.append(student.split('.')[0]) # <student>.txt
      tot_graphs += 1
      offset_time = min([np.amin(times) for times in all_times])
      offset_times = [times for times in all_times]
      print "Creating subplot axis."
      fig = plt.figure(figsize=(18,6))
      ax1 = plt.gca()
      fig.canvas.set_window_title('%s' % year_q)
      print "Starting box plot."
      bp = plt.boxplot(offset_times)
      # # ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey',
      # #            alpha=0.5)
      print "Adding x labels."
      numBoxes = len(students)
      # #ax1.set_xlim(0.5, numBoxes + 0.5)
      # top = 40
      # bottom = -5
      # ax1.set_ylim(bottom, top)
      xtickNames = plt.setp(ax1, xticklabels=students)
      plt.setp(xtickNames, rotation=90, fontsize=8)

      # print "Adding y labels."
      ylims = ax1.get_ylim()
      new_lb = ylims[0] + (ylims[1] - ylims[0])/2
      new_lb, new_ub = ylims
      if zoom:
        new_lb = np.median(np.array([np.amin(times) for times in all_times]))
        new_ub = np.median(np.array([np.amax(times) for times in all_times]))
      ax1.set_ylim(new_lb, new_ub)
      y_steps = 10
      posix_range = np.linspace(new_lb, new_ub, y_steps)
      labels = [(date.fromtimestamp(posix_t)).strftime('%m/%d %H:%M') for posix_t in posix_range]
      print labels
      ax1.set_yticks(posix_range)
      ytickNames = plt.setp(ax1, yticklabels=labels)
      #plt.setp(ytickNames, rotation=45, fontsize=8)

      # add title
      ax1.set_title("Sample data worktime distribution.")
      plt.tight_layout()
      # #plt.show()
      graph_name = "boxplot_%s_%s.png" % (year_q, tot_graphs)
      if zoom:
        graph_name = "boxplot_%s_%s_zoom.png" % (year_q, tot_graphs)
      print "Saving box plot to %s" % graph_name
      fig.savefig(os.path.join(output_dir, graph_name))
