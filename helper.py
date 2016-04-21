import os, sys, subprocess
import shutil
import numpy as np
import matplotlib as mpl
mpl.use('Agg') # to enable non ssh -X
import matplotlib.pyplot as plt

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
