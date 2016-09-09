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
  try:
    month_int = int(month)
  except:
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
  
  make_scatter_dur_time(output_dir, '%s_%s' % (year_q, "Midterms"),
                mt_grades, starttimes, endtimes, commit_lengths)
  
  make_scatter_dur_time(output_dir, '%s_%s' % (year_q, "Finals"),
                f_grades, starttimes, endtimes, commit_lengths)

  make_scatter_g_time(output_dir, '%s_%s' % (year_q, "Midterms"),
                mt_grades, starttimes, endtimes, commit_lengths)

  make_scatter_g_time(output_dir, '%s_%s' % (year_q, "Finals"),
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
def make_scatter_dur_time(output_dir, name, grades, starttimes, endtimes, commit_length):
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

def make_scatter_g_time(output_dir, name, grades, starttimes, endtimes, commit_length):
  name = '%s_vs_grade' % name
  print "Creating figures for %s figure." % (name)
  fig, ax =plt.subplots(2,3, figsize=(60,45))
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
  ax[0,0].scatter(starttimes, grades, s=area, c=grades, lw=0, alpha=0.7)
  ax[0,0].set_title('Grades vs start time (absolute grades)', fontsize=label_fs)
  ax[0,1].scatter(endtimes, grades, s=area, c=grades, lw=0, alpha=0.7)
  ax[0,1].set_title('Grades vs end time (absolute grades).', fontsize=label_fs)
  ax[0,2].scatter(time_duration, grades, s=area, c=grades, lw=0, alpha=0.7)
  ax[0,2].set_title('Grades vs duration (absolute grades).', fontsize=label_fs)
  # student ranking
  ax[1,0].scatter(starttimes, grades, s=area, c=rankings, lw=0, alpha=0.7)
  ax[1,0].set_title('Grades vs start time (rankings)', fontsize=label_fs)
  ax[1,1].scatter(endtimes, grades, s=area, c=rankings, lw=0, alpha=0.7)
  ax[1,1].set_title('Grades vs end time (rankings).', fontsize=label_fs)
  ax[1,2].scatter(time_duration, grades, s=area, c=rankings, lw=0, alpha=0.7)
  ax[1,2].set_title('Grades vs duration (rankings).', fontsize=label_fs)
  # 

  ##### ylabels (grades)
  print "Setting grade ranking."
  for ax_a in ax[0,:]:
    ax_a.set_ylim(0,1.0)
    ax_a.set_ylabel('Grade (absolute)', fontsize=label_fs)
  for ax_r in ax[1,:]:
    ax_r.set_ylim(0,1.0)
    ax_r.set_ylabel('Grade (ranking)', fontsize=label_fs)

  ##### xlabels (duration, start time, and end time)
  print "Setting Time durations."
  new_ub=1625000 #adjust as needed
  new_lb=0        #adjust as needed
  x_steps=6
  posix_range=np.linspace(new_lb, new_ub, x_steps)
  mod_t=[]
  for posix_t in posix_range:
    rem_d=posix_t%(86400)
    days=(posix_t-rem_d)/86400
    rem_h=rem_d%3600
    hours=(rem_d-rem_h)/3600
    mod_t.append('%sd %shr' % (round(days), round(hours)))
  ax[0,2].set_xlim(new_lb, new_ub)
  ax[1,2].set_xlim(new_lb, new_ub)
  ax[0,2].set_xticks(posix_range)
  ax[0,2].set_xticklabels(mod_t,fontsize=tick_fs)
  ax[1,2].set_xticks(posix_range)
  ax[1,2].set_xticklabels(mod_t,fontsize=tick_fs)
  ax[0,2].set_xlabel('Assignment duration', fontsize=label_fs)
  ax[1,2].set_xlabel('Assignment duration', fontsize=label_fs)

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

"""
sort_types:
  # commits
  grades
One figure per quarter, split into percentiles.
  Plots all commit times per student based on sort_type metric.
"""
COMMIT_TYPE = 0
GRADE_TYPE = 1
START_TYPE = 2
END_TYPE = 3
def plot_times_sorted(output_dir, year_q, cluster=True):
  ################ load points for each user ###############
  top_sims = load_top_sims_from_log(output_dir, year_q)
  posix_lookup = load_posix_to_commit_ind(output_dir, year_q)
  # all_points[uname][posix_time] -> addtl data
  all_points = get_points(top_sims, posix_lookup, cluster=cluster)

  exam_grades = load_exam_grades(output_dir, year_q)
  mt_gr, f_gr = get_graderank_dict(exam_grades)
  print "year_q:", year_q
  all_stats = []
  # get PER USER stats (not actual plot points)
  max_cluster_size = 1
  for uname in all_points:
    uname_stats = []
    all_posix = posix_lookup[uname].keys()
    start_posix, end_posix, num_commits = min(all_posix), max(all_posix), len(all_posix)
    mt_gr_uname, f_gr_uname = (1.0,1.0), (1.0,1.0)
    if uname not in mt_gr:
      continue
    else:
      mt_gr_uname = mt_gr[uname]
    if uname not in f_gr:
      continue
    else:
      f_gr_uname = f_gr[uname]
    uname_stats.append(
        (start_posix, end_posix, num_commits,
         mt_gr_uname[0], mt_gr_uname[1],
         f_gr_uname[0], f_gr_uname[1],
         int(uname)))
    all_stats += uname_stats

    if cluster:
      cluster_sizes = [len(x) for x in all_points[uname].values()]
      max_cluster_size = max(max(cluster_sizes), max_cluster_size)
  all_stats_np = np.array(all_stats)
  print "max cluster size:", max_cluster_size

  # creates 2 x n/2 (two columns), vs default n/2 x 2 (two rows)
  use_vertical = True

  graph_options = list(itertools.product((True, False), (True, False),
                      (False, True),
                      (GRADE_TYPE, COMMIT_TYPE, START_TYPE, END_TYPE)))
  for use_mt, use_rank, normalize_flag, sort_type in graph_options:
    print "norm flag: %s, use_mt: %s, rank: %s, sort type: %s" % \
        (normalize_flag, use_mt, use_rank, sort_type)
    # indexing variables uname stats
    start_ind, end_ind, length_ind = 0, 1, 2
    mt_g_ind, mt_r_ind = 3, 4
    f_g_ind, f_r_ind = 5, 6
    uname_ind = 7
    grade_ind = mt_g_ind + 2*int(not use_mt) + int(use_rank)

    col_to_sort = all_stats_np[:,length_ind]
    if sort_type == GRADE_TYPE:
      col_to_sort = -all_stats_np[:,grade_ind] # need reverse rank/grade
    elif sort_type == COMMIT_TYPE:
      pass
    elif sort_type == START_TYPE:
      col_to_sort = all_stats_np[:,start_ind]
    elif sort_type == END_TYPE:
      col_to_sort = all_stats_np[:,end_ind]

    sort_inds = np.argsort(col_to_sort)
    sort_col = col_to_sort[sort_inds]

    # # IMPORTANT ##################################################
    numplots = 10 # even number
    num_half = numplots/2
    set_size = len(sort_inds)/numplots
    # to compare best to worst
    # 100 % ------> 50%
    #   0 % <------ 50%
    # worst of each subplot towards center
    # # IMPORTANT ##################################################
    plot_reorg = range(0, num_half) + range(numplots-1, num_half-1, -1)

    # reorg_inds = range(0,set_size*num_half) + \
    #     range(len(sort_inds)-1, set_size*num_half-1, -1)
    #     #len(sort_inds)/2) + \
    #     #range(len(sort_inds)-1,len(sort_inds)/2-1,-1)
    # sort_inds = sort_inds[reorg_inds]
    # sort_col = sort_col[reorg_inds]
    unames_np = all_stats_np[:,uname_ind]
    #all_starts_sort_np = 

    m = set_colormap([0.0, 1.0])
    pixel_spacing = 10

    incr = incr_length
    posix_range = np.arange(all_start_time, all_end_time, step=incr)
    xlabels = [posix_to_time(posix_t) for posix_t in posix_range]

    # indexing variables for all commit stats
    posix_ind, commit_ind = 0, 1
    msize_ind = 2

    ### get user groups ###
    x_grps = []
    y_offss = []
    y_grps = []
    c_grps = []
    w_grps = []
    uname_grid = []
    for plt_grp in xrange(numplots):
      uname_plts = []

      if plt_grp == numplots - 1:
        sort_inds_sub = sort_inds[plt_grp*set_size:]
      else:
        sort_inds_sub = sort_inds[plt_grp*set_size:(plt_grp+1)*set_size]

      unames_sub = unames_np[sort_inds_sub].tolist()
      stats_sub = all_stats_np[sort_inds_sub,:]
      y_spacing = len(unames_sub)*pixel_spacing# * (1 - plt_x)
      y_dir = -1#(plt_x*2-1) # col 1 decr, col 2 incr
      x_grp_grp = []
      y_offs_grp = []
      y_grp_grp = []
      c_grp_grp = []
      w_grp_grp = []
      for i, uname in enumerate(unames_sub):
        y_spacing = y_spacing + y_dir * pixel_spacing
        uname = str(int(uname))
        uname_plts.append(uname)
        uname_stat = stats_sub[i,:].tolist()
        uname_stat.append(y_spacing)

        uname_points = []
        for posix_time in all_points[uname]:
          if not cluster:
            commit_num = posix_lookup[uname][int(posix_time)]
            count = 1
          else: # posix time is a cluster time. Find closest.
            closest_posix_time = find_nearest(posix_lookup[uname].keys(),
                                    posix_time)
            commit_num = posix_lookup[uname][closest_posix_time]
            count = len(all_points[uname][posix_time]) # size of posix
          uname_points.append(
              (int(posix_time), int(commit_num), count))
        uname_points_np = np.array(uname_points)

        times = uname_points_np[:,posix_ind]
        weights = uname_points_np[:,msize_ind]
        #float(max_cluster_size)
        # print uname_points_np[:,msize_ind]/float(max_cluster_size)
        # print '\t',msizes
        norm_gran = 3 # decimal granularity
        if normalize_flag:
          times = np.around(uname_points_np[:,commit_ind]/uname_stat[length_ind],
                            decimals=norm_gran)
        grades = uname_stat[grade_ind]
        c = m.to_rgba(grades)

        x_grp_grp.append(times)
        y_offs_grp.append(y_spacing)
        y_grp_grp.append(np.ones(times.shape))
        c_grp_grp.append(c)
        w_grp_grp.append(weights)
        uname_grid.append(uname_plts)

      x_grps.append(x_grp_grp)
      y_grps.append(y_grp_grp)
      y_offss.append(y_offs_grp)
      c_grps.append(c_grp_grp)
      w_grps.append(w_grp_grp)
              
    ################ plot points for each user ###############
    max_ms = 18
    if cluster:
      max_ms = 50
    # num rows, num cols, width, height
    if use_vertical:
      fig, ax_all = plt.subplots(num_half, 2, figsize=(30, 15*num_half))
    else:
      fig, ax_all = plt.subplots(2, num_half, figsize=(15*num_half, 30))
    for plt_ind in xrange(numplots):
      plt_y, plt_x = plt_ind/num_half, plt_ind % num_half
      if use_vertical:
        plt_x, plt_y = plt_y, plt_x
      #print "x:%d, y:%d (%d num_half)" % (plt_x, plt_y, num_half)
      plt_tup = (plt_y, plt_x)
      if num_half == 1:
        plt_tup = plt_ind

      reorg_ind = plot_reorg[plt_ind]
      use_reverse = 1-2*int(plt_ind/num_half == 1)
      plt_grp = zip(x_grps[reorg_ind], y_offss[reorg_ind][::use_reverse],
                    y_grps[reorg_ind], c_grps[reorg_ind],
                    w_grps[reorg_ind])
      for times, y_offs, y_grp, c, weights in plt_grp:
        y = (y_offs-1) + y_grp # y_offs determines the data's horizontal line offset
        # normalize
        msizes = max_ms*weights/float(np.amax(weights))

        ax_all[plt_tup].plot(times, y,
                marker='.', mew=0.0,
                lw=1,
                color=c)
        ax_all[plt_tup].scatter(times, y,
                marker='o', lw=0, s=msizes,
                color=c)
    ######## create an aggregate figure with everything
    use_hist = True
    use_stack = True
    use_interval = True
    use_outline = False
    use_exclusive = True
    exclusive_range = [0, 9]
    fig_aggr = plt.figure(figsize=(10,10))
    ax_aggr = plt.gca()
    posix_range_aggr = np.arange(all_start_time-incr, all_end_time+incr, step=incr)
    xlabels_aggr = [posix_to_time(posix_t) for posix_t in posix_range_aggr]
    # histogram widths and start points
    lefts = []
    num_bins = numplots
    for lower_time in posix_range_aggr[0::2]:
      bar_range = np.linspace(lower_time+incr*0.1, lower_time+2*incr*0.85,num=num_bins)#[:-1])
      lefts.append(bar_range)
    bottoms = [0.1*np.ones(l.shape) for l in lefts]
    bar_width_abs = lefts[0][1] - lefts[0][0]
    weight_by_time_int = []
    max_cluster_size_time_int = []
    data_by_time_int = []
    time_time_ints = zip(posix_range_aggr[0::2], posix_range_aggr[2::2])
    num_time_ints = len(time_time_ints)
    # sort by time intervals first
    for interval in xrange(num_time_ints):
      lower_time, upper_time = time_time_ints[interval]
      interval_data = []
      for plt_ind in xrange(numplots):
        y_spacing_aggr = numplots - plt_ind - 1
        c = m.to_rgba(y_spacing_aggr/float(numplots))
        plt_grp = zip(x_grps[plt_ind], y_offss[plt_ind],
                      y_grps[plt_ind], c_grps[plt_ind],
                      w_grps[plt_ind])
        max_time = []
        times = np.concatenate(x_grps[plt_ind])
        weights = np.concatenate(w_grps[plt_ind])
        colors_extend = [np.tile(c_grps[plt_ind][i], (w_grps[plt_ind][i].shape[0],1)) \
                          for i in range(len(w_grps[plt_ind]))]
        colors = np.concatenate(colors_extend)

        valid_times_inds = np.nonzero(np.logical_and(times >= lower_time, times < upper_time))
        valid_times = times[valid_times_inds]
        valid_weights = weights[valid_times_inds]
        valid_colors = colors[valid_times_inds]
        valid_matrix = np.zeros((valid_times.shape[0],7))
        valid_matrix[:,0] = valid_times
        valid_matrix[:,1] = valid_weights
        valid_matrix[:,2] =plt_ind*np.ones(valid_weights.shape)
        valid_matrix[:,3:] = valid_colors
        #interval_data.append(np.concatenate(valid_times, valid_weights, valid_colors))
        if valid_matrix.shape[0]:
          interval_data.append(valid_matrix)
        if valid_weights.shape[0] and np.amax(valid_weights) > 0 and not use_hist:
          ax_aggr.scatter(valid_times,
                        y_spacing_aggr*np.ones(valid_times.shape),
                        c=np.tile(c, valid_times.shape),
                        s=max_ms*valid_weights/float(np.amax(valid_weights)),
                        lw=0,
                        alpha=0.5)
          pass
      interval_data_np = np.concatenate(interval_data)
      weight_time_int = interval_data_np[:,1]
      # weight_time_int = np.array(weight_time_int) # row: weights per grade
      # grade_time_int = np.repmat(np.linspace(0, 1.0, num=numplots).T, weight
      #max_cluster_size_time_int.append(max([np.amax(vw) for vw in weight_time_int if vw.shape[0]]))
      max_cluster_size_time_int.append(max(np.amax(weight_time_int), 0))
      weight_by_time_int.append(weight_time_int)
      data_by_time_int.append(interval_data_np)

    # get largest cluster size
    # largest_cluster = max([max(np.concatenate(w_grps[plt_ind])) for plt_ind in \
    #                           range(numplots)])
    print "max cluster size", max_cluster_size
    # TODO: fix max cluster size issue -- 347 vs 571
    print "test max cluster size", max([np.amax(x[:,1]) for x in data_by_time_int])
    max_cluster_size = max([np.amax(x[:,1]) for x in data_by_time_int])
    #sizebins = np.logspace(0, np.log10(max_cluster_size_time_int[interval]), num=num_bins+1)
    sizebins = np.linspace(0, max_cluster_size, num=num_bins+1)
    print "sizebins", sizebins
    ylabels_aggr = np.arange(0.0, 1.0, 0.1)
    if use_hist and use_interval:
      ylabels_aggr = map(lambda (x, y): "(%.2f, %.2f)" % (x, y), zip(sizebins[:-1], sizebins[1:]))
      ylabels_aggr = ylabels_aggr[::-1]

    max_bar_height = float(max([x.shape[0] for x in data_by_time_int]))
    print "max bar height", max_bar_height
    print "sizes by interval", [x.shape[0] for x in data_by_time_int]
    for interval in xrange(num_time_ints):
      #weight_time_int = weight_by_time_int[interval]
      data_time_int = data_by_time_int[interval]
      if not max_cluster_size_time_int[interval]: continue
      if not max_cluster_size_time_int[interval]: continue
      #num_weights_time_int = [len(weights) for weights in weight_time_int]
      #scaler = max(max(num_weights_time_int), 1)
      weight_time_int = data_time_int[:,1]
      plt_ind_time_int = data_time_int[:,2]
      plt_ind_bins = range(numplots+1)
      color_bins = m.to_rgba(np.arange(numplots,-1,-1)/float(numplots))
      interval_info = []
      for lower_lim, upper_lim, y_spacing_aggr in zip(sizebins[:-1], sizebins[1:], range(numplots-1,-1,-1)):
        interval_inds = np.nonzero(np.logical_and(weight_time_int >= lower_lim, weight_time_int < upper_lim))
        interval_info.append((interval_inds, y_spacing_aggr))
      max_interval_size = float(max([len(x[0][0]) for x in interval_info]))
      print "max interval size", max_interval_size
      print [len(x[0][0]) for x in interval_info]
      for interval_inds, y_spacing_aggr in interval_info:
        weights_interval = weight_time_int[interval_inds]
        print "lower %s, upper %s" % (lower_lim, upper_lim)
        if not weights_interval.shape[0]: print "empty"; continue
        plt_ind_interval = plt_ind_time_int[interval_inds]
        hist, bin_edges = np.histogram(plt_ind_interval, bins=plt_ind_bins,
                                       density=True)
        pmf = hist*np.diff(bin_edges)
        interval_size = weights_interval.shape[0]
        pmf_scaled = pmf*data_time_int.shape[0]/max_bar_height*interval_size/max_interval_size
        #pmf_scaled = pmf*interval_size/max_interval_size
        lefts_time_int = lefts[interval]
        bottoms_time_int = bottoms[interval]

        if use_hist and use_interval:
          ax_aggr.bar(lefts_time_int,
                    pmf_scaled,
                    width=bar_width_abs,
                    #bottom=bottoms_time_int,
                    bottom=y_spacing_aggr,
                    lw=0,
                    color=color_bins)
          pass

        bottoms[interval] = bottoms_time_int + pmf_scaled

      tot_weights = float(max([len(np.nonzero(plt_ind_time_int == plt_ind)) for plt_ind in range(numplots)]))
      tot_weights = float(max([weight_time_int[np.nonzero(plt_ind_time_int == plt_ind)].shape[0] for plt_ind in range(numplots)]))
      if use_exclusive:
        tot_weights = float(max([weight_time_int[np.nonzero(plt_ind_time_int == plt_ind)].shape[0] for plt_ind in exclusive_range]))
      print "weights by plt", [weight_time_int[np.nonzero(plt_ind_time_int == plt_ind)].shape[0] for plt_ind in range(numplots)]

      bottoms[interval] = 0.0*np.ones(lefts[interval].shape)
      max_interval_size_2 = [x.shape[0] for x in data_by_time_int]
      print "weights by interval", max_interval_size_2
      print "max weight by plt", tot_weights, "max weight by interval", max(max_interval_size_2)
      max_interval_size_2 = float(max(max_interval_size_2))

      if use_hist and not use_interval:
        ylabels_aggr = np.arange(0.0, 1.0, 0.1)
        if use_stack:
          if use_exclusive:
            ylabels_aggr *= tot_weights
          else:
            ylabels_aggr *= max_interval_size_2
      for plt_ind in xrange(numplots):
        if use_exclusive and plt_ind not in exclusive_range: continue
        #weight_plt_ind = weight_time_int[plt_ind]

        #onum_num_weights = float(num_weights_time_int[plt_ind])
        weight_plt_ind = weight_time_int[np.nonzero(plt_ind_time_int == plt_ind)]
        num_weights = weight_plt_ind.shape[0]
        hist, bin_edges = np.histogram(weight_plt_ind, bins=sizebins,
                                       density=True)
        pmf = hist*np.diff(bin_edges)
        if use_exclusive:
          pmf_scaled = pmf * num_weights/tot_weights
        else:
          pmf_scaled = pmf * weight_time_int.shape[0]/max_interval_size_2
        if not use_stack:
          pmf_scaled = num_weights/tot_weights * pmf * weight_time_int.shape[0]/max_interval_size_2

        y_spacing_aggr = numplots - plt_ind - 1
        c = m.to_rgba(y_spacing_aggr/float(numplots))
        lefts_time_int = lefts[interval]
        bottoms_time_int = bottoms[interval]

        if use_hist and not use_interval:
          ax_aggr.bar(lefts_time_int,
                    pmf_scaled,
                    width=bar_width_abs,
                    bottom=int(not use_stack) * y_spacing_aggr + int(use_stack) * bottoms_time_int,
                    lw=int(use_outline),
                    color=c)
          pass

        bottoms[interval] = bottoms_time_int + pmf_scaled
        # print "prev bottoms", bottoms_time_int
        # print "new bottoms", bottoms[interval]

    # add labels and set axes
    title_str = "%s students sorted by" % (year_q)
    if sort_type == GRADE_TYPE:
      title_str += " grade"
    elif sort_type == COMMIT_TYPE:
      title_str += " commit"
    elif sort_type == START_TYPE:
      title_str += " start time"
    if normalize_flag:
      title_str += " (normalized)"
    exam_str = "mt"
    rank_str = "rank"
    if not use_mt: exam_str = "final"
    if not use_rank: rank_str = "abs"
    title_str += "(%s, %s)" % (exam_str, rank_str)
    fig.suptitle(title_str)
    ax_aggr.set_title("%s (aggr)" % title_str)

    # axes
    for plt_ind in xrange(numplots):
      plt_y, plt_x = plt_ind/num_half, plt_ind % num_half
      if use_vertical:
        plt_x, plt_y = plt_y, plt_x
      plt_tup = (plt_y, plt_x)
      if num_half == 1:
        plt_tup = plt_y
      
      # x-axis: time
      if not normalize_flag:
        ax_all[plt_tup].set_label('Date')
        ax_all[plt_tup].set_xlim(all_start_time, all_end_time)
        ax_all[plt_tup].set_xticks(posix_range)
        ax_all[plt_tup].set_xticklabels(xlabels, rotation=45, fontsize=8)
      else:
        ax_all[plt_tup].set_label('Normalized progress over commits')
        ax_all[plt_tup].set_xlim(0.0, 1.0)

      # y-axis: percentile (maybe have this be sort_col?)
      num_skip = 10
      yticks = np.arange(0,
                         set_size*pixel_spacing,
                         pixel_spacing*num_skip)
      if plt_ind == numplots - 1:
        sort_col_sub = sort_col[plt_ind*set_size:]
      else:
        sort_col_sub = sort_col[plt_ind*set_size:(plt_ind+1)*set_size]

      ylabels = sort_col_sub[::-num_skip].tolist()

      if sort_type == GRADE_TYPE:
        ylabels = map(lambda f : '%.2f' % (-1*f),
                    ylabels)
      elif sort_type in [START_TYPE, END_TYPE]:
        ylabels = map(posix_to_time, ylabels)
      else:
        ylabels = map(int, ylabels)

      ax_all[plt_tup].set_ylim(-2*pixel_spacing, # pad top/bottom
                               (set_size+2)*pixel_spacing)
      ax_all[plt_tup].set_yticks(yticks)
      ax_all[plt_tup].set_yticklabels(ylabels)

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
    #ax_aggr.set_yticks(np.arange(1.0, 0, 0.1))

    fig.tight_layout()
    fig.subplots_adjust(right=0.94)
    # cbar_ax = fig.add_axes([0.95, 0.07, 0.02, 0.8])
    # cbar_ax.tick_params()
    # fig.colorbar(m, cax=cbar_ax)
    fig_prefix = '%s_students' % year_q
    if sort_type == COMMIT_TYPE:
      fig_prefix += '_commit'
    elif sort_type == GRADE_TYPE:
      fig_prefix += '_grade'
    elif sort_type == START_TYPE:
      fig_prefix += '_start'
    elif sort_type == END_TYPE:
      fig_prefix += '_end'
    if normalize_flag:
      fig_prefix += '_norm'
    fig_prefix += '_%s_%s' % (exam_str, rank_str)
    if cluster:
      fig_prefix += '_kmeans'
    fig_dest = os.path.join(output_dir, '%s.png' % fig_prefix)
    print "Saving", fig_dest
    fig.savefig(fig_dest)
    plt.close(fig)

    fig_aggr.tight_layout()
    fig_aggr_prefix = '%s_aggr' % fig_prefix
    fig_aggr_dest = os.path.join(output_dir, '%s.png' % fig_aggr_prefix)
    print "Saving", fig_aggr_dest
    fig_aggr.savefig(fig_aggr_dest)
    plt.close(fig_aggr)

"""
Returns points to plot per user.
all_points[uname][posix_time] -> addtl data
Clustering might happen here!!

note: posix_lookup is a superset of all usernames
  that can be returned in all_points.
"""
def get_points(top_sims, posix_lookup, cluster=False):
  all_points = posix_lookup
  if not cluster:
    pass
  else:
    all_points = {}
    for uname in posix_lookup:
      #print uname
      posix_times = posix_lookup[uname].keys()
      k_results = k_means(posix_times)
      if k_results:
        all_points[uname] = k_results
      else:
        print "uname errored", uname
  return all_points

"""
k-means clustering of the data.

Returns dictionary:
result[m] --> [datapoint list]
"""
def k_means(data, incr=0):
  if not incr:
    global incr_length
    incr = incr_length
  posix_range = np.arange(all_start_time, all_end_time, step=incr)
  min_d, max_d = min(data), max(data)
  floor_d = int(incr * (round(float(min_d)/incr)-1))
  ceil_d = int(incr * (round(float(max_d)/incr)+1))
  ms = posix_range[np.nonzero(posix_range >= floor_d)]
  ms = ms[np.nonzero(ms <= ceil_d)]
  k = ms.shape[0]
  if k == 0:
    print "error with this dataset"
    # print map(posix_to_time, data)
    # print data
    print "data: (%s, %s) vs assgt: (%s, %s) " % tuple(map(posix_to_time,
        [floor_d, ceil_d, all_start_time, all_end_time]))
    return {}
  #print "k means (k=%d):" % k
  sets = [[]] * k

  num_iters = 10
  data = np.array(data) # assume 1D!
  for i in range(num_iters):
    # assign
    new_sets = []
    new_ms = []
    bcast = np.tile(ms, (data.shape[0],1)).T
    bcast = np.absolute(bcast - data) # | x - m_j |, L1 norm (1-dimension)
    argms = np.argmin(bcast, axis=0)
    for m in ms:
      m_data = data[np.nonzero(ms[argms] == m)]
      new_sets.append(m_data)
      if len(m_data) != 0:
        new_ms.append(np.mean(m_data))
      else:
        new_ms.append(m)
    new_ms = np.array(new_ms)

    # update
    changes = [len(np.setxor1d(old, new)) for \
          (old, new) in zip(sets, new_sets)]
    if sum(changes) == 0:
      #print "breaking at iter", i
      break

    
    ms = new_ms
    sets = new_sets
  result = {}
  for m, s in zip(ms, sets):
    result[m] = s
  return result

"""
Array may not be a numpy list; convert first.
"""
def find_nearest(array, value):
  idx = (np.abs(np.array(array)-value)).argmin()
  return array[idx]

def plot_k_means(output_dir, year_q):
  ################ load points for each user ###############
  top_sims = load_top_sims_from_log(output_dir, year_q)
  posix_lookup = load_posix_to_commit_ind(output_dir, year_q)
  # all_points[uname][posix_time] -> addtl data
  all_points = get_points(top_sims, posix_lookup, cluster=True)

  exam_grades = load_exam_grades(output_dir, year_q)
  mt_gr, f_gr = get_graderank_dict(exam_grades)
  print "year_q:", year_q
  all_stats = []

"""
Box plots of all times, nothing else.
"""
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
