from helper import *
from git_helper import *
from time import strptime
from datetime import date

output_tokens_dir = "tokens"
output_commitdoc_dirname = "percommitdoc"
output_user_dirname = "peruser"
output_thresh_dir = "ignore"
output_count_dir = "count"
doc_suffix = "doc"
token_suffix = "token"
output_final_dir = "final_submissions"
preprocess_thresh = 50

"""
commitdoc->token count
"""
def load_commitdoc_counts(output_dir, year_q):
  commitdoc_counts = {}
  with open(os.path.join(output_dir, year_q, output_count_dir, output_commitdoc_dirname), 'r') as f:
    line = f.readline()
    while line:
      commitdoc, count = (line.strip()).split('\t')
      commitdoc_counts[commitdoc] = int(count)
      line = f.readline()
  return commitdoc_counts

def load_user_counts(output_dir, year_q):
  user_counts = {}
  with open(os.path.join(output_dir, year_q, output_count_dir, output_user_dirname), 'r') as f:
    line = f.readline()
    while line:
      user, count = (line.strip()).split('\t')
      user_counts[user] = int(count)
      line = f.readline()
  return user_counts

"""
imports commitdoc_counts and creates peruser file in counts that sums over
all commits per user
"""
def make_user_counts(output_dir, year_q):
  commitdoc_counts = load_commitdoc_counts(output_dir, year_q)
  user_counts = {}
  for commitdoc in commitdoc_counts:
    user = commitdoc.split('_')[0]
    if user not in user_counts:
      user_counts[user] = 0
    user_counts[user] += commitdoc_counts[commitdoc]
  with open(os.path.join(output_dir, year_q, output_count_dir, output_user_dirname), 'w') as f:
    users = user_counts.keys()
    users.sort()
    f.write('\n'.join(['%s\t%s' % (user, user_counts[user]) for user in users]))

def make_token_counts(output_dir, year_q, use_commitdoc=False):
  token_granularity = output_commitdoc_dirname
  if not use_commitdoc: token_granularity = output_user_dirname
  else: return # commitdoc version not implemented yet
  count_dir = os.path.join(output_dir, year_q, output_count_dir)
  user_to_token = {}
  with open(os.path.join(count_dir, '%s_doc' % token_granularity), 'r') as f:
    for line in f.readlines():
      token, count = line.strip().split('\t')
      user_commitdoc = load_token_to_user(output_dir, year_q,
              token, use_commitdoc=use_commitdoc)
      for user in user_commitdoc:
        if user not in user_to_token:
          user_to_token[user] = set()
        user_to_token[user].add(token)
  with open(os.path.join(count_dir, 'token_%s' % token_granularity), 'w') as f:
    users = user_to_token.keys()
    users.sort()
    f.write('\n'.join(['%s\t%s' % (user, '\t'.join(list(user_to_token[user]))) \
              for user in users]))

"""
for a given token,
user->commitdoc
"""
def load_token_to_user(output_dir, year_q, token, use_commitdoc=False):
  token_granularity = output_commitdoc_dirname # smaller granularity
  if not use_commitdoc:
    token_granularity = output_user_dirname
  token_path = os.path.join(output_dir, year_q, output_tokens_dir,
                          token_granularity, token)
  user_commitdoc = {}
  with open(token_path, 'r') as f:
    line = f.readline()
    while line:
      commitdoc = line.strip()
      user = commitdoc.split('_')[0]
      if user not in user_commitdoc:
        user_commitdoc[user] = set()
      user_commitdoc[user].add(commitdoc)
      line = f.readline()
  return user_commitdoc

def remove_empty_files(output_dir, year_q):
  tokens_dir = os.path.join(output_dir, year_q, output_tokens_dir)
  for token_type in os.listdir(os.path.join(output_dir, year_q, output_tokens_dir)):
    if token_type == output_commitdoc_dirname: continue
    token_type_dir = os.path.join(output_dir, year_q, output_tokens_dir, token_type)
    empties = 0
    count = 0
    for commit in os.listdir(token_type_dir):
      count += 1
      if count % 5000 == 0: print "processed: %d, empties: %d" % (count, empties)
      fpath = os.path.join(token_type_dir, commit)
      remove_dir = False
      with open(fpath, 'r') as f:
        remove_dir = (len(f.readlines()) == 0)
      if remove_dir:
        os.remove(fpath)
        empties += 1
    print "Removed %d empty files for token type %s" % (empties, token_type)

