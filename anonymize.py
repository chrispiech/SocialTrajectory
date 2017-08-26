from helper import *
from git_helper import *
from time import strptime
from datetime import date
from moss_tool import *
from run import *
import re

"""
This file shouldn't really be needed anymore.

rawdata still has student names, but upon expanding the rawdata into readable
git directories, the expanded directory is anonymized. See git_tool.py for more
information.

For each new year, we should probably modifiy add_uname_to_lookup
code inside helper.py, but for now everything it's alright.
"""

def anonymize_all(moss_dir, output_dir, commit_dir, grades_and_lair_dir=None):
  uname_lookup = load_uname_to_id_lookup()
  # reload lookups for sorting...
  # print "Doing some reloading of usernames"
  # by_year = load_uname_lookup_by_year_q()
  # export_uname_lookup_by_year_q(by_year)

  for year_q_dirname in os.listdir(output_dir):
    try:
      year, q = year_q_dirname.split('_')
      int(year), int(q)
    except: continue
    print "Anonymizing top_sims for dir %s" % (year_q_dirname)
    #anonymize_top_sims(moss_dir, year_q_dirname, output_dir, uname_lookup)
    #anonymize_all_sims(os.path.join(output_dir, year_q_dirname, 'moss'), uname_lookup)
    #anonymize_stats(os.path.join(output_dir, year_q_dirname, 'stats'), uname_lookup)
def anonymize_grades_and_lair(grades_and_lair_dir):
  uname_lookup = load_uname_to_id_lookup()
  real_grades = os.path.join(grades_and_lair_dir, 'real_grades')
  anon_grades = os.path.join(grades_and_lair_dir, 'anon_grades')
  anonymize_grades(real_grades, anon_grades, uname_lookup)

  real_lair = os.path.join(grades_and_lair_dir, 'real_lair')
  anon_lair = os.path.join(grades_and_lair_dir, 'anon_lair')
  anonymize_lair(real_lair, anon_lair, uname_lookup)

  # new_unames = []
  # for year_q_dirname in os.listdir(commit_dir):
  #   flag = False
  #   try:
  #     year, q = year_q_dirname.split('_')
  #     int(year), int(q)
  #     print "Anonymizing csv for dir %s" % (year_q_dirname)
  #   except:
  #     # if year_q_dirname == "online":
  #     #   print "Anonymizing online submissions."
  #     #   flag = True
  #     if year_q_dirname == "final_submissions":
  #       print "Anonymizing final submissions."
  #       flag = True
  #     else:
  #       continue
  #   commit_new_unames = anonymize_commits(os.path.join(commit_dir, year_q_dirname), uname_lookup, flag)
  #   new_unames.append(((commit_dir, year_q_dirname), commit_new_unames))

  # for year_q_dirname in os.listdir(moss_dir):
  #   flag = False
  #   try:
  #     year, q = year_q_dirname.split('_')
  #     int(year), int(q)
  #     print "Anonymizing moss dir %s" % (year_q_dirname)
  #   except:
  #     continue
  #   moss_new_unames = anonymize_commits(os.path.join(moss_dir, year_q_dirname), uname_lookup, flag)
  #   new_unames.append(((moss_dir, year_q_dirname), commit_new_unames))

  # for year_q_dirname in os.listdir(moss_dir):
  #   try:
  #     year, q = year_q_dirname.split('_')
  #     int(year), int(q)
  #     print "Anonymizing moss dir %s" % (year_q_dirname)
  #   except:
  #     continue
  #   anonymize_indices(os.path.join(moss_dir, year_q_dirname), uname_lookup)

def anonymize_top_sims(moss_dir, year_q, output_dir, uname_lookup):
  #all_sims = load_all_sims_from_log(output_dir, year_q)
  top_sims = load_top_sims_from_log(output_dir, year_q)

  convert_top_sims_to_nums(output_dir, year_q, uname_lookup)

def anonymize_commits(commits_dir, uname_lookup, flag):
  # if flag on, directory is online or final submissions, so don't split for posix/commit string.
  new_unames = []
  for commit in os.listdir(commits_dir):
    orig_commit_path = os.path.join(commits_dir, commit)
    if not flag: # split for posix and commit
      if len(commit.split('_')) == 3: continue
      uname, submit_num, posix_time, commit_hash = commit.split('_')
      uname = "%s_%s" % (uname, submit_num)
      if uname not in uname_lookup:
        new_unames.append(uname)
        print "\tuname not found", uname
        continue
      uname_id = uname_lookup[uname]
      new_commit_str = '%s_%s_%s' % (uname_id, posix_time, commit_hash)
      print commit, new_commit_str
    else: # split for year and q
      if len(commit.split('_')) == 1: continue
      year, q, uname, submit_num = commit.split('_')
      uname = "%s_%s" % (uname, submit_num)
      if uname not in uname_lookup:
        new_unames.append(uname)
        print "\tuname not found", uname
        continue
      uname_id = uname_lookup[uname]
      new_commit_str = uname_id
      print commit, new_commit_str
    new_commit_path = os.path.join(commits_dir, new_commit_str)
    mv_cmd = "mv %s %s" % (orig_commit_path, new_commit_path)
    call_cmd(mv_cmd)
  print "unfound names", new_unames
  return new_unames

