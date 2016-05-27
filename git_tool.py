from git_helper import *
from general_stats import *

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
  for student in os.listdir(code_dir):
    student_dir = os.path.join(code_dir, student)
    all_commits = git_log(git_dir=student_dir,
            format_str="%h %ct",
            extra_str="--date=local").split('\n')
    if not all_commits[0]:
      print "expand: %s ignored, corrupt git" % (student)
      continue

    year_q = get_submit_time(student_dir) 
    year_target_dir = os.path.join(target_dir, year_q)

    add_uname_to_lookup(student, year_q, uname_lookup_by_year_q)
    student_id = uname_lookup_by_year_q[year_q][student]
    print student, student_id
    for commit in all_commits:
      git_checkout(commit, orig_dir=student_dir, target_dir=year_target_dir, prefix=student_id)
  export_uname_lookup_by_year_q(uname_lookup_by_year_q)
  
"""
Gets all lines changed during particular commit.
"""
def line_changes(code_dir, target_dir):
  print code_dir
  uname_lookup = load_uname_lookup_by_year_q()
  for student in os.listdir(code_dir):
    student = 'irvhsu_1'
    student_dir = os.path.join(code_dir, student)
    all_commits = git_log(git_dir=student_dir,
            format_str="%h %ct",
            extra_str="--date=local").split('\n')
    if not all_commits[0]:
      print "expand: %s ignored, corrupt git" % (student)
      continue

    year_q = get_submit_time(student_dir) 
    year_target_dir = os.path.join(target_dir, year_q)

    if student not in uname_lookup[year_q]: continue
    student_id = uname_lookup[year_q][student]
    print student, student_id
    print git_log(git_dir=student_dir,
                format_str="%h %ct",
                extra_str="--date=local --shortstat").split('\n')
    commit = None
    commit_time = None
    multi_file_commits = []
    for old_commit in all_commits: # commit list is in backwards order
      old_commit, old_commit_time = old_commit.split(' ')
      print "old %s(%s), new %s(%s)" % (old_commit, old_commit_time, commit, commit_time)
      if commit:
        diff_changes =  git_diff(old_commit, commit, git_dir=student_dir).split('\n')
        diff_changes = filter(lambda x: len(x) > 0, diff_changes)
        print '\n'.join(diff_changes)
        indices = range(len(diff_changes))
        # only get the insertions/deletions
        multiline_indices = filter(lambda i: diff_changes[i][:2] == '@@', indices)
        indices = filter(lambda i: diff_changes[i][0] in ['-', '+'], indices)
        # ---,+++ are filename lines
        indices = filter(lambda i: diff_changes[i][:3] not in ['---','+++'], indices)
        # every line has one extra space in it (blank, -, or +)
        deletions_i = filter(lambda i: diff_changes[i][0] == '-', indices)
        deletions = [diff_changes[i][1:] for i in deletions_i]
        insertions_i = filter(lambda i: diff_changes[i][0] == '+', indices)
        insertions = [diff_changes[i][1:] for i in insertions_i]
        if len(multiline_indices) > 2: multi_file_commits.append(commit)
        print "insertions", insertions_i
        print "Deletions", deletions_i
        for block_j in range(1,len(multiline_indices)):
          prev_block_i, curr_block_i = multiline_indices[block_j-1],multiline_indices[block_j]
          print "block (%d-%d)" % (prev_block_i, curr_block_i)
          deletions_block_i = filter(lambda i: i > prev_block_i and i < curr_block_i, deletions_i)
          insertions_block_i = filter(lambda i: i > prev_block_i and i < curr_block_i, insertions_i)
          print "insertions block", insertions_block_i
          print "deletions\n", '\n'.join([diff_changes[i][1:] for i in deletions_block_i])
          print "insertions\n", '\n'.join([diff_changes[i][1:] for i in insertions_block_i])
          
      commit = old_commit
      commit_time = old_commit_time
    print multi_file_commits
    break

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
  for student in os.listdir(code_dir):
    student_dir = os.path.join(code_dir, student)
    git_master(student_dir)

"""
Copy all final submissions to the directory specified.
"""
def copy_all_final(code_dir, final_submissions_dir):
  reset_all_to_master(code_dir)
  uname_lookup_by_year_q = load_uname_lookup_by_year_q()
  for student in os.listdir(code_dir):
    student_dir = os.path.join(code_dir, student)
    year_q = get_submit_time(student_dir) 
    if not year_q: continue
    add_uname_to_lookup(student, year_q, uname_lookup_by_year_q)
    student_id = uname_lookup_by_year_q[year_q][student]
    #target_final_dir = os.path.join(final_submissions_dir, "%s_%s" % (year_q, student))
    target_final_dir = os.path.join(final_submissions_dir, student_id)
    if not os.path.exists(target_final_dir):
      os.makedirs(target_final_dir)
    cp_cmd = "cp -r %s/* %s" % (student_dir, target_final_dir)
    call_cmd(cp_cmd)
    print "Copied student %s (%s) to final dir %s" % (student, year_q, target_final_dir)
  export_uname_lookup_by_year_q(uname_lookup_by_year_q)
