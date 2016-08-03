from helper import *
from git_helper import *
from time import strptime
from datetime import date
from scipy.interpolate import interp1d
from scipy.interpolate import UnivariateSpline
from scipy.misc import derivative
from scipy.signal import argrelextrema

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

def graph_gradetime(output_dir, year_q):
  top_sims = load_top_sims_from_log(output_dir, year_q)
  exam_grades = load_exam_grades(output_dir, year_q)
  output_stats_path = os.path.join(output_dir, year_q)
  print "year_q:", year_q

  posix_lookup = load_posix_to_commit_ind(output_dir, year_q)
  
  # returns scaled grades
  # note duration is # commits, not endtimes-starttimes.
  starttimes, endtimes, commit_lengths, mt_grades, f_grades = \
      get_gradetimes(top_sims, posix_lookup, exam_grades)
  
  make_scatterplot(output_dir, '%s_%s' % (year_q, "Midterms"),
                mt_grades, starttimes, endtimes, commit_lengths)
  
  make_scatterplot(output_dir, '%s_%s' % (year_q, "Finals"),
                f_grades, starttimes, endtimes, commit_lengths)

  end_vs_start(output_dir, '%s_%s' % (year_q, "Midterm_Finals"),
                mt_grades, f_grades,
                starttimes, endtimes, commit_lengths)

"""
Returns start, end, and ranges, and grades sorted by uname.
"""
def get_gradetimes(top_sims, posix_lookup, exam_grades,
                mt_max=120.0, f_max=180.0):
  stats = []
  unames = top_sims.keys()
  unames.sort()
  for uname in unames:
    if uname not in exam_grades:
      print "skipping %s" % uname
      continue
    all_posix = [int(posix) for posix in posix_lookup[uname].keys()]
    start_posix, end_posix = min(all_posix), max(all_posix)
    commit_length = len(all_posix)
    mt_grade, f_grade = exam_grades[uname][:2]
    mt_grade, f_grade = mt_grade/mt_max, f_grade/f_max
    stats.append((start_posix, end_posix, commit_length, mt_grade, f_grade))
  return zip(*stats)

def get_time_info(top_sims, posix_lookup):
  time_info = []
  unames = top_sims.keys()
  unames.sort()

  for uname in unames:
    set_stats = {}
    # get start and end posix times..
    time_info.append((start_posix, end_posix, range_posix))
  return zip(*time_info)
  
def get_grades(grade_dict, mt_max=120, f_max=180):
  grades = []
  unames = grade_dict.keys()
  unames.sort()
  for uname in unames:
    # get midterm and final grades
    #for info in grades[uname]:
    grade0=float(grade_dict[uname][0])/mt_max
    grade1=float(grade_dict[uname][1])/f_max
    grades.append((grade0, grade1))
    #print grade0, grade1
    # if grade0 not in set_grades0:
    #   set_grades0[grade0] = []
    # set_grades0[grade0].append((int(grade0)))
    # for grade0 in set_grades0:
    #   if uname not in midterm_grades:
    #     midterm_grades[uname] = {}
    #   midterm_grades[uname] = \
    #     np.array(set_grades0[grade0])
    # if grade1 not in set_grades1:
    #   set_grades1[grade1] = []
    # set_grades1[grade1].append((int(grade1)))
    # for grade1 in set_grades1:
    #   if uname not in final_grades:
    #     final_grades[uname] = {}
    #   final_grades[uname] = \
    #     np.array(set_grades1[grade1])
  return zip(*grades)
  
