from git_helper import *
from general_stats import *
from multiprocessing import Pool as ThreadPool

"""
Goes through everything and changes all commits per
student into different snapshots of the code directory.
Each snapshot will be in a timestamp folder (also contains git hash).

Timestamp: UNIX timestamp.
  To convert to human dates: date -d @<dirname>
"""
def expand_all_commits(code_dir, target_dir):
  print code_dir
  uname_lookup_by_year_q = load_uname_lookup_by_year_q()
  latest_submissions = get_latest_submissions(code_dir)
  num_students = len(latest_submissions)

  def get_commit_args(args):
    i, student = args
    latest_submit = latest_submissions[student]
    student_dir = os.path.join(code_dir, latest_submit)
    year_q = get_submit_time(student_dir) 
    if not year_q: return (-1,'','',-1,'',-1)
    year_target_dir = os.path.join(target_dir, year_q)
    if year_q not in uname_lookup_by_year_q or \
          latest_submit not in uname_lookup_by_year_q[year_q]:
        add_uname_to_lookup(latest_submit, year_q, uname_lookup_by_year_q)
    student_id = uname_lookup_by_year_q[year_q][latest_submit]
    return i, student, student_dir, student_id, year_target_dir, num_students

  students = sorted(latest_submissions.keys())
  zipped_args = map(get_commit_args, enumerate(students))
  pool = ThreadPool(8)
  results = pool.map(thread_process_commit, zipped_args)
  pool.close()
  pool.join()
  export_uname_lookup_by_year_q(uname_lookup_by_year_q)

def thread_process_commit(args):
  i, student, student_dir, student_id, year_target_dir, num_students = args
  if i == -1: return
  all_commits = git_log(git_dir=student_dir,
          format_str="%h %ct",
          extra_str="--date=local").split('\n')
  if not all_commits[0]:
    print "expand: %s ignored, corrupt git" % (student)
    return

  num_commits = len(all_commits)
  for j, commit in enumerate(all_commits):
    print "student {}/{}: commit {}/{}".format(
        i, num_students, j, num_commits)
    git_checkout(commit, orig_dir=student_dir, target_dir=year_target_dir, prefix=student_id)


#   for i, student in enumerate(latest_submissions.keys()):
#     latest_submit = latest_submissions[student]
#     student_dir = os.path.join(code_dir, latest_submit)
#     all_commits = git_log(git_dir=student_dir,
#             format_str="%h %ct",
#             extra_str="--date=local").split('\n')
#     if not all_commits[0]:
#       print "expand: %s ignored, corrupt git" % (student)
#       continue
# 
#     year_q = get_submit_time(student_dir) 
#     year_target_dir = os.path.join(target_dir, year_q)
# 
#     if year_q not in uname_lookup_by_year_q or \
#           latest_submit not in uname_lookup_by_year_q[year_q]:
#         add_uname_to_lookup(latest_submit, year_q, uname_lookup_by_year_q)
#     student_id = uname_lookup_by_year_q[year_q][latest_submit]
#     num_commits = len(all_commits)
#     for j, commit in enumerate(all_commits):
#       print "student {}/{} {}: commit {}/{}".format(
#           i, num_students, student, j, num_commits)
#       git_checkout(commit, orig_dir=student_dir, target_dir=year_target_dir, prefix=student_id)
#   export_uname_lookup_by_year_q(uname_lookup_by_year_q)

def get_latest_submissions(code_dir):
  all_submissions = {}
  for submit in os.listdir(code_dir):
    student = submit.split('_')[0]
    if student not in all_submissions:
      all_submissions[student] = []
    all_submissions[student].append(submit)
  latest_submissions = dict([(student,
                          sorted(all_submissions[student])[-1]) \
                              for student in all_submissions])
  return latest_submissions
  