def write_token_counts(output_dir, year_q, separate_token_types=False, use_commitdoc=False):
  token_granularity = output_commitdoc_dirname
  if not use_commitdoc:
    token_granularity = output_user_dirname
  tokens_dir = os.path.join(output_dir, year_q, output_tokens_dir)
  count_dir = os.path.join(output_dir, year_q, output_count_dir)
  if not os.path.exists(count_dir):
    os.makedirs(count_dir)
  
  if not use_commitdoc:
    convert_commitdoc_token_counts(output_dir, year_q)

  all_tokens = {}
  all_tokens_docs = {}
  unique_docs = set()
  for token_type in os.listdir(tokens_dir):
    if token_type == output_commitdoc_dirname: continue
    if token_type == output_user_dirname: continue
    print "loading tokens for token_type", token_type
    token_type_tokens, token_type_docs, doc_set, unique_docs = load_tokens_from_token_type(
        os.path.join(tokens_dir, token_type), doc_set=unique_docs, use_commitdoc=use_commitdoc)
    print "%s num tokens: %d" % (token_type, len(token_type_docs))
    if separate_token_types:
      docs_tuples = [(key, len(token_type_docs[key])) for key in token_type_docs]
      docs_tuples.sort()
      token_tuples = [(key, token_type_tokens[key]) for key in token_type_tokens]
      token_tuples.sort()
      with open(os.path.join(count_dir, '%s_%s' % (token_type, doc_suffix)), 'w') as f:
        f.write('\n'.join(['%s\t%s' % (x, y) for x, y in docs_tuples]))
      with open(os.path.join(count_dir, '%s_%s' % (token_type, token_suffix)), 'w') as f:
        f.write('\n'.join(['%s\t%s' % (x, y) for x, y in token_tuples]))
      with open(os.path.join(count_dir, '%s_unique' % token_type), 'w') as f:
        doc_list = list(doc_set)
        doc_list.sort()
        f.write('\n'.join(doc_list))
    else:
      split_and_merge_tokens(token_type_tokens, all_tokens)
      print "current token count (all_tokens):", len(all_tokens)
      split_and_merge_tokens(token_type_docs, all_tokens_docs, is_set=True)
      print "current token count (all_tokens_docs):", len(all_tokens_docs)
  if not separate_token_types:
    docs_tuples = [(key, len(all_tokens_docs[key])) for key in all_tokens_docs]
    docs_tuples.sort()
    token_tuples = [(key, all_tokens[key]) for key in all_tokens]
    token_tuples.sort()
    with open(os.path.join(count_dir, '%s_%s' % (token_granularity, doc_suffix)), 'w') as f:
      f.write('\n'.join(['%s\t%s' % (x, y) for x, y in docs_tuples]))
    with open(os.path.join(count_dir, '%s_%s' % (token_granularity, token_suffix)), 'w') as f:
      f.write('\n'.join(['%s\t%s' % (x, y) for x, y in token_tuples]))
    with open(os.path.join(count_dir, '%s_unique' % (token_granularity)), 'w') as f:
      print "len unique docs", len(unique_docs)
      doc_list = list(unique_docs)
      doc_list.sort()
      print f.name
      f.write('\n'.join(doc_list))
    
  print "total unique docs above threshold", len(unique_docs)
  unique_docs_sorted = list(unique_docs)
  unique_docs_sorted.sort()
  with open(os.path.join(count_dir, 'unique_docs'), 'w') as f:
    f.write('\n'.join(unique_docs_sorted))

def convert_commitdoc_token_counts(output_dir, year_q):
  token_granularity = output_user_dirname


"""
token->[commit1,commit2,commit3]
commit->token_count
"""
def convert_tokens_by_user(output_dir, year_q, token_type,
          token_dict_user=None, n_docs=None, use_commitdoc=False):
  token_dir = os.path.join(output_dir, year_q, output_tokens_dir, token_type)
  if not token_dict_user: token_dict_user = {}
  if not n_docs: n_docs = {}
  count = 0
  for commit in os.listdir(token_dir):
    count += 1
    if count % 5000 == 0: print count
    user, posix_time, commit_hash = commit.split('_')
    # if user not in token_dict_user:
    #   token_dict_user[user] = {}
    with open(os.path.join(token_dir, commit), 'r') as f:
      line = f.readline()
      while line:
        # process two lines at a time
        tokens = convert_punct_token(line)
        appearances = f.readline().strip().split('\t')
        line = f.readline()
        for token in tokens:
          if token not in token_dict_user: token_dict_user[token] = set()
          if use_commitdoc:
            doc_appearances = ['%s_%s' % (commit, appearance.split('_')[0]) for appearance in appearances]
          else:
            doc_appearances = [user for appearance in appearances]
          for doc in doc_appearances:
            if doc not in n_docs: n_docs[doc] = 0
            token_dict_user[token].add(doc)
            n_docs[doc] += 1

  return token_dict_user, n_docs