def anonymize_indices(moss_dir, uname_lookup):
  count = 10
  print moss_dir
  for commit in os.listdir(moss_dir):
    print commit
    index_path = os.path.join(moss_dir, commit, "index.html")
    anonymize_index(index_path, uname_lookup)

def anonymize_index(index_path, uname_lookup):
  new_index_path = "%s.%s" % (index_path, 'temp')
  with open(index_path, 'r') as index_f:
    with open(new_index_path, 'w') as new_index_f:
      for line in index_f.readlines():
        if '_' not in line and 'online' not in line:
          new_index_f.write(line)
        else:
          new_line_segs = re.split('(<|>| )', line)
          for i in range(len(new_line_segs)):
            seg = new_line_segs[i]
            if '_' not in seg and 'online' not in seg:
              continue
            new_seg = convert_seg(seg, uname_lookup)
            new_line_segs[i] = new_seg
          new_line = ''.join(new_line_segs)
          new_index_f.write(new_line)
  mv_cmd = "mv %s %s" % (new_index_path, index_path)
  #call_cmd(mv_cmd)

def anonymize_all_sims(all_sims_dir, uname_lookup):
  for commit_csv in os.listdir(all_sims_dir):
    commit, ext = commit_csv.split('.')
    if len(commit.split('_')) == 3: continue
    new_commit = convert_seg(commit, uname_lookup)
    new_commit_csv = '%s.%s' % (new_commit, ext)
    with open(os.path.join(all_sims_dir, commit_csv), 'r') as old_f:
      with open(os.path.join(all_sims_dir, new_commit_csv), 'w') as new_f:
        for line in old_f.readlines():
          line_segs = line.split(',')
          line_segs[0] = convert_seg(line_segs[0], uname_lookup)
          new_f.write(','.join(line_segs))
    print new_commit_csv

def anonymize_stats(stats_dir, uname_lookup):
  for stat_f in os.listdir(stats_dir):
    uname, ext = stat_f.split('.')
    new_stat_f = '%s.%s' % (uname_lookup[uname], ext)
    mv_cmd = "mv %s %s" % (os.path.join(stats_dir, stat_f),
                           os.path.join(stats_dir, new_stat_f))
    call_cmd(mv_cmd)

def convert_seg(seg, uname_lookup):
  if '/' not in seg: # regular convert
    if len(seg.split('_')) != 4: return seg
    uname, submit_num, posix_time, commit_hash = seg.split('_')
    uname = "%s_%s" % (uname, submit_num)
    uname_id = uname_lookup[uname]
    return '%s_%s_%s' % (uname_id, posix_time, commit_hash)
  # final submission or online, then convert
  seg_dir, seg_f = seg.split('/')
  if len(seg_f.split('_')) == 1 and seg_dir != 'online': return seg
  if 'online' in seg_f: return seg
  uname = get_uname_from_f(seg)
  uname_id = uname_lookup[uname]
  return '/'.join([seg_dir, uname_id])

def convert_top_sims_to_nums(output_dir, year_q, uname_lookup):
  top_sim_path = os.path.join(output_dir, "%s_top_sim.csv" % (year_q))
  print ">>>>>>>>%s" % top_sim_path
  new_top_sim_path = os.path.join(output_dir, "%s_top_sim_convert.csv" % (year_q))
  print "new top sim path: %s" % new_top_sim_path
  top_sims = {}
  with open(top_sim_path, 'r') as f:
    line = f.readline()
    uname = ''
    uname_id = ''
    while line:
      line = line.strip()
      if not line:
        uname = ''
      else:
        line_commas = line.split(',')
        if len(line_commas) == 1:
          if uname: print "Error: uname already assigned"
          uname = line
          uname_id = uname_lookup[uname]
          print "\t\t", uname, uname_id
          if uname_id not in top_sims:
            top_sims[uname_id] = {}
        else:
          # own_commit, other_f_path, other_f_html, tokens_matched,
          #       percent_self, percent_other
          posix_time, commit_hash = line_commas[0].split('_')[-2:]
          other_f_path, other_f_html, tokens_matched, \
            percent_self, percent_other = line_commas[1:]
          new_f_path = convert_f_path(other_f_path, uname_lookup)
          new_commit = '%s_%s_%s' % (uname_id, posix_time, commit_hash)
          top_sims[uname_id][new_commit] = \
            (new_f_path, other_f_html, int(tokens_matched),
                      float(percent_self), float(percent_other))
      line = f.readline()
  write_top_sims_to_file(top_sims, new_top_sim_path)

