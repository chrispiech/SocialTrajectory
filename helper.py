import os, sys, subprocess
import shutil
import numpy as np
import matplotlib as mpl
mpl.use('Agg') # to enable non ssh -X
import matplotlib.pyplot as plt
import matplotlib.cm as cmx
import matplotlib.colors as mplcolors
#import javalang
import re
import itertools
from time import mktime, strptime
from datetime import datetime
import pytz
from lxml import etree
from lxml import html

# directory things
def load_path():
  with open('file_path.csv', 'r') as f:
    top_dir = f.readline().strip().split(',')[0]
  return top_dir

top_dir = load_path()

# popen stuff
def call_cmd(cmd):
  return subprocess.Popen([cmd],stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()

# threshold stuff for grouping
thresh_token = 250 # 180 # for baseline: 180,23
thresh_p_self = 0
thresh_p_other = 25
def check_thresh(tokens, p_self, p_other,norm_commit=0, meds=None):
  #print tokens >= thresh_token and p_self >= thresh_p_self and p_other >= thresh_p_other
  return tokens >= thresh_token and p_self >= thresh_p_self and p_other >= thresh_p_other

  # ignore the below, which uses meds as well.
  if not meds:
    return tokens >= thresh_token and p_self >= thresh_p_self and p_other >= thresh_p_other

  floor_norm_commit = float('%.3f' % norm_commit)
  token_med, _, p_other_med = meds[floor_norm_commit]
  return tokens > token_med and p_other > p_other_med

def get_hours(posix_list, work_limit=0):
  posix_list = map(int, posix_list)
  posix_list.sort()
  if work_limit:
    posix_list = filter(lambda posix: posix < work_limit, posix_list)
  num_seconds = 0.0
  time_worked = []
  posix_worked = []
  gap = float(day_length/24)/2 # half an hour
  if not posix_list: # not started work
    return num_seconds, posix_worked
  diffs = (np.array(posix_list[1:]) - np.array(posix_list[:-1])).tolist()
  num_seconds = sum(filter(lambda diff: diff < gap, diffs))
  gap_indices = filter(lambda i: i != -1, map(lambda (i, diff): i if diff >= gap else -1, enumerate(diffs)))
  prev_ind = 0
  for gap_index in gap_indices:
    if prev_ind != gap_index:
      posix_worked.append((posix_list[prev_ind], posix_list[gap_index]))
      time_worked.append(sum(diffs[prev_ind:gap_index]))
    prev_ind = gap_index+1
  if prev_ind != len(diffs):
    posix_worked.append((posix_list[prev_ind], posix_list[-1]))
    time_worked.append(sum(diffs[prev_ind:]))

  return num_seconds/float(day_length/24), posix_worked



# time stuff
pst = pytz.timezone('US/Pacific')
utc = pytz.utc
day_length = 86400
pst_shift = 25200
incr_length = day_length/2 # 12 hours

# all_start_time = mktime(datetime(2012,10,15,tzinfo=pst).timetuple())
# all_end_time = mktime(datetime(2012,10,24,15,15,tzinfo=pst).timetuple()) # deadline
# all_end_time = mktime(datetime(2012,10,25, 1, 0,tzinfo=pst).timetuple())

# dictionary of posix values
START_TIME, END_TIME = 0, 1
all_startend_times = {\
    '2012_1': (mktime(datetime(2012,10,15,13,15,tzinfo=pst).timetuple()),
      mktime(datetime(2012,10,24,15,15,tzinfo=pst).timetuple())), # 3:15pm (9)
    '2013_2': (mktime(datetime(2013, 1,30,14,58,tzinfo=pst).timetuple()),
      mktime(datetime(2013, 2, 8,15,15,tzinfo=pst).timetuple())), # 3:15pm (9)
    '2013_3': (mktime(datetime(2013, 4,19,13,34,tzinfo=pst).timetuple()),
      mktime(datetime(2013, 4,29,13,15,tzinfo=pst).timetuple())), # 1:15pm (10)
    '2013_4': (mktime(datetime(2013, 7, 7,16,23,tzinfo=pst).timetuple()),
      mktime(datetime(2013, 7,16,13,15,tzinfo=pst).timetuple())), # 1:15pm (9)
    '2013_1': (mktime(datetime(2013,10,13,19, 5,tzinfo=pst).timetuple()),
      mktime(datetime(2013,10,23,15,15,tzinfo=pst).timetuple())), # 3:15pm (10)
    '2014_2': (mktime(datetime(2014, 1,31,21, 2,tzinfo=pst).timetuple()),
      mktime(datetime(2014, 2,10,15,15,tzinfo=pst).timetuple())), # 3:15pm (10)
    '2014_3': (mktime(datetime(2014, 4,21,10,23,tzinfo=pst).timetuple()),
      mktime(datetime(2014, 4,30,12, 0,tzinfo=pst).timetuple())), # 12:00pm (9)
    '2014_4': (mktime(datetime(2014, 7, 9,14, 8,tzinfo=pst).timetuple()),
      mktime(datetime(2014, 7,17,16, 0,tzinfo=pst).timetuple())), # 4:00pm (8)
    '2014_1': (mktime(datetime(2014,10,13,13,26,tzinfo=pst).timetuple()),
      mktime(datetime(2014,10,22,15,15,tzinfo=pst).timetuple()))} # 3:15pm (9)

MT_TIME = 0
FINAL_TIME = 1
all_exam_times = {'2012_1': (mktime(datetime(2012, 11,  1,19, 0, tzinfo=pst).timetuple()),
                             mktime(datetime(2012, 12, 14,12,15, tzinfo=pst).timetuple())),
                  '2013_1': (mktime(datetime(2013, 10, 29,19, 0, tzinfo=pst).timetuple()),
                             mktime(datetime(2013, 12, 12,12,15, tzinfo=pst).timetuple())),
                  '2014_1': (mktime(datetime(2014, 10, 29,19, 0, tzinfo=pst).timetuple()),
                             mktime(datetime(2014, 12, 10,12,15, tzinfo=pst).timetuple()))}


def posix_to_datetime(posix_t, format_str=None):
  if not format_str:
    format_str = '%m/%d %H:%M'
  return utc.localize(datetime.fromtimestamp(posix_t)).astimezone(pst).strftime(format_str)

"""
Get the day only (get the day's midnight)
ex: YYYY/MM/DD hh:mm --> YYYY/MM/DD 00:00
"""
def date_floor(posix_t):
  return day_length * (int(posix_t)/day_length) + pst_shift

"""
Get the next day (get the next day's midnight)
ex: YYYY/MM/DD hh:mm --> YYYY/MM/(DD+1) 00:00
"""
def date_ceiling(posix_t):
  return day_length * (int(posix_t)/day_length + 1) + pst_shift


"""
Scale to same day timeline.
This is done by calculating the posix difference between the deadline for
  old_year_q to the deadline for 2014_1 (the latest), and then scaling
  all the input posix_t's days by that interval.

posix_times should be a single int or a numpy array, not a list. :)
"""
def scale_days(posix_times, old_year_q, new_year_q=None):
  if not new_year_q: new_year_q = '2014_1'
  is_list = False
  try:
    posix_times.shape
  except:
    is_list = True
    posix_times = np.array(posix_times)
  # new_end_floor = date_floor(all_startend_times[new_year_q][END_TIME])
  # old_end_floor = date_floor(all_startend_times[old_year_q][END_TIME])
  # diff_deadline = new_end_floor - old_end_floor

  diff_deadline = all_startend_times[new_year_q][END_TIME] - \
                  all_startend_times[old_year_q][END_TIME]

  new_posix_times = posix_times + diff_deadline
  if is_list:
    return new_posix_times.tolist()
  return new_posix_times

"""
plus_minus: integer (or decimal) of extra days to tack on to borders.
"""
def get_day_range(year_q, plus_minus=None, incr=None, include_point=None):
  if not plus_minus:
    plus_minus = [0, 0]
  if not incr:
    incr = day_length/2
  start_floor = date_floor(all_startend_times[year_q][START_TIME])
  end_floor = date_floor(all_startend_times[year_q][END_TIME])
  start_posix = start_floor + plus_minus[START_TIME]*day_length
  end_posix = end_floor + plus_minus[END_TIME]*day_length
  if not include_point:
    return np.arange(start_posix, end_posix+1, incr)

  if include_point < start_posix or include_point > end_posix:
    print "Error in getting day range :|"
  early_range = np.arange(include_point, start_posix-(incr-1), -incr).tolist()[::-1]
  late_range = np.arange(include_point, end_posix, incr).tolist()[1:]
  return early_range + late_range


"""
For a single day, return a string
of the day as a T-<deadline> for this quarter's deadline.
"""
def get_t_minus(posix_time, year_q):
  end_ceil = date_floor(all_startend_times[year_q][END_TIME])
  day_diff = int(date_floor(posix_time) - end_ceil)/day_length
  if day_diff > 0:
    return "T+%02d" % (day_diff)
  return "T-%02d" % (abs(day_diff))

"""
Return only hh:mm
"""
def posix_to_time(posix_t):
  return posix_to_datetime(posix_t, format_str='%H:%M')

# top sim loading
def load_top_sims_from_log(output_dir, year_q, use_diff=0, add_str=''):
  if use_diff == 1:
    year_q = 'diff_%s' % year_q
    add_str = '_insert'
  elif use_diff == 2:
    year_q = 'diff_%s' % year_q
    add_str = '_delete'
  if add_str == 'both' or add_str == 'both_':
    top_sims_online = load_top_sims_from_log(output_dir, year_q, add_str='online_')
    top_sims_reg = load_top_sims_from_log(output_dir, year_q)
    for uname, online_dict in top_sims_online.iteritems():
      if uname not in top_sims_reg:
        print "adding new uname here", uname
        top_sims_reg[uname] = online_dict
      else:
        reg_dict = top_sims_reg[uname]
        # Tends to be the smallest one used when matching on token 25, so just replace? idk
        replace_add = []
        tot_add = len(online_dict)
        for posix_time, info_tup in online_dict.iteritems():

          if posix_time not in reg_dict:
            reg_dict[posix_time] = info_tup
          else:
            token_ind = 1
            # smallest token match is 25, so ignore
            if info_tup[token_ind] < 30 or 'online' in reg_dict[posix_time][0]:
              continue
            elif info_tup[token_ind] >= reg_dict[posix_time][token_ind]:
              replace_add.append((info_tup[token_ind], reg_dict[posix_time][token_ind], reg_dict[posix_time][0]))
              reg_dict[posix_time] = info_tup
        if len(replace_add) > 0:
          #print "uname %s: added %d/%d: %s" % (uname, len(replace_add), tot_add, replace_add)
          pass
    return top_sims_reg

  top_sim_path = os.path.join(output_dir, "%s%s_top_sim.csv" % (add_str, year_q))
  top_sims = {}
  print ">>>>>>>>%s" % top_sim_path
  with open(top_sim_path, 'r') as f:
    line = f.readline()
    uname = ''
    while line:
      line = line.strip()
      if not line:
        uname = ''
      else:
        line_commas = line.split(',')
        if len(line_commas) == 1:
          if uname: print "Error: uname already assigned"
          uname = line
          if uname not in top_sims:
            top_sims[uname] = {}
        else:
          if use_diff:
            _, posix_time, commit_hash = line_commas[0].split('_')
            line_range = line_commas[-1]
            other_f_path, other_f_html, tokens_matched, \
              percent_self, percent_other, commit_num, posix_t_2 = line_commas[1:-1]
            if posix_time not in top_sims[uname]:
              top_sims[uname][posix_time] = {}
            top_sims[uname][posix_time][line_range] = \
              (get_uname_from_f(other_f_path), int(tokens_matched),
                        float(percent_self), float(percent_other),
                        int(commit_num), commit_hash)
          else:
            # own_commit, other_f_path, other_f_html, tokens_matched,
            #       percent_self, percent_other
            _, posix_time, commit_hash = line_commas[0].split('_')
            #posix_time, commit_hash = line_commas[0].split('_')[-2:]
            other_f_path, other_f_html, tokens_matched, \
              percent_self, percent_other, commit_num, posix_t_2 = line_commas[1:]
            top_sims[uname][posix_time] = \
              (get_uname_from_f(other_f_path), int(tokens_matched),
                        float(percent_self), float(percent_other),
                        int(commit_num), commit_hash)
      line = f.readline()
  return top_sims

# assignment code format.
FILETYPE = 'java'
"""
Checks if the directory contains any java files.
If it contains no java files, return False.
"""
def moss_okay(commit_dir, filetype=FILETYPE):
  file_exts = [f.split('.')[-1] for f in os.listdir(commit_dir)]
  if not filetype in file_exts:
    return False
  return True

def get_uname_from_f(output_f):
  # format: final_submissions/year_q_username_num
  # return add username_num
  if "final_submissions" in output_f or 'baseline' in output_f:
    #return '_'.join((output_f.split('/')[-1]).split('_')[2:])
    return output_f.split('/')[-1]
  else:
    # format online/username
    return '_'.join(output_f.split('/'))

def load_uname_to_id_lookup():
  uname_to_id = {}
  
  lookup_folder = os.path.join(top_dir, 'uname_lookup')
  for lookup in os.listdir(lookup_folder):
    year_q, ext = lookup.split('.')
    uname_lookup_year = load_uname_to_id_lookup_single_year_q(year_q)
    for uname in uname_lookup_year:
      uname_to_id[uname] = uname_lookup_year[uname]
  return uname_to_id

def load_uname_lookup_by_year_q():
  uname_to_id = {}
  
  lookup_folder = os.path.join(top_dir, 'uname_lookup')
  all_lookups = filter(lambda fname: fname.endswith('lookup'),
      os.listdir(lookup_folder))
  for lookup in all_lookups:
    year_q = lookup.split('.')[0]
    uname_to_id[year_q] = load_uname_to_id_lookup_single_year_q(year_q)
  return uname_to_id
  
def load_uname_to_id_lookup_single_year_q(year_q):
  uname_to_id = {}
  lookup_folder = os.path.join(top_dir, 'uname_lookup')
  lookup_dest = os.path.join(lookup_folder, '%s.%s' % (year_q, 'lookup'))
  with open(lookup_dest, 'r') as f:
    for line in f.readlines():
      line = line.strip()
      if line:
        ind, uname = line.split(',')
        uname_to_id[uname] = ind
  return uname_to_id

def add_uname_to_lookup(uname, year_q, uname_lookup_by_year_q):
  year, q = year_q.split('_')
  if year_q not in uname_lookup_by_year_q:
    uname_lookup_by_year_q[year_q] = {}
  if uname in uname_lookup_by_year_q[year_q]: return
  uname_id = '%s%02d%04d' % (int(year), int(q), len(uname_lookup_by_year_q[year_q]))
  print "new", uname_id
  uname_lookup_by_year_q[year_q][uname] = uname_id

def export_uname_lookup_by_year_q(uname_lookup_by_year_q):
  lookup_folder = os.path.join(top_dir, 'uname_lookup')
  for year_q in uname_lookup_by_year_q:
    lookup_dest = os.path.join(lookup_folder, '%s.%s' % (year_q, 'lookup'))
    with open(lookup_dest, 'w') as f:
      unames_by_year = uname_lookup_by_year_q[year_q].values()
      unames_by_year.sort()
      print "saving %s unames to quarter %s" % (len(unames_by_year), year_q)
      temp_uname_dict = {}
      for uname, student_id in uname_lookup_by_year_q[year_q].iteritems():
        temp_uname_dict[student_id] = uname
      student_ids = temp_uname_dict.keys()
      student_ids.sort()
      for student_id in student_ids:
        f.write('%s,%s\n' % (student_id, temp_uname_dict[student_id]))
      # for uname in unames_by_year:
      #   f.write('%s,%s\n' % (uname_lookup_by_year_q[year_q][uname], uname))

"""Plot black line on the aggregate student plot.
This marks the 95th percentile for similarities at any given timestep.
(well, this doesn't actually plot it, but that would be the intention)
"""
def med_calc(times, sims, med_thresh=95):
  points_by_time = {}
  for i in range(len(times)):
    #   
    # for times, sims in points_std:
    #   for i in range(len(times)):
    time = times[i]
    if time not in points_by_time:
      points_by_time[time] = []
    points_by_time[time].append(sims[i])
  meds = []
  for time in points_by_time:
    sims_bound = np.percentile(np.array(points_by_time[time]), med_thresh)
    meds.append([time, sims_bound])
  meds_np = np.array(meds)
  meds_np = meds_np[meds_np[:,0].argsort()]
  print "loaded times for median."
  return meds_np

"""
Returns the coordinates of the username label if there
are similarities above the 95th percentile (from med_calc).
"""
def get_label_if_thresh(times, sims, med_lookup):
  times = np.array(times)
  sims = np.array(sims)
  above_thresh = [i for i in range(len(times)) if \
                        sims[i] > med_lookup[times[i]]]
  # almost everyone was above the threshold at some point,
  # so only count a significant number
  min_violations = 0.02
  if above_thresh and len(above_thresh)/float(len(times)) > min_violations:
    fraction_above = sims[above_thresh]/np.array([med_lookup[time] for time in times[above_thresh]])
    max_frac_ind = np.argmax(fraction_above)
    max_time, max_sim = times[above_thresh][max_frac_ind], sims[above_thresh][max_frac_ind]
    return max_time, max_sim, len(above_thresh)/float(len(times))
  return -1, -1, -1

"""
uname --> posix_time --> commit index
commit index: starts from 0.
  if this is the student's 10th snapshot, index = 9
"""
def load_posix_to_commit_ind(output_dir, year_q):
  lookup_dict = {}
  stats_dir = os.path.join(output_dir, year_q, 'stats')
  # for student_f in os.listdir(stats_dir):
  #   uname = student_f.split('.')[0]
  #   lookup_dict[uname] = {}
  #   with open(os.path.join(stats_dir, student_f), 'r') as f:
  #     lines = f.readlines()
  #     for i, line in zip(range(len(lines)-1, -1, -1), lines):
  #       posix_time = line.split('\t')[1]
  #       lookup_dict[uname][int(posix_time)] = i
  moss_dir = os.path.join(output_dir, year_q, 'moss')
  all_lines = filter(lambda fname: fname.endswith('csv'), os.listdir(moss_dir))
  fields = [line.split('_') for line in all_lines]
  temp_dict = {}
  for uname, posix_time, _ in fields:
    if uname not in temp_dict:
      temp_dict[uname] = []
    temp_dict[uname].append(int(posix_time))
  for uname in temp_dict:
    lookup_dict[uname] = {}
    for i, posix_time in enumerate(sorted(temp_dict[uname])):
      lookup_dict[uname][posix_time] = i
    
  return lookup_dict

"""
student --> (start, end, ta_id, prob, sol)
"""
CLASS_NAME = "CS106A"
def load_student_lair(output_dir, year_q):
  lair_dir = os.path.join(output_dir, 'lair')
  fname = '%s_%s.csv' % (CLASS_NAME, year_q)
  if fname not in os.listdir(lair_dir):
    return {}
  lair_dict = {}
  with open(os.path.join(lair_dir, fname), 'r') as f:
    for line in f.readlines():
      line = line.strip()
      # print "len", len(line.split(','))
      # print line.split(',')
      uname, start_str, end_str, ta_uname, prob, sol = line.split(',')
      start_time = mktime(datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pst).timetuple())
      end_time = mktime(datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pst).timetuple())
      if uname not in lair_dict:
        lair_dict[uname] = []
      lair_dict[uname].append((int(start_time), int(end_time), ta_uname))
      #print start_time, end_time
  return lair_dict