"""
Gets all lines changed during particular commit.

Writes all to directories.
"""
def line_changes(code_dir, target_dir):
  uname_lookup = load_uname_lookup_by_year_q()
  count = 0
  #test_commit = '2012010259_1350909164_2d1fc93'#'2012010311_1350615022_4a66c46'
  for student in os.listdir(code_dir):
    #student = 'vnangia_2'
    student_dir = os.path.join(code_dir, student)
    all_commits = git_log(git_dir=student_dir,
            format_str="%h %ct",
            extra_str="--date=local").split('\n')
    if not all_commits[0]:
      print "expand: %s ignored, corrupt git" % (student)
      continue

    year_q = get_submit_time(student_dir) 

    if student not in uname_lookup[year_q]: continue
    student_id = uname_lookup[year_q][student]
    # test
    #student_id = test_commit.split('_')[0]
    print count, student, student_id
    #  git_log(git_dir=student_dir,
    #        format_str="%h %ct",
    #        extra_str="--date=local --shortstat").split('\n')
    commit = None
    commit_time = None
    all_changes = {}
    for old_commit in all_commits: # commit list is in backwards order
      old_commit, old_commit_time = old_commit.split(' ')
      if commit:
        #print commit
        diff_changes =  git_diff(old_commit, commit, git_dir=student_dir).split('\n')
        #print '\n'.join(diff_changes)
        diff_changes = filter(lambda x: len(x) > 0, diff_changes)
        indices = range(len(diff_changes))
        chunk_indices = filter(lambda i: diff_changes[i][:2] == '@@', indices)
        # ---,+++ are filename lines
        insert_inds, delete_inds = [], []
        insert_line_no, delete_line_no = [], []
        #### get line numbers and lines
        for j in range(len(chunk_indices)):
          chunk_j = chunk_indices[j]
          _, old_st, new_st = diff_changes[chunk_j].split(' ')[:3]
          old_line_no = 1+int(old_st[1:].split(',')[0]) # -21,11 as example
          new_line_no = 1+int(new_st[1:].split(',')[0]) # +21,10 as example
          if j != len(chunk_indices) - 1:
            chunk_range = xrange(chunk_j+1,chunk_indices[j+1])
          else:
            chunk_range = xrange(chunk_j+1, len(indices))
          chunk_ins, chunk_del = [], []
          for i in chunk_range:
            # ---/+++ is diff header
            if len(diff_changes[i]) >= 3 and \
                  diff_changes[i][:3] in ['---','+++']: continue
            if diff_changes[i][0] is '+':
              chunk_ins.append((new_line_no, diff_changes[i][1:]))
              new_line_no += 1
            elif diff_changes[i][0] is '-':
              chunk_del.append((old_line_no, diff_changes[i][1:]))
              old_line_no += 1
            else:
              old_line_no += 1
              new_line_no += 1
              pass # do nothing if not insert/delete
          insert_inds.append(chunk_ins)
          delete_inds.append(chunk_del)
        #### organize consecutive lines
        insert_consec, delete_consec = [], []
        for j in range(len(chunk_indices)):
          insert_block = insert_inds[j]
          lines = []
          for i in range(len(insert_block)):
            line_no, line = insert_block[i]
            lines.append((line_no, line))
            if i == len(insert_block) - 1 or \
                line_no + 1 != insert_block[i+1][0]:
              insert_consec.append(zip(*lines))
              lines = []
          delete_block = delete_inds[j]
          lines = []
          for i in range(len(delete_block)):
            line_no, line = delete_block[i]
            lines.append((line_no, line))
            if i == len(delete_block) - 1 or \
                line_no + 1 != delete_block[i+1][0]:
              delete_consec.append(zip(*lines))
              lines = []
        # print "insert", insert_consec
        # print "delete", delete_consec

        # will each be visited once, so no need to check keys
        all_changes['%s_%s_%s' % (student_id, commit_time, commit)] = \
              (insert_consec, delete_consec)

      commit = old_commit
      commit_time = old_commit_time
    print "Diff lines processed for %s, begin writing..." % student_id
    save_line_changes(target_dir, year_q, student_id, all_changes)
    count += 1

