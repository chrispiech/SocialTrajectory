#!/usr/bin/python3

import os, sys, subprocess
import pymoss
import shutil
import threading
from multiprocessing import Pool as ThreadPool
import time

top_dir = os.getcwd()

baseline = True # running only final submissions against each other
use_sample = False
use_all_quarters = True
#TARGET_DIR_NAME = "expanded_dir3"
TARGET_DIR_NAME = "expanded_mass"
TARGET_DIR = os.path.join(top_dir, TARGET_DIR_NAME)

FINAL_SUBMISSIONS_DIR_NAME = "final_submissions"
FINAL_SUBMISSIONS_DIR = os.path.join(TARGET_DIR, FINAL_SUBMISSIONS_DIR_NAME)
LECTURE_DIR_NAME = "lecture"
LECTURE_DIR = os.path.join(TARGET_DIR, LECTURE_DIR_NAME)
ONLINE_DIR_NAME = "online" # all known online versions
ONLINE_DIR = os.path.join(TARGET_DIR, ONLINE_DIR_NAME)
NOONLINE_DIR_NAME = "noonline"
STARTER_DIR_NAME = "STARTER"
STARTER_DIR = os.path.join(TARGET_DIR, STARTER_DIR_NAME)

MOSS_DIR_NAME = "moss_mass"
MOSS_OUTPUT_DIR = os.path.join(top_dir, MOSS_DIR_NAME)
FILETYPE = "java"


def call_cmd(cmd):
  return subprocess.Popen([cmd],stdout=subprocess.PIPE, shell=True).communicate()[0]

def baseline(CURRENT_Q):
  #current_q = 'baseline'
  current_q = os.path.join('final_submissions', CURRENT_Q)
  #current_q = 'final_submissions' # for holdout and mass; all quarters!

  OUTPUT_TEMP_DIR_NAME = "baseline_temp"

  cwd = os.getcwd()
  os.chdir(TARGET_DIR)
  print("in dir", TARGET_DIR)
  m = pymoss.Runner(FILETYPE)
  m.add(STARTER_DIR_NAME, pymoss.util.STARTER)
  m.add_all(ONLINE_DIR_NAME, pymoss.util.ARCHIVE)
  m.add_all(current_q)
  num_dirs = len(os.listdir(os.path.join(TARGET_DIR, current_q)))
  num_dirs_ceil = (num_dirs/100+1)*100

  m.run(npairs=num_dirs_ceil)
  h = pymoss.Html(m, "%s" % current_q)
  moss_dir = (h.gen_all(OUTPUT_TEMP_DIR_NAME)).split('/')[-1]

  target_dir = os.path.join(MOSS_OUTPUT_DIR, 'baseline', CURRENT_Q)
  if os.path.exists(target_dir):
    shutil.rmtree(target_dir)
  elif not os.path.exists(os.path.join(MOSS_OUTPUT_DIR, 'baseline')):
    os.makedirs(os.path.join(MOSS_OUTPUT_DIR, 'baseline'))
  mv_cmd = "mv %s %s" % (os.path.join(cwd, moss_dir), target_dir)
  print("moving moss output:", mv_cmd)
  call_cmd(mv_cmd)
  os.chdir(cwd)

from multiprocessing import Lock, Value
class LockedCounter(object):
  def __init__(self):
    self.lock = Lock()
    self.count = Value('i', 0)
  
  def incr_and_get(self):
    with self.lock:
      self.count.value += 1
      return self.count.value

global_counter = LockedCounter()

def multi_moss(CURRENT_Q):
  # make temp dir in base_dir
  # for each dir in target_dir, add to temp
  # once directory is generated, move to moss_output_dir
  current_q_dir = os.path.join(TARGET_DIR, CURRENT_Q)
  moss_q_dir = os.path.join(MOSS_OUTPUT_DIR, CURRENT_Q)
  if not os.path.exists(moss_q_dir):
    os.makedirs(moss_q_dir)

  count = -1 # run all of them
  # uname = '2014010069'
  # if uname not in commit: continue
  commits = os.listdir(current_q_dir)
  if count != -1: commits = commits[:count]
  commit_tot = len(commits)
  zipped_args = [(commit, commit_tot, CURRENT_Q) \
      for commit in commits]
  pool = ThreadPool(8) # 8 at once?
  results = pool.map(thread_process, zipped_args)
  pool.close()
  pool.join()