"""
With respect to the array input_arr, which is an array
with values in [0.0, 1.0] (or something)
"""
def set_colormap(input_arr=None):
  if input_arr is None:
    input_arr = np.array([0.0, 1.0])
  vmin, vmax = min(input_arr), max(input_arr)

  colormap=input_arr
  norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
  m=cmx.ScalarMappable(norm=norm, cmap=cmx.jet)
  m.set_array(colormap)
  return m

################# grades GRADES #####################
# below is not used...
FUN_1, STY_1, TOT_1, LATE_1 =  0, 1, 2, 3
FUN_2, STY_2, TOT_2, LATE_2 =  4, 5, 6, 7
FUN_3, STY_3, TOT_3, LATE_3 =  8, 9,10,11
FUN_4, STY_4, TOT_4, LATE_4 = 12,13,14,15
FUN_5, STY_5, TOT_5, LATE_5 = 16,17,18,19
FUN_6, STY_6, TOT_6, LATE_6 = 20,21,22,23
FUN_7, STY_7, TOT_7, LATE_7 = 24,25,26,27
MT_IND, F_IND = 29, 28 # flipped

LATE_1, LATE_2, LATE_3 = 0, 1, 2
LATE_4, LATE_5, LATE_6 = 3, 4, 5
LATE_7 = 6
LATE_TOT = 7