"""
grades are out of 140 or 180 for mt and final, respectively
converted_grades are ranks. e.g., top student is 1/#students
"""
def make_scatterplot(output_dir, name, grades, starttimes, endtimes, commit_length):
  print "Creating figures for %s figure." % (name)
  fig, ax =plt.subplots(2,2, figsize=(60,30),sharey=True)
  rankings = get_rankings(grades)
  time_duration = np.array(endtimes) - np.array(starttimes)
  
  area=np.pi*10**2 # size of circle
  #alpha: darker the circle, the more points of data there are
  m=set_colormap(grades)
  time_fstr = '%m/%d\n%H:%M'

  # graphing
  label_fs = 30
  tick_fs = 30
  # absolute grades
  ax[0,0].scatter(starttimes, time_duration, s=area, c=grades, lw=0, alpha=0.7)
  ax[0,0].set_title('Duration vs start time (absolute grades)', fontsize=label_fs)
  ax[0,1].scatter(endtimes, time_duration, s=area, c=grades, lw=0, alpha=0.7)
  ax[0,1].set_title('Duration vs end time (absolute grades).', fontsize=label_fs)
  # student ranking
  ax[1,0].scatter(starttimes, time_duration, s=area, c=rankings, lw=0, alpha=0.7)
  ax[1,0].set_title('Duration vs start time (rankings)', fontsize=label_fs)
  ax[1,1].scatter(endtimes, time_duration, s=area, c=rankings, lw=0, alpha=0.7)
  ax[1,1].set_title('Duration vs end time (rankings).', fontsize=label_fs)
  # 

  ##### ylabels (duration)
  print "Setting Time durations."
  ylims=ax[0,0].get_ylim()
  new_ub=1625000 #adjust as needed
  new_lb=0        #adjust as needed
  # all y axes are duration. :)
  ax[0,0].set_ylim(new_lb, new_ub)
  #ax2.set_ylim(new_lb, new_ub)
  ax[1,0].set_ylim(new_lb, new_ub)
  y_steps=6
  posix_range=np.linspace(new_lb, new_ub, y_steps)
  mod_t=[]
  for posix_t in posix_range:
    rem_d=posix_t%(86400)
    days=(posix_t-rem_d)/86400
    rem_h=rem_d%3600
    hours=(rem_d-rem_h)/3600
    mod_t.append('%sd %shr' % (round(days), round(hours)))
  ax[0,0].set_yticks(posix_range)
  ax[0,0].set_yticklabels(mod_t,fontsize=tick_fs)
  ax[1,0].set_yticks(posix_range)
  ax[1,0].set_yticklabels(mod_t,fontsize=tick_fs)
  ax[0,0].set_ylabel('Assignment duration', fontsize=label_fs)
  ax[1,0].set_ylabel('Assignment duration', fontsize=label_fs)

  ##### xlabels (start time, then end time)
  print "Adding start time xlabel." # ax1 and ax3
  #new_xlb_st = 1350300000  #adjust as needed
  new_xlb_st = mktime(datetime(2012,10,15,0,0,tzinfo=pst).timetuple())
  new_xub_st = mktime(datetime(2012,10,25,0,0,tzinfo=pst).timetuple())
  x_steps = 10
  posix_xrange_st = np.linspace(new_xlb_st, new_xub_st, x_steps)
  xlabels_st = [posix_to_time(posix_t, format_str=time_fstr) \
            for posix_t in posix_xrange_st]
  ax[0,0].set_xlim(new_xlb_st, new_xub_st)
  ax[0,0].set_xticks(posix_xrange_st)
  ax[0,0].set_xticklabels(xlabels_st, rotation=45, fontsize=tick_fs)
  ax[1,0].set_xlim(new_xlb_st, new_xub_st)
  ax[1,0].set_xticks(posix_xrange_st)
  ax[1,0].set_xticklabels(xlabels_st, rotation=45, fontsize=tick_fs)
  # add labels
  ax[1,0].set_xlabel('Start times.', fontsize=label_fs)
  
  print "Adding end time label." # xlabel on bottom subplots
  new_xlb_end = mktime(datetime(2012,10,21,15,15,tzinfo=pst).timetuple())
  #new_xub_end = 1351500000  #adjust as needed
  # a day later than all_end_time
  new_xub_end = mktime(datetime(2012,10,25,15,15,tzinfo=pst).timetuple())
  posix_xrange_end = np.linspace(new_xlb_end, new_xub_end, x_steps)
  xlabels_end = [posix_to_time(posix_t, format_str=time_fstr) \
            for posix_t in posix_xrange_end]
  ax[0,1].set_xlim(new_xlb_end, new_xub_end)
  ax[0,1].set_xticks(posix_xrange_end)
  ax[0,1].set_xticklabels(xlabels_end, rotation=45, fontsize=tick_fs)
  ax[1,1].set_xlim(new_xlb_end, new_xub_end)
  ax[1,1].set_xticks(posix_xrange_end)
  ax[1,1].set_xticklabels(xlabels_end, rotation=45, fontsize=tick_fs)
  # add labels
  ax[1,1].set_xlabel('End times.', fontsize=label_fs)

  # save figure
  fig.tight_layout()
  fig.subplots_adjust(right=0.94)
  cbar_ax = fig.add_axes([0.95, 0.07, 0.02, 0.8])
  cbar_ax.tick_params(labelsize=tick_fs)
  fig.colorbar(m, cax=cbar_ax)
  fname = os.path.join(output_dir, '%s.png' % name)
  print fname
  fig.savefig(fname) 

