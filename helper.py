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

homedir = "/home/ubuntu/"
top_dir = "socialTrajectories"

def call_cmd(cmd):
  return subprocess.Popen([cmd],stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()

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
  
  lookup_folder = os.path.join(homedir, top_dir, 'uname_lookup')
  for lookup in os.listdir(lookup_folder):
    year_q, ext = lookup.split('.')
    uname_lookup_year = load_uname_to_id_lookup_single_year_q(year_q)
    for uname in uname_lookup_year:
      uname_to_id[uname] = uname_lookup_year[uname]
  return uname_to_id

def load_uname_lookup_by_year_q():
  uname_to_id = {}
  
  lookup_folder = os.path.join(homedir, top_dir, 'uname_lookup')
  for lookup in os.listdir(lookup_folder):
    year_q, ext = lookup.split('.')
    uname_to_id[year_q] = load_uname_to_id_lookup_single_year_q(year_q)
  return uname_to_id
  
def load_uname_to_id_lookup_single_year_q(year_q):
  uname_to_id = {}
  lookup_folder = os.path.join(homedir, top_dir, 'uname_lookup')
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
  lookup_folder = os.path.join(homedir, top_dir, 'uname_lookup')
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