def convert_punct_token(line):
  tokens = re.split('\W+', line)
  tokens = [token.lower() for token in tokens if token]
  return tokens

def use_user(output_dir, year_q):
    print "write user by token counts"
    write_user_by_token_counts(output_dir, year_q, use_commitdoc=False)
    print "\nwrite token counts"
    #write_sum_files(output_dir, year_q, use_commitdoc=False)
    write_token_counts(output_dir, year_q, use_commitdoc=False)
    print "\nmake user counts"
    make_user_counts(output_dir, year_q)

def use_commitdoc(output_dir, year_q):
    write_user_by_token_counts(output_dir, year_q, use_commitdoc=True)
    write_token_counts(output_dir, year_q, use_commitdoc=True)

def write_sum_files(output_dir, year_q, use_commitdoc=False):
  token_granularity = output_commitdoc_dirname
  if not use_commitdoc:
    token_granularity = output_user_dirname
  tokens_dir = os.path.join(output_dir, year_q, output_tokens_dir)
  count_dir = os.path.join(output_dir, year_q, output_count_dir)

  if use_commitdoc:
    print "sum files (\"all\") not implemented yet for commit doc; use write_token_counts instead"
    return
  for token in all_token_to_user:
    all_users = list(all_token_to_user[token])
    all_users.sort()
    with open(os.path.join(tokens_dir, token_granularity, token), 'w') as f:
      f.write('\n'.join(all_users))
  

def write_user_by_token_counts(output_dir, year_q, separate_token_types=False,
        use_commitdoc=False):
  token_granularity = output_commitdoc_dirname
  if not use_commitdoc:
    token_granularity = output_user_dirname
  tokens_dir = os.path.join(output_dir, year_q, output_tokens_dir)
  count_dir = os.path.join(output_dir, year_q, output_count_dir)
  if not os.path.exists(count_dir):
    os.makedirs(count_dir)
  if not os.path.exists(os.path.join(tokens_dir, token_granularity)):
    os.makedirs(os.path.join(tokens_dir, token_granularity))

  all_token_to_user = {}
  all_token_counts = {}
  unique_docs = set()
  for token_type in os.listdir(tokens_dir):
    if token_type == output_commitdoc_dirname: continue
    if token_type == output_user_dirname: continue
    print "loading tokens for token_type", token_type
    all_token_to_user, all_token_counts = convert_tokens_by_user(output_dir, year_q, token_type, all_token_to_user, all_token_counts, use_commitdoc=use_commitdoc)
    print "current key count (token->user): %d, doc count %d" % (len(all_token_to_user), len(all_token_counts))
  
  print "Writing all tokens->user maps"
  for token in all_token_to_user:
    all_users = list(all_token_to_user[token])
    all_users.sort()
    with open(os.path.join(tokens_dir, token_granularity, token), 'w') as f:
      f.write('\n'.join(all_users))

  all_docs = all_token_counts.keys()
  with open(os.path.join(count_dir, token_granularity), 'w') as f:
    print "Writing all doc counts to %s" % f.name
    all_docs.sort()
    f.write('\n'.join(['%s\t%s' % (doc, all_token_counts[doc]) for doc in all_docs]))

"""
Splits up tokens in token_type_dict and remove all punctuation.
Merges the dictionary of tokens from a token type to
the dictionary of all tokens.
"""
def split_and_merge_tokens(token_type_dict, all_token_dict, is_set=False):
  for punct_token in token_type_dict:
    token_val = token_type_dict[punct_token]
    tokens = convert_punct_token(punct_token)
    for token in tokens:
      if token not in all_token_dict:
        if is_set:
          all_token_dict[token] = set()
        else:
          all_token_dict[token] = 0
      if is_set:
        all_token_dict[token] = all_token_dict[token].union(token_val)
      else:
        all_token_dict[token] += token_val

