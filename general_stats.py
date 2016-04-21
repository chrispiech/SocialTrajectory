from helper import *
from git_helper import *
from time import strptime
from datetime import date

output_stats_dir = "stats"

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