def end_vs_start(output_dir, name, mt_grades, f_grades, starttimes, endtimes, commit_lengths):
  print "Creating figures for %s figure." % (name)
  fig, axs =plt.subplots(4,2, figsize=(44,80))
  mt_rankings = get_rankings(mt_grades)
  f_rankings = get_rankings(f_grades)
  commit_lengths = np.array(commit_lengths)
  time_durations = np.array(endtimes) - np.array(starttimes)
  
  area=np.pi*10**2 # size of circle
  #alpha: darker the circle, the more points of data there are
  m=set_colormap(mt_grades) # doesn't really matter which one
  time_fstr = '%m/%d\n%H:%M'

  # graphing
  label_fs = 30
  tick_fs = 30
  axs[0,0].scatter(endtimes, starttimes, s=area, c=mt_grades, lw=0, alpha=0.7)
  axs[0,0].set_title('Start vs end time (absolute MT grades)', fontsize=label_fs)
  axs[0,1].scatter(endtimes, starttimes, s=area, c=f_grades, lw=0, alpha=0.7)
  axs[0,1].set_title('Start vs end time (absolute Final grades)', fontsize=label_fs)
  axs[1,0].scatter(endtimes, starttimes, s=area, c=mt_rankings, lw=0, alpha=0.7)
  axs[1,0].set_title('Start vs end time (MT rankings)', fontsize=label_fs)
  axs[1,1].scatter(endtimes, starttimes, s=area, c=f_rankings, lw=0, alpha=0.7)
  axs[1,1].set_title('Start vs end time (Final rankings)', fontsize=label_fs)
  axs[2,0].scatter(commit_lengths, starttimes, s=area,c=mt_rankings,lw=0,alpha=0.7)
  axs[2,0].set_title('Start time vs commit length (MT rankings)', fontsize=label_fs)
  axs[2,1].scatter(commit_lengths, starttimes, s=area,c=f_rankings,lw=0,alpha=0.7)
  axs[2,0].set_title('Start time vs commit length (Final rankings)', fontsize=label_fs)
  axs[3,0].scatter(commit_lengths, time_durations, s=area,c=mt_rankings,lw=0,alpha=0.7)
  axs[3,0].set_title('Time spent vs commit length (MT rankings)', fontsize=label_fs)
  axs[3,1].scatter(commit_lengths, time_durations, s=area,c=f_rankings,lw=0,alpha=0.7)
  axs[3,1].set_title('Time spent vs commit length (Final rankings)', fontsize=label_fs)

  # start time bounds
  new_ylb = mktime(datetime(2012,10,15,0,0,tzinfo=pst).timetuple())
  new_yub = mktime(datetime(2012,10,25,0,0,tzinfo=pst).timetuple())
  # end time bounds
  new_xlb = mktime(datetime(2012,10,21,15,15,tzinfo=pst).timetuple())
  new_xub = mktime(datetime(2012,10,25,15,15,tzinfo=pst).timetuple())
  ##### ylabels
  print "Adding ylabel start time."
  y_steps = 10
  posix_yrange = np.linspace(new_ylb, new_yub, y_steps)
  ylabels = [posix_to_time(posix_t, format_str=time_fstr) \
            for posix_t in posix_yrange]
  for ax in [axs[0,0],axs[0,1],axs[1,0],axs[1,1],axs[2,0],axs[2,1]]:
    #ax.set_ylim(new_ylb, new_yub)
    ax.set_ylim(new_yub, new_ylb) # reverse so that last time is on bottom
    ax.set_yticks(posix_yrange[::-1])
    ax.set_yticklabels(ylabels[::-1], rotation=45, fontsize=tick_fs)
  # add labels
  axs[0,0].set_ylabel('Start times', fontsize=label_fs)
  axs[1,0].set_ylabel('Start times', fontsize=label_fs)
  axs[2,0].set_ylabel('Start times', fontsize=label_fs)
  # duration stuff
  time_ub = new_xub - new_ylb # end time to start time
  time_lb=0        #adjust as needed
  posix_range=np.linspace(time_lb, time_ub, 6) # y_steps
  mod_t=[]
  for posix_t in posix_range:
    tot_hours = int(posix_t) / 3600
    days = tot_hours / 24
    hours = tot_hours % 24
    rem_d=posix_t%(86400)
    mod_t.append('%sd %shr' % (round(days), round(hours)))
  # reverse axes
  axs[3,0].set_ylim(time_ub, time_lb)
  axs[3,1].set_ylim(time_ub, time_lb)
  axs[3,0].set_yticks(posix_range[::-1])
  axs[3,1].set_yticks(posix_range[::-1])
  axs[3,0].set_yticklabels(mod_t[::-1], fontsize=tick_fs)
  axs[3,1].set_yticklabels(mod_t[::-1], fontsize=tick_fs)
  axs[3,0].set_ylabel('Time duration', fontsize=label_fs)
  axs[3,1].set_ylabel('Time duration', fontsize=label_fs)


  ##### xlabels
  print "Adding xlabel end time."
  x_steps = 10
  posix_xrange = np.linspace(new_xlb, new_xub, x_steps)
  xlabels = [posix_to_time(posix_t, format_str=time_fstr) \
            for posix_t in posix_xrange]
  for ax in [axs[0,0],axs[0,1],axs[1,0],axs[1,1]]:
    #ax.set_ylim(new_ylb, new_yub)
    ax.set_xlim(new_xlb, new_xub)
    ax.set_xticks(posix_xrange)
    ax.set_xticklabels(xlabels, rotation=45, fontsize=tick_fs)
  axs[2,0].set_xlim(0, axs[2,0].get_xlim()[1])
  axs[2,1].set_xlim(0, axs[2,1].get_xlim()[1])
  axs[3,0].set_xlim(0, axs[3,0].get_xlim()[1])
  axs[3,1].set_xlim(0, axs[3,1].get_xlim()[1])

  # add labels
  axs[1,0].set_xlabel('End times (Midterm)', fontsize=label_fs)
  axs[1,1].set_xlabel('End times (Final)', fontsize=label_fs)
  axs[2,0].set_xlabel('Commit lengths', fontsize=label_fs)
  axs[2,1].set_xlabel('Commit lengths', fontsize=label_fs)
  axs[3,0].set_xlabel('Commit lengths', fontsize=label_fs)
  axs[3,1].set_xlabel('Commit lengths', fontsize=label_fs)
  
  # save figure
  fig.tight_layout()
  fig.subplots_adjust(right=0.94)
  cbar_ax = fig.add_axes([0.95, 0.07, 0.02, 0.8])
  cbar_ax.tick_params(labelsize=tick_fs)
  fig.colorbar(m, cax=cbar_ax)
  fname = os.path.join(output_dir, '%s.png' % name)
  print fname
  fig.savefig(fname) 