letter_lookup = {'++': 7,
  '+': 6,
 'V+': 5,
  'V': 4,
 'V-': 3,
  '-': 2,
 '--': 1}

# below is used...
ASSGT_1, ASSGT_2, ASSGT_3 = 0, 1, 2
ASSGT_4, ASSGT_5, ASSGT_6 = 3, 4, 5
ASSGT_7 = 6
MT_IND, F_IND = 7, 8
NUM_ASSGTS = 7 # almost never use this, it's dangerous
NUM_GRADES = NUM_ASSGTS + 2 # num_assgts + mt + final
G_IND, R_IND = 0, 1
GRADE_MAXES = [100.0,100.0,100.0, # 1, 2, 3 assgt
             100.0,100.0,100.0,100.0, # 4, 5, 6, 7 assgt
             140.0, # mt
             180.0] # final
GRADE_NAMES = ["assgt1", "assgt2", "assgt3",
               "assgt4", "assgt5", "assgt6", "assgt7",
               "mt",
               "final"]
GRADE_TYPES = ["abs", "rank"]

def load_all_graderanks(output_dir, year_q):
    grade_dict = load_all_grades(output_dir, year_q)
    gr = get_graderank_dict(grade_dict)
    return gr

"""
student --> (midterm, final)
Some students dropped the class after the midterm, so they have no
final grade. These students have '-1' for a final grade.
"""
def load_all_grades(output_dir, year_q):
  grades_dir = os.path.join(output_dir, 'grades')
  fname = '%s.csv' % year_q
  if fname not in os.listdir(grades_dir):
    return {}

  grades_dict = {}
  lates_dict = {}
  with open(os.path.join(grades_dir, fname), 'r') as f:
    for line in f.readlines():
      line = line.strip()
      uname = line.split(',')[0]
      grades = line.split(',')[1:]
      grades_entry = []
      lates_entry = []
      for assgt_id in range(NUM_ASSGTS):
        grade_tup = grades[:6]
        grades = grades[6:]
        func_gr, func_l, style_l, style_gr, tot_gr, late_days = grade_tup
        grades_entry.append(float(tot_gr))
        if late_days == '':
          late_days = '0'
        lates_entry.append(int(late_days))
      final, mt, tot_late_days = grades[:3] # skip notes col if present
      if mt == '': mt = -1
      if final == '': final = -1
      # if mt == '' or final == '':
      #   print "skipping uname (no mt/final):", uname
      #   continue
      grades_entry += [int(mt), int(final)]
      lates_entry.append(int(tot_late_days))
      grades_dict[uname] = grades_entry #(int(mt), int(final))
      lates_dict[uname] = lates_entry
  return grades_dict

