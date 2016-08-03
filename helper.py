import os, sys, subprocess
import shutil
import numpy as np
import matplotlib as mpl
mpl.use('Agg') # to enable non ssh -X
import matplotlib.pyplot as plt
import matplotlib.cm as cmx
import matplotlib.colors as mplcolors
import javalang
import re
import itertools
from time import strptime, mktime
from datetime import datetime
from pytz import timezone
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

# time stuff
pst = timezone('US/Pacific')
all_start_time = mktime(datetime(2012,10,15,tzinfo=pst).timetuple())
all_end_time = mktime(datetime(2012,10,24,15,15,tzinfo=pst).timetuple())
incr_length = 86400/2

def posix_to_time(posix_t, format_str=None):
	if not format_str:
		format_str = '%m/%d %H:%M'
	return pst.localize(datetime.fromtimestamp(posix_t)).strftime(format_str)

# top sim loading
add_str = ''
def load_top_sims_from_log(output_dir, year_q, use_diff=False):
  if use_diff:
    year_q = 'diff_%s' % year_q
  top_sim_path = os.path.join(output_dir, "%s_top_sim%s.csv" % (year_q, add_str))
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
  if "final_submissions" in output_f:
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
  for lookup in os.listdir(lookup_folder):
    year_q, ext = lookup.split('.')
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
    lookup_dest = os.path.join(lookup_folder, '%s.%s' % (year_q, 'lookup2222'))
    with open(lookup_dest, 'w') as f:
      for uname in uname_lookup_by_year_q[year_q]:
        f.write('%s,%s\n' % (uname_lookup_by_year_q[year_q][uname], uname))
    lookup_orig = os.path.join(lookup_folder, '%s.%s' % (year_q, 'lookup'))
    mv_cmd = "cp %s %s" % (lookup_dest, lookup_orig)
    print "Moving", mv_cmd
    call_cmd(mv_cmd)

"""Plot black line on the aggregate student plot.
This marks the 95th percentile for similarities at any given timestep.
(well, this doesn't actually plot it, but that would be the intention)
"""
def med_calc(times, sims, med_thresh=87):
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
  for student_f in os.listdir(stats_dir):
    uname = student_f.split('.')[0]
    lookup_dict[uname] = {}
    with open(os.path.join(stats_dir, student_f), 'r') as f:
      lines = f.readlines()
      for i, line in zip(range(len(lines)-1, -1, -1), lines):
        posix_time = line.split('\t')[1]
        lookup_dict[uname][int(posix_time)] = i
  return lookup_dict

"""
student --> (midterm, final)
max midterm score: 120
max final score: 180

Some students dropped the class after the midterm, so they have no
final grade. These students have '-1' for a final grade.
"""
def load_exam_grades(output_dir, year_q):
  grades_dir = os.path.join(output_dir, 'grades')
  fname = '%s.csv' % year_q
  if fname not in os.listdir(grades_dir):
    return {}

  grades_dict = {}
  with open(os.path.join(grades_dir, fname), 'r') as f:
    for line in f.readlines():
      line = line.strip()
      uname, mt, final = line.split(',')
      if mt == '': mt = -1
      if final == '': final = -1
      grades_dict[uname] = (int(mt), int(final))
  return grades_dict

"""
With respect to the array c_grades, which is an array
with values in [0.0, 1.0]
"""
def set_colormap(c_grades):
  colormap=c_grades
  norm = mpl.colors.Normalize(vmin=min(c_grades), vmax=max(c_grades))
  m=cmx.ScalarMappable(norm=norm, cmap=cmx.jet)
  m.set_array(colormap)
  return m

def get_rankings(grades): #, starttimes, endtimes, duration):
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
  mt_list = []
  f_list = []
  for uname in grades_dict:
    mt, f = grades_dict[uname]
    if mt != -1:
      mt_list.append((mt, uname))
    if f != -1:
      f_list.append((f, uname))
  m_grades, m_unames = zip(*mt_list)
  m_inds = np.argsort(np.array(m_grades))
  m_rankdict = {}
  for rank in range(len(m_unames)):
    ind = m_inds[rank]
    m_rankdict[m_unames[ind]] = (m_grades[ind]/float(mt_max),
                                 rank/float(len(m_unames)))
  f_rankdict = {}
  f_grades, f_unames = zip(*f_list)
  f_inds = np.argsort(np.array(f_grades))
  for rank in range(len(f_unames)):
    ind = f_inds[rank]
    f_rankdict[f_unames[ind]] = (f_grades[ind]/float(f_max),
                                 rank/float(len(f_unames)))
  return m_rankdict, f_rankdict