def convert_f_path(other_f, uname_lookup):
  other_uname = get_uname_from_f(other_f)
  if other_uname not in uname_lookup:
    print "error:", other_uname, "not found in lookup"
  other_id = uname_lookup[other_uname]
  if 'online' in other_id:
    new_other_f = os.path.join('online',other_id)
  else:
    new_other_f = os.path.join('final_submissions',other_id)
  return new_other_f

def anonymize_grades(real_dir, anon_dir, uname_lookup_orig):
  # since the uname_lookup table is tagged with the user's submit
  # count, we make a uname_lookup solely based on user for the grades.

  # SUNet ID, midterm, final
  uname_lookup_by_year_q = load_uname_lookup_by_year_q()
  for grade_fname in os.listdir(real_dir):
    if len(grade_fname.split('-extended')) != 2: continue
    year = grade_fname.split('-extended')[0][-4:]
    #year = grade_fname.split('.')[0][-4:]
    year_q = '%s_1' % (year)

    uname_lookup_orig = uname_lookup_by_year_q[year_q]
    uname_lookup = {}
    for student_commit in uname_lookup_orig:
      student = student_commit.split('_')[0]
      uname_lookup[student] = uname_lookup_orig[student_commit]
    num_orig_students = len(uname_lookup.keys())
    print "num orig students", num_orig_students

    anon_grades = {}
    tot_students = 0
    with open(os.path.join(real_dir, grade_fname), 'r') as real_f:
      print real_f.name
      line = real_f.readline() # skip header
      line = real_f.readline()
      while line:
        tot_students += 1
        line = line.strip()
        student = line.split(',')[0]
        all_grades = line.split(',')[1:]
        line = real_f.readline() # read next line

        if student not in uname_lookup:
          #print "%s: student %s not available" % (year_q, student)
          add_uname_to_lookup(student, year_q, uname_lookup_by_year_q)
          continue

        student_id = uname_lookup[student]
        if student_id[:4] != year_q[:4]: continue # student retaking
        anon_grades[student_id] = all_grades
    print "%s: %s/%s students used" % (year_q, len(anon_grades), tot_students)

    with open(os.path.join(anon_dir, '%s.csv' % year_q), 'w') as anon_f:
      student_ids = anon_grades.keys()
      student_ids.sort()
      anon_f.write('\n'.join(['%s,%s' % (student_id,
                                ','.join(anon_grades[student_id])) \
                                    for student_id in student_ids]))
      print anon_f.name
  export_uname_lookup_by_year_q(uname_lookup_by_year_q)