def save_line_changes(target_dir, year_q, student_id, all_changes):
  diff_dir = os.path.join(target_dir, year_q, 'diffs')
  insert_dir = os.path.join(diff_dir, 'insert')
  delete_dir = os.path.join(diff_dir, 'delete')
  commits = all_changes.keys()
  commits.sort()
  for commit in commits:
    insertions, deletions = all_changes[commit]
    commit_insert_dir = os.path.join(insert_dir, commit)
    if insertions and not os.path.exists(commit_insert_dir):
      os.makedirs(commit_insert_dir)
    commit_delete_dir = os.path.join(delete_dir, commit)
    if deletions and not os.path.exists(commit_delete_dir):
      os.makedirs(commit_delete_dir)
    # insertions
    for line_nos, lines in insertions:
      fname = '%s_%s' % (line_nos[0], line_nos[-1])
      with open(os.path.join(commit_insert_dir, fname), 'w') as f:
        f.write('\n'.join(lines))
    # deletions
    for line_nos, lines in deletions:
      fname = '%s_%s' % (line_nos[0], line_nos[-1])
      with open(os.path.join(commit_delete_dir, fname), 'w') as f:
        f.write('\n'.join(lines))
  print "Wrote all diffs for %s" % student_id

"""
Removes commits from the expanded directory that do not
have the right files for MOSS processing.
"""
def check_all_commits(target_dir, year_q):
  year_dir = os.path.join(target_dir, year_q)
  for student_commit in os.listdir(os.path.join(target_dir, year_dir)):
    commit_path = os.path.join(target_dir, year_dir, student_commit)
    if not moss_okay(commit_path):
      shutil.rmtree(commit_path)
      print "No java files in %s. Removing." % (student_commit)
      continue
    

############## UTILITY FUNCTIONS #################
def reset_all_to_master(code_dir):
  tot_students = len(os.listdir(code_dir))
  num_students = 0
  for student in os.listdir(code_dir):
    num_students += 1
    print "%d/%d: Reset to master (%s)" % (num_students, tot_students, student)
    student_dir = os.path.join(code_dir, student)
    git_master(student_dir)

"""
Copy all final submissions to the directory specified.
"""
def copy_all_final(code_dir, final_submissions_dir):
  #reset_all_to_master(code_dir)
  uname_lookup_by_year_q = load_uname_lookup_by_year_q()
  for year_q in uname_lookup_by_year_q:
    print uname_lookup_by_year_q[year_q].keys()
  latest_submissions = get_latest_submissions(code_dir)
  num_students = len(latest_submissions)
  for i, student in enumerate(latest_submissions.keys()):
    latest_submit = latest_submissions[student]
    student_dir = os.path.join(code_dir, latest_submit)
    year_q = get_submit_time(student_dir) 
    if not year_q: continue
    if year_q not in uname_lookup_by_year_q or \
          latest_submit not in uname_lookup_by_year_q[year_q]:
        add_uname_to_lookup(latest_submit, year_q, uname_lookup_by_year_q)
    student_id = uname_lookup_by_year_q[year_q][latest_submit]
    #target_final_dir = os.path.join(final_submissions_dir, "%s_%s" % (year_q, student))
    target_final_dir = os.path.join(final_submissions_dir, year_q, student_id)
    if not os.path.exists(target_final_dir):
      os.makedirs(target_final_dir)
    cp_cmd = "cp -r %s/* %s" % (student_dir, target_final_dir)
    call_cmd(cp_cmd)
    print "Copied student %s (%s) to final dir %s" % (student, year_q, target_final_dir)
  for year_q in uname_lookup_by_year_q:
    print uname_lookup_by_year_q[year_q].keys()
  export_uname_lookup_by_year_q(uname_lookup_by_year_q)