def write_unique_docs_no_thresh(commit_dir, output_dir, year_q):
  count_dir = os.path.join(output_dir, year_q, output_count_dir)
  if not os.path.exists(count_dir):
    os.makedirs(count_dir)
  unique_docs = set()
  count = 0
  for commit in os.listdir(os.path.join(commit_dir, year_q)):
    student_commit_dir = os.path.join(commit_dir, year_q, commit)
    for filename in os.listdir(student_commit_dir):
      if filename.split('.')[-1] != 'java': continue
      unique_docs.add('%s_%s' % (commit, filename))
  unique_docs_sorted = list(unique_docs)
  unique_docs_sorted.sort()
  with open(os.path.join(count_dir, 'unique_docs_no_thresh'), 'w') as f:
    f.write('\n'.join(unique_docs_sorted))
  

# only call this when you need to reload the threshold file.
def token_preprocess(commit_dir, output_dir, year_q):
  year, q = [int(x) for x in year_q.split('_')]
  yearstr = '%s%02d' % (year, q)
  # get tokens from each of the final submission for preprocessing.
  token_process(commit_dir, output_dir, output_final_dir, use_only=yearstr)
  final_tokens, final_doc_tokens = load_final_tokens(output_dir)
  write_thresh_files(output_dir, final_doc_tokens)

def load_final_tokens(output_dir):
  final_tokens_dir = os.path.join(output_dir, output_final_dir, output_tokens_dir)
  final_tokens = {}
  final_doc_tokens = {}
  for token_type in os.listdir(final_tokens_dir):
    if token_type == output_commitdoc_dirname: continue
    if token_type == output_user_dirname: continue
    final_tokens[token_type], final_doc_tokens[token_type], _, _ = \
        load_tokens_from_token_type(os.path.join(final_tokens_dir, token_type))
  return final_tokens, final_doc_tokens

# doc dict: count of documents that a token appears in.
# token dict: number of times a token appears in all documents.
# doc set: unique set of document names with multiple token types
# token type doc set: subset of doc set
def load_tokens_from_token_type(output_token_type_dir,
        doc_dict=None, doc_set=None, use_commitdoc=False):
  if not doc_dict: doc_dict = {}
  if not doc_set: doc_set = set()
  token_dict = {}
  count = 0
  
  token_type_doc_set = set()
  user_counts = {}
  doc_user_dict = {}
  token_type_doc_user_set = set()
  for commit in os.listdir(output_token_type_dir):
    user = commit.split('_')[0]
    if user not in user_counts:
      user_counts[user] = 0
    count += 1
    if count % 5000 == 0: print "loaded %d commits" % count
    with open(os.path.join(output_token_type_dir, commit), 'r') as f:
      line = f.readline()
      while line:
        # process two lines at a time
        token = line.strip()
        if not token: line = f.readline(); continue # could be blank
        if token not in doc_dict: doc_dict[token] = set()
        if token not in token_dict: token_dict[token] = 0
        appearances = f.readline().strip().split('\t')
        doc_appearances = ['%s_%s' % (commit, appearance.split('_')[0]) for appearance in appearances]
        token_dict[token] += len(appearances)
        if use_commitdoc:
          unique_doc_count = len(set(doc_appearances))
          doc_dict[token].add(set(doc_appearances))
          for doc in set(doc_appearances):
            doc_set.add(doc)
            token_type_doc_set.add(doc)
        else:
          if token not in doc_user_dict:
            doc_user_dict[token] = set()
          doc_user_dict[token].add(user)
          token_type_doc_user_set.add(user)
        
        line = f.readline()

  if not use_commitdoc:
    doc_set = doc_set.union(token_type_doc_user_set)
    doc_dict = doc_user_dict
    token_type_doc_set = token_type_doc_user_set
  print output_token_type_dir, "docs", len(token_type_doc_set), "tot docs", len(doc_set)
  return token_dict, doc_dict, token_type_doc_set, doc_set

def load_thresh_files(output_dir):
  ignore_tokens = {}
  thresh_dir = os.path.join(output_dir, output_final_dir, output_thresh_dir)
  for token_type in os.listdir(thresh_dir):
    if token_type == output_commitdoc_dirname: continue
    if token_type == output_user_dirname: continue
    thresh_token_type_path = os.path.join(thresh_dir, token_type)
    with open(thresh_token_type_path, 'r') as f:
      ignore_tokens[token_type] = set([x.strip() for x in f.readlines()])
    print "ignore", token_type, ignore_tokens[token_type]
  return ignore_tokens