def anonymize_lair(real_dir, anon_dir, uname_lookup_orig):
  import csv
  # since the uname_lookup table is tagged with the user's submit
  # count, we make a uname_lookup solely based on user for the grades.
  uname_lookup = {}
  for student_commit in uname_lookup_orig:
    student = student_commit.split('_')[0]
    uname_lookup[student] = uname_lookup_orig[student_commit]

  lair_dict = {}
  sunetid_ind, ta_ind, class_ind, year_q_ind = 0, 1, 2, 3
  enter_ind, help_ind, end_ind = 4, 5, 6
  problem_ind, solution_ind = 7, 8
  ta_lookup = {} # ta_sunetid -> value
  ta_lookup_by_year = {}
  tots_lookup = {}
  count = 0
  student_list = {}
  with open(os.path.join(real_dir, 'AnonRequests.csv'), 'r') as csvfile:
    reader = csv.reader(csvfile)
    # SUNet ID, TA name, date entered, helped, finished
    # can sometimes have "null" in the start help time column, so ignore
    for row in reader:
      if count % 1000 == 0:
        #print count
        pass
      count += 1
      if len(row) < 5: continue
      uname, ta_uname, classname, year_q_str, start_help, _, end_help, prob, sol = \
          row

      year_int, q_int = map(int, year_q_str.split('.'))
      q_int = (q_int + 1) # fall: 4 -> 5 -> 1 (else: 2 -> 3, etc.)
      if q_int == 5: q_int = 1
      if q_int == 4: q_int = 4
      year_q = '%s_%s_%s' % (classname, year_int, q_int)
      if year_q not in tots_lookup:
        tots_lookup[year_q] = {}
      if uname not in tots_lookup[year_q]:
        tots_lookup[year_q][uname] = 0
      tots_lookup[year_q][uname] += 1

      # TA things
      if year_q not in ta_lookup_by_year:
        ta_lookup_by_year[year_q] = {}

      if ta_uname not in ta_lookup:
        ta_lookup[ta_uname] = '%s%02d%02d' % (year_int, q_int,
            len(ta_lookup_by_year[year_q]))
      ta_id = ta_lookup[ta_uname]
      if ta_id not in ta_lookup_by_year[year_q]:
        ta_lookup_by_year[year_q][ta_id] = 0
      ta_lookup_by_year[year_q][ta_id] += 1 # number of times helped a student
      if classname.upper() != 'CS106A': continue
      year_tup = '%s_%s' % (year_int, q_int)
      if year_tup not in student_list:
        student_list[year_tup] = set()
      student_list[year_tup].add(uname)
      if uname not in uname_lookup: continue
      student_id = uname_lookup[uname]
      if '%s0%s' % (year_int, q_int) != student_id[:6]:
        print "%s is retaking in %s" % (student_id, year_q)
        continue

      if year_q not in lair_dict:
        lair_dict[year_q] = {}
      if student_id not in lair_dict[year_q]:
        lair_dict[year_q][student_id] = []
      # remove all commas from prob/sol strings
      lair_dict[year_q][student_id].append(\
          (start_help, end_help, ta_id, ''.join(prob.split(',')), ''.join(sol.split(','))))

  all_year_qs = tots_lookup.keys()
  all_year_qs.sort()
  for year_q in ta_lookup_by_year:
    tas = list(ta_lookup_by_year[year_q].keys())
    tas.sort()
    for ta in tas:
      #print year_q, ta, ta_lookup_by_year[year_q][ta]
      pass
    #print '%s\n\t%s' % (year_q, '\n\t'.join(tas))
  tas = ta_lookup.keys()
  tas.sort()
  for ta in tas:
    #print ta, ta_lookup[ta]
    pass
  # confirm number saved
  for year_q in all_year_qs:
    lair_unames = 0
    tot_unames = len(tots_lookup[year_q].keys())
    if year_q in lair_dict:
      lair_unames = len(lair_dict[year_q].keys())
    print "%s: saving %s/%s student records" % (year_q, lair_unames, tot_unames)

  # construct TA dictionary
  ta_info = {}
  for ta_uname, ta_id in ta_lookup.iteritems():
    ta_years = [(year_q,ta_lookup_by_year[year_q][ta_id]) for year_q in ta_lookup_by_year if ta_id in ta_lookup_by_year[year_q]]
    student_id = ''
    if ta_uname in uname_lookup:
      student_id = uname_lookup[ta_uname]

    student_years = [(year_q, tots_lookup[year_q][ta_uname]) for year_q in tots_lookup if ta_uname in tots_lookup[year_q]]

    ta_info[ta_id] = (student_id, '\t'.join(map(str,ta_years)), '\t'.join(map(str,student_years)), ta_uname)
  ta_ids = ta_info.keys()
  ta_ids.sort()
  with open(os.path.join(anon_dir, '%s.csv' % 'ta_info'), 'w') as anon_ta_f:
    ta_ids = ta_info.keys()
    ta_ids.sort()
    anon_ta_f.write('\n'.join(['%s,%s' % (ta_id,
        ','.join(ta_info[ta_id][:3])) for ta_id in ta_ids]))
    print anon_ta_f.name

  for year_q in student_list:
    print "year_q %s: %s students" % (year_q, len(student_list[year_q]))

  for year_q in lair_dict:
    with open(os.path.join(anon_dir, '%s.csv' % year_q), 'w') as anon_f:
      student_ids = lair_dict[year_q].keys()
      student_ids.sort()
      print "num student ids in %s" % year_q, len(student_ids)
      for student_id in student_ids:
        lair_entries = lair_dict[year_q][student_id]
        # for lair_entry in lair_entries:
        #   print student_id, ','.join(map(str, lair_entry))
        # print '\n'.join(['%s,%s' % (student_id,
        #                               ','.join(map(str,lair_entry))) \
        #                   for lair_entry in lair_entries])
        anon_f.write('\n'.join(['%s,%s' % (student_id,
                                      ','.join(map(str,lair_entry))) \
                          for lair_entry in lair_entries]))
        anon_f.write('\n')
      print anon_f.name