def get_rankings(grades):
  inds = np.argsort(grades) # smallest to largest
  inds_arg = np.argsort(inds) # ranking indices
  rankings = np.linspace(0.0, 1.0, len(inds))[inds_arg]
  return rankings

"""
Returns two dictionaries (mt and final):
  uname --> (grade, rank)
  grade and rank are both on a scale of 0.0 to 1.0.
"""
def get_graderank_dict(grades_dict, mt_max=140.0, f_max=180.0):
  rankdict = {}
  if not grades_dict:
    return rankdict
  grade_list = []
  for uname in grades_dict:
    # if min(grades_dict[uname]) == -1:
    #   continue
    grade_list.append((uname, grades_dict[uname]))

  unames, all_grades = zip(*grade_list)
  all_grades_np = np.array(all_grades)

  num_grades = all_grades_np.shape[1]
  all_grades = []
  all_ranks = []
  for g_ind in range(num_grades):
    g_s = -1*np.ones((len(grade_list),))
    r_s = -1*np.ones((len(grade_list),))

    grades_i = all_grades_np[:,g_ind]
    nz_grades = np.nonzero(grades_i > -1)[0]
    g_s[nz_grades] = grades_i[nz_grades]/float(GRADE_MAXES[g_ind])
    all_grades.append(g_s.tolist())

    inds_i = np.argsort(grades_i[nz_grades])
    ranks_i = np.linspace(0.0, 1.0, len(nz_grades))[np.argsort(inds_i)]
    r_s[nz_grades] = ranks_i
    all_ranks.append(r_s.tolist())

    # commented out for now because i'm confused
    """
    grades_i = all_grades_np[:,g_ind]
    all_grades.append((grades_i/float(GRADE_MAXES[g_ind])).tolist())
    inds_i = np.argsort(grades_i)
    ranks_i = np.linspace(0.0, 1.0, len(grade_list))[np.argsort(inds_i)]
    all_ranks.append(ranks_i.tolist())
    """

  all_grades = zip(*all_grades)
  all_ranks = zip(*all_ranks)
  for i in range(len(grade_list)):
    rankdict[str(unames[i])] = (all_grades[i], all_ranks[i])
  return rankdict