"""
*** the tokens to IGNORE ***
"""
def write_thresh_files(output_dir, final_doc_tokens):
  thresh_dir = os.path.join(output_dir, output_final_dir, output_thresh_dir)
  if not os.path.exists(thresh_dir):
    os.makedirs(thresh_dir)
  for token_type in final_doc_tokens:
    if token_type == output_commitdoc_dirname: continue
    if token_type == output_user_dirname: continue
    fname = "%s" % (token_type)
    above_thresh_tokens = filter(
      lambda token: final_doc_tokens[token_type][token] > preprocess_thresh,
      final_doc_tokens[token_type].keys())
    above_thresh_tokens.sort()

    # IGNORE the tokens written to this file
    thresh_token_type_path = os.path.join(thresh_dir, fname)
    with open(thresh_token_type_path, 'w') as f:
      f.write('\n'.join(above_thresh_tokens))
    print "thresholds written to", thresh_token_type_path

"""
The key function that processes all commits in a particular directory
and tokenizes them, saving the token outputs into a commit directory.

The token files will NOT contain the ones in ignore_tokens.
"""
def token_process(commit_dir, output_dir, year_q, use_only=''):
  if year_q == output_final_dir: ignore_tokens = {}
  else: ignore_tokens = load_thresh_files(output_dir)

  commit_year_dir = os.path.join(commit_dir, year_q)
  token_year_dir = os.path.join(output_dir, year_q, output_tokens_dir)
  if not os.path.exists(token_year_dir):
    os.makedirs(token_year_dir)
  count = 0
  for commit in os.listdir(commit_year_dir):
    if commit[:len(use_only)] != use_only:
      continue
    print count, ": Tokenizing", commit
    make_tokens(commit_year_dir, token_year_dir, commit, ignore_tokens)
    count += 1
    #if count == 20: break

"""
Tokenizes a given commit. Called by token_process.
Writes the tokens as well.
"""
def make_tokens(commit_dir, output_dir, commit, ignore_tokens=None):
  all_tokens = {}
  all_lines = ''
  student_commit_dir = os.path.join(commit_dir, commit)
  for filename in os.listdir(student_commit_dir):
    if filename.split('.')[-1] != 'java': continue
    f_path = os.path.join(student_commit_dir, filename)
    print f_path
    lines = ''
    with open(f_path, 'r') as f:
      lines = ''.join(f.readlines())
      try:
        tokens = list(javalang.tokenizer.tokenize(lines))
      except:
         print "\tIgnoring; error in parser"
         continue
      all_tokens = make_token_dict(tokens, filename,
                      ignore_tokens=ignore_tokens, token_dict=all_tokens)
  for token_type in all_tokens:
    if token_type == output_commitdoc_dirname: continue
    if token_type == output_user_dirname: continue
    token_type_path = os.path.join(output_dir, token_type)
    if not os.path.exists(token_type_path):
      os.makedirs(token_type_path)
    f_path = os.path.join(token_type_path, commit)
    with open(f_path, 'w') as f:
      all_tokens_str = token_dict_to_str(all_tokens, token_type)
      f.write(all_tokens_str)

def get_type(token):
  type_str = str(type(token))
  type_str = type_str.strip(">'")
  type_str = type_str.split('.')[-1]
  return type_str

def token_dict_to_str(token_dict, token_type):
  type_dict = token_dict[token_type]
  keys = type_dict.keys()
  keys.sort()
  dict_str = []
  for key in keys:
    dict_str.append(key)
    dict_str.append('\t'.join([value for value in type_dict[key]]))
  return '\n'.join(dict_str)

def make_token_dict(token_list, fname, ignore_tokens=None, token_dict=None):
  if not token_dict:
    token_dict = {}
  if not ignore_tokens: ignore_tokens = {}
  for i in range(len(token_list)):
    token = token_list[i]
    token_type = get_type(token)
    if token_type not in token_dict:
      token_dict[token_type] = {}
    token_value = (token.value).strip().encode('ascii', 'ignore').decode('ascii')
    if not token_value: continue # ignore whitespace characters
    if token_type in ignore_tokens and token_value in ignore_tokens[token_type]:
      continue
    if token_value not in token_dict[token_type]:
      token_dict[token_type][token_value] = []
    token_dict[token_type][token_value].append('%s_%s' % (fname, str(token.position)))
  return token_dict
