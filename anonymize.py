from helper import *
from git_helper import *
from time import strptime
from datetime import date
from lxml import etree, html
from moss_tool import *
from run import *
import re

def anonymize_all(moss_dir, output_dir, commit_dir):
  uname_lookup = load_uname_to_id_lookup()

  for year_q_dirname in os.listdir(output_dir):
    try:
      year, q = year_q_dirname.split('_')
      int(year), int(q)
    except: continue
    print "Anonymizing top_sims for dir %s" % (year_q_dirname)
    #anonymize_top_sims(moss_dir, year_q_dirname, output_dir, uname_lookup)
    #anonymize_all_sims(os.path.join(output_dir, year_q_dirname, 'moss'), uname_lookup)
    anonymize_stats(os.path.join(output_dir, year_q_dirname, 'stats'), uname_lookup)

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