"""
Get number of ta sessions and hours (posix secs) within a certain period.

Can get ta sessions for only a particular ta as well.
"""
def get_ta_lengths(lair_dict, uname, assgt_no=-1, only_ta_uname=None):
  uname_year, uname_q = uname[:4], uname[4:6]
  year_q = '%s_%s' % (int(uname_year), int(uname_q))
  st_bound = all_startend_times[year_q][START_TIME]
  end_bound = all_startend_times[year_q][END_TIME]
  if assgt_no != -1:
    st_bound = all_startend_times[year_q][START_TIME]
    end_bound = all_startend_times[year_q][END_TIME]

  ta_length = 0
  ta_posix_length = 0
  for start_ta_time, end_ta_time, ta_uname in lair_dict[uname]:
    if start_ta_time >= st_bound and end_ta_time <= end_bound:
      if only_ta_uname and ta_uname is not only_ta_uname:
        continue
      ta_length += 1
      ta_posix_length += end_ta_time - start_ta_time

  return ta_length, ta_posix_length

"""
Returns start/end/student uname for all tas for this particular lair_dict.
Can get total time helped by summing up numpy column.
start_times, end_times, student unames
"""
def get_ta_teaching_times(lair_dict, assgt_no=-1):
  ta_dict = {}
  for uname in lair_dict:
    uname_year, uname_q = uname[:4], uname[4:6]
    year_q = '%s_%s' % (int(uname_year), int(uname_q))
    st_bound = all_startend_times[year_q][START_TIME]
    end_bound = all_startend_times[year_q][END_TIME]
    if assgt_no != -1:
      st_bound = all_startend_times[year_q][START_TIME]
      end_bound = all_startend_times[year_q][END_TIME]
    for start_ta_time, end_ta_time, ta_uname in lair_dict[uname]:
      if start_ta_time >= st_bound and end_ta_time <= end_bound:
        if ta_uname not in ta_dict:
          ta_dict[ta_uname] = {}
        if uname not in ta_dict[ta_uname]:
          ta_dict[ta_uname][uname] = []
        ta_dict[ta_uname][uname].append((start_ta_time, end_ta_time))
  for ta_uname in ta_dict:
    for uname in ta_dict[ta_uname]:
      ta_dict[ta_uname][uname] = np.array(ta_dict[ta_uname][uname])

  return ta_dict