def plot_times(output_dir, zoom=False, use_top_sims=False):
  # POSIX time difference in seconds.
  for year_q in os.listdir(output_dir):
    if not os.path.isdir(os.path.join(output_dir, year_q, output_stats_dir)):
      continue
    output_stats_path = os.path.join(output_dir, year_q, output_stats_dir)
    all_students_f = os.listdir(output_stats_path)
    all_students_f.sort()

    # load top sims if necessary
    top_sims = {}
    if use_top_sims:
    	top_sims = load_top_sims_from_log(output_dir, year_q)

    graph_size = 100
    tot_graphs = 0
    plot_graph = True
    while plot_graph:
      print "%s: Graph %d" % (year_q, tot_graphs)
      all_times = []
      students = []
      curr_k = 0
      for k in range(graph_size):
        student_ind = k + tot_graphs*graph_size
        if student_ind >= len(all_students_f):
          plot_graph = False
          break
        student_ext = all_students_f[student_ind] # <student>.txt
        student_log_file = os.path.join(output_stats_path, student_ext)
        student = student_ext.split('.')[0]
        if use_top_sims and student in top_sims:
          student_times = [int(posix_t) \
                  for posix_t in top_sims[student].keys()]
          student_times.sort()
        else:
          with open(student_log_file, 'r') as f:
            lines = f.readlines()
            student_times = np.array([int(line.split('\t')[1]) \
                                for line in lines])
        all_times.append(student_times)
        students.append(student)
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
