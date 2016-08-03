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
def process_diffs(code_dir, output_dir, year_q):
  #line_changes(os.path.join(code_dir, 'dir3'), output_dir)
  process_consecline_stats(output_dir, year_q)

def line_range(line_str):
  start, end = map(int, line_str.split('_'))
  return end - start + 1

"""
Does the actual diffing.
Gets the progress of each commit and saves it in the output dir.
"""
def all_diffs(code_dir, output_dir, year_q):
  #code_dir = os.path.join(code_dir, year_q)
  code_dir = os.path.join(code_dir, 'dir3')
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
          commit_str = '%s_%s_%s' %  (student_id, posix_time, commit)

          all_stats.append((commit_str, file_count, insertion, deletion))

    if not os.path.exists(os.path.join(output_dir, year_q, output_diffs_dir, 'stats')):
      os.makedirs(os.path.join(output_dir, year_q, output_diffs_dir, 'stats'))
    student_log_file = os.path.join(output_dir, year_q, output_diffs_dir, 'stats',
              student_log_name)
    print student_log_file
    with open(student_log_file, 'w') as f:
      f.write('\n'.join(['%s\t%s\t%s\t%s' % stat_line for stat_line in all_stats]))
    print

"""
Just loads statistics of diffs, not the line changes themselves.
"""
def load_diff_stats(output_dir, year_q): # from stats!
  diffs_dir = os.path.join(output_dir, year_q, output_diffs_dir)
  diffstats_dir = os.path.join(diffs_dir, 'stats')
  all_diffs = {}
  for uname in os.listdir(diffstats_dir):
    uname_diff_file = os.path.join(diffstats_dir, uname)
    all_diffs[uname] = {}
    with open(uname_diff_file, 'r') as f:
      line = f.readline()
      while line:
        line = line.strip()
        commit, num_files, insertions, deletions = line.split('\t')
        posix_time = commit.split('_')[1]
        all_diffs[uname][posix_time] = (int(num_files), int(insertions), int(deletions), commit)
        line = f.readline()
  return all_diffs

def process_consecline_stats(output_dir, year_q):
  all_diffs = load_diff_stats(output_dir, year_q)
  diffs_dir = os.path.join(output_dir, year_q, output_diffs_dir)
  insert_dir = os.path.join(diffs_dir, 'insert')
  delete_dir = os.path.join(diffs_dir, 'delete')
  for uname in all_diffs:
    posix_times = all_diffs[uname].keys()
    posix_times.sort()
    stats_dict = {}
    print "starting consecline reading", uname
    for posix in posix_times:
      file_no, insert_no, delete_no, commit = all_diffs[uname][posix]
      # commit = '2012010259_1350909164_2d1fc93'
      # file_no, insert_no, delete_no, commit = all_diffs[commit.split('_')[0]][commit.split('_')[1]]
      inserts, deletes = [], []
      if int(insert_no) > 0:
        if commit not in os.listdir(insert_dir):
          print "\terror: skipping %s insert" % commit
        else:
          for line_no in os.listdir(os.path.join(insert_dir, commit)):
            inserts.append(line_range(line_no))
      if int(delete_no) > 0:
        if commit not in os.listdir(delete_dir):
          print "\terror: skipping %s delete" % commit
        else:
          for line_no in os.listdir(os.path.join(delete_dir, commit)):
            deletes.append(line_range(line_no))
      # print "sanity check %s: insert %s (%s==%s), delete %s (%s==%s)" % \
      #       (commit, insert_no == sum(inserts), insert_no, sum(inserts),
      #             delete_no == sum(deletes), delete_no, sum(deletes))
      stats_dict[posix] = (file_no, inserts, deletes, commit)
    save_consecline_stats(output_dir, year_q, stats_dict, uname)

"""
Per username
"""
def save_consecline_stats(output_dir, year_q, consec_stats, uname):
  consec_dir = os.path.join(output_dir, year_q, 'diffs', 'stats_consec')
  if not os.path.exists(consec_dir):
    os.makedirs(consec_dir)
  posix_times = consec_stats.keys()
  posix_times.sort()
  lines_out = ['%s\t%s\t%s\t%s' % (consec_stats[posix][3],
                  consec_stats[posix][0],
                  ','.join(map(str, consec_stats[posix][1])),
                  ','.join(map(str, consec_stats[posix][2]))) \
                      for posix in posix_times]
  with open(os.path.join(consec_dir, uname), 'w') as f:
    print "writing conseclines to", f.name
    f.write('\n'.join(lines_out))

"""
All usernames.
uname -> posix -> (insert counts, delete counts)
"""
def load_consecline_stats(output_dir, year_q):
  consec_dir = os.path.join(output_dir, year_q, 'diffs', 'stats_consec')
  consec_stats = {}
  for uname in os.listdir(consec_dir):
    with open(os.path.join(consec_dir, uname), 'r') as f:
      lines = f.readlines()
    consec_stats[uname] = {}
    for line in lines:
      line = line.split('\n')[0]
      commit, file_no, insert_str, delete_str = line.split('\t')
      posix = commit.split('_')[1]
      inserts = map(lambda x: int(x) if x is not '' else 0, insert_str.split(','))
      deletes = map(lambda x: int(x) if x is not '' else 0, delete_str.split(','))
      consec_stats[uname][int(posix)] = (inserts, deletes)
  return consec_stats