"""
Returns z-score of an assignment.
"""
def get_z_scores(tot_np, grade_ind, scores):
  tot_grades = tot_np[:,grade_ind]
  mean = np.average(tot_grades)
  stdev = np.std(tot_grades)
  return (scores - mean)/stdev

"""
Compares value to a list of values, and returns
the bin that this value fits into.
bins: [1, 2, 3, 4]
val: 0.5 --> returns 0
val: 1 --> returns 0
val: 1.5 --> returns 0
val: 2 --> returns 1
val: 4.5 --> returns 3
"""
def get_bins(val, bins):
  if val < bins[0]:
    return 0
  for i in range(len(bins) - 1):
    if val < bins[i+1]:
      return i
  return len(bins)-1

"""
Use kmeans with k=2 to separate data along a single axis (x by default).
The secondary axis is supplied mainly for plotting purposes.
"""
from scipy import stats as spstats
from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from sklearn import metrics
from sklearn.datasets.samples_generator import make_blobs
from sklearn.preprocessing import StandardScaler

def is_time(arr_or_list):
  np_arr = np.array(arr_or_list)
  return np.average(np_arr) >= all_startend_times['2012_1'][START_TIME]

def separate_kmeans_plot(output_dir, year_q_list,
                    info_np, x_ind, y_ind, titles,
                    k=2, use_y=False, plotstr=None):
  # print "t-test for late vs early", \
  #     spstats.ttest_ind(late_times, early_times,
  #         equal_var=False)
  # print "wilcoxon test for late - early", \
  #     spstats.ranksums(late_times, early_times)
  # print "chi stats, late: %s, early: %s" % \
  #     (spstats.normaltest(late_times),
  #         spstats.normaltest(early_times))
  data_info = info_np[:,x_ind]
  if use_y:
    data_info = info_np[:,y_ind]
  skout = KMeans(n_clusters=k, random_state=0).fit(data_info.reshape(-1, 1))
  # example for DBscan:
  # http://scikit-learn.org/stable/auto_examples/cluster/plot_dbscan.html#sphx-glr-auto-examples-cluster-plot-dbscan-py
  labels = skout.labels_
  thresh_sep = np.average(skout.cluster_centers_)

  # Number of clusters in labels, ignoring noise if present.
  unique_labels = set(labels)
  colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
  fig = plt.figure()
  ax = plt.gca()
  all_x = []
  all_y = []
  for k_val, col in zip(unique_labels, colors):
    class_member_mask = (labels == k_val)
    xy = info_np[class_member_mask]
    all_x += xy[:,x_ind].tolist()
    all_y += xy[:,y_ind].tolist()
    ax.plot(xy[:,x_ind], xy[:,y_ind], 'o', markerfacecolor=col,
                    markeredgecolor='k', markersize=6)
  posix_range = get_day_range(max(year_q_list),plus_minus=[0,2], incr=day_length) # daily
  posix_labels = map(lambda x: posix_to_datetime(x, format_str='%m/%d'), posix_range)

  ax.set_xlabel(titles[x_ind])
  if is_time(info_np[:,x_ind]):
    ax.set_xlim(min(posix_range), max(posix_range))
    ax.set_xticks(posix_range)
    ax.set_xticklabels(posix_labels, fontsize=8, rotation=45)
  ax.set_ylabel(titles[y_ind])
  if is_time(info_np[:,y_ind]):
    ax.set_ylim(min(posix_range), max(posix_range))
    ax.set_yticks(posix_range)
    ax.set_yticklabels(posix_labels, fontsize=8, rotation=45)

  ax.set_title('kmeans separation with %d clusters' % k)
  fig_prefix = '%s_clustersep_%s_%s' % ('_'.join(year_q_list), titles[x_ind], titles[y_ind])
  try:
    '_'.split(year_q_list)
    fig_prefix = '%s_clustersep_%s_%s' % (year_q_list, titles[x_ind], titles[y_ind])
  except:
    pass
  if use_y:
    fig_prefix += '_y'
  if plotstr:
    fig_prefix += '_%s' % plotstr
  fig_dest = os.path.join(output_dir, '%s.png' % fig_prefix)
  print "Saving kmeans cluster figure to", fig_dest
  fig.savefig(fig_dest)

  if fig_prefix == '2012_1_2013_1_2014_1_clustersep_st_hrs_y_all':
    with open(os.path.join(output_dir, '%s.csv' % fig_prefix), 'w') as f:
      f.write('%s\n' % (','.join(map(str, posix_range))))
      f.write('%s\n' % (','.join(map(lambda x: get_t_minus(x, max(year_q_list)), posix_range))))
      f.write('\n'.join(map(lambda (x,y): '%s,%s\n' % (x,y), zip(all_x, all_y))))
      print "Saving kmeans csv file", f.name
  return thresh_sep

def load_meds(output_dir):
  med_by_normcommit = {}
  with open(os.path.join(output_dir, 'moss_meds.csv'), 'r') as f:
    line = f.readline()
    line = f.readline()
    while line:
      line = line.strip()
      norm_commit, token, percent_self, percent_other = line.split(',')
      med_by_normcommit[float(norm_commit)] = (float(token), float(percent_self), float(percent_other))
      line = f.readline()
  #print ">>>>>>med norm commit", med_by_normcommit
  return med_by_normcommit