def thread_process(args):
  commit, commit_tot, current_q = args
  current_q_dir = os.path.join(TARGET_DIR, current_q)
  moss_q_dir = os.path.join(MOSS_OUTPUT_DIR, current_q)
  final_q_dir = os.path.join(FINAL_SUBMISSIONS_DIR, current_q)

  commit_count = global_counter.incr_and_get()
  print("{}/{}: starting moss for commit {}".format(
    commit_count, commit_tot, commit))

  commit_moss_dir = os.path.join(moss_q_dir, commit)
  if os.path.exists(commit_moss_dir):
    print("redoing...")
    shutil.rmtree(commit_moss_dir)
  temp_dir = prepare_temp_dir(current_q_dir, commit)
  if not temp_dir:
    print("skipping dir %s (no %s files)" % (commit, FILETYPE))
    return

  # make basically no threshold
  it_worked = False # hack
  m = make_moss_runner(temp_dir, final_q_dir)
  try:
    gen_moss_output(m, commit, commit_moss_dir)
  finally: m.cleanup()

  rm_cmd = "rm -r %s" % temp_dir
  call_cmd(rm_cmd)

def prepare_temp_dir(expanded_moss_dir, commit):
  commit_dir = os.path.join(expanded_moss_dir, commit)
  java_files = filter(lambda fname: FILETYPE in fname,
              os.listdir(commit_dir))
  if not java_files:
    return ''
  temp_dir = "temp_%s" % commit
  if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
  os.mkdir(temp_dir)
  for java_f in java_files:
    f_prefix = java_f.split('.')[0]
    java_moss_dir = os.path.join(temp_dir,
                          '%s_%s' % (commit, f_prefix))
    os.mkdir(java_moss_dir)
    cp_cmd = "cp %s %s/." % (os.path.join(commit_dir, java_f),
                              java_moss_dir)
    call_cmd(cp_cmd)
  return temp_dir

def make_moss_runner(self_dir, other_dir):
  m = pymoss.Runner(FILETYPE, threshold=10 ** 9)
  m.add(STARTER_DIR, pymoss.util.STARTER)
  m.add_all(self_dir, prefix="")
  m.add_all(other_dir, pymoss.util.ARCHIVE)
  m.add_all(ONLINE_DIR, pymoss.util.ARCHIVE)
  return m

def gen_moss_output(moss_runner, commit, output_dir):
  moss_runner.run(npairs=5)
  output_temp_dir = 'output_%s' % commit
  if os.path.exists(output_temp_dir):
    shutil.rmtree(output_temp_dir)
  h = pymoss.Html(moss_runner, "%s" % commit)
  #moss_dir = (h.gen_all(output_temp_dir)).split('/')[-1]
  moss_dir = h.gen_all(output_temp_dir)
  mv_cmd = "mv %s %s" % (moss_dir, output_dir)
  print("moving moss output to", output_dir)
  call_cmd(mv_cmd)

def seconds_to_time(seconds):
  dec = ("%.4f" % (seconds % 1)).lstrip('0')
  m, s = divmod(seconds, 60)
  h, m = divmod(m, 60)
  return "%d:%02d:%02d%s" % (h, m, s, dec)
 
if __name__ == "__main__":
  # for year_q_dirname in os.listdir(TARGET_DIR):
  #   try:
  #     year, q = year_q_dirname.split('_')
  #     int(year), int(q)
  #   except: continue

  runtimes = []
  year_q_dirnames = ["2012_1", "2013_1", "2014_1"]
  for year_q_dirname in year_q_dirnames:
    start_time = time.time()
    # pymoss.util.time("Running all moss {}".format(year_q_dirname),
    #     lambda: multi_moss(year_q_dirname))
    pymoss.util.time("Running baseline moss {}".format(year_q_dirname),
        lambda: baseline(year_q_dirname))
    end_time = time.time()
    runtimes.append(end_time - start_time)

  print("Summary of times for each quarter...")
  for year_q, time_elapsed in zip(year_q_dirnames, runtimes):
    print("{}: {} ({})".format(year_q,
      seconds_to_time(time_elapsed), time_elapsed))
