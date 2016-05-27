from helper import *
from git_helper import *
from time import strptime
from datetime import date
from tokenize_tool import *
from scipy.sparse import csr_matrix

output_tokens_dir = "tokens"
output_commitdoc_dirname = "percommitdoc"
output_user_dirname = "peruser"
output_thresh_dir = "ignore"
output_count_dir = "count"
doc_suffix = "doc"
token_suffix = "token"
output_final_dir = "final_submissions"
preprocess_thresh = 50
output_probs_dir = "probs"
output_graph_dir = "graphs"


###############################################################################
# Token probability parsing heuristics #####
###############################################################################
max_users_per_token = 30 # use -1 if want all tokens used for probs

"""
max(keys, key=sort_function)
"""
def sort_function(user_i_dict):
  def helper(x):
    log_prob, token_count, token = user_i_dict[x]
    log_prob, token_count = float(log_prob), int(token_count)
    return -log_prob # sort by min probability
    return token_count # sort by token count
  return helper
###############################################################################

def parse_token_probs_pairs(output_dir, year_q):
  prob_dir = os.path.join(output_dir, year_q, output_probs_dir, output_commitdoc_dirname)
  user_is = os.listdir(prob_dir)
  user_is.sort()
  max_docs = []
  for user_i in user_is:
    user_j, P_dict = load_token_probs_pair(output_dir, year_q, user_i)
    (doc_i, doc_j), (log_prob, token_count, token) = argmax_pairwise(P_dict)
    doc_i = '%s/%s' % ('_'.join(doc_i.split('_')[:-1]), doc_i.split('_')[-1])
    doc_j = '%s/%s' % ('_'.join(doc_j.split('_')[:-1]), doc_j.split('_')[-1])
    max_docs.append((doc_i, doc_j, log_prob, token_count, token))
    #graph_token_probs_pair(output_dir, year_q, user_i, user_j, P_dict)
  with open(os.path.join(output_dir, year_q, output_probs_dir, 'max_pairs_commitdocs'), 'w') as f:
    f.write('\n'.join(['%s\t%s\t%s\t%s\t%s' % max_doc for max_doc in max_docs]))

def token_probs_pairs(output_dir, year_q):
  pairs = parse_token_probs(output_dir, year_q)
  pair_count = 0
  for user_i, user_j in pairs:
    pair_count += 1
    print "pair %d : (%s, %s)" % (pair_count, user_i, user_j)
    token_probs(output_dir, year_q, use_commitdoc=True, user_pairs=[(user_i, user_j)])

def get_doc_lookup(P_dict):
  all_times = set()
  doc_is = P_dict.keys()
  for doc_i in P_dict.keys():
    all_times.add(int(doc_i.split('_')[1])) # int(posix_time)
    for doc_j in P_dict[doc_i]:
      all_times.add(int(doc_j.split('_')[1])) # int(posix_time)

  all_times_list = list(all_times)
  all_times_list.sort()
  return dict([(all_times_list[i], i) for i in range(len(all_times_list))])

"""
converted dict:
fname_i -> commit index -> fname_j --> commit index -->
                                          (log_prob, token_count, token set)
"""
def convert_P_dict_with_lookup(P_dict):
  converted = {}
  doc_lookup = get_doc_lookup(P_dict)
  for doc_i in P_dict.keys():
    _, posix_time_i, commit_i, fname_i = doc_i.split('_')
    i = doc_lookup[int(posix_time_i)]
    if fname_i not in converted: converted[fname_i] = {}
    for doc_j in P_dict[doc_i].keys():
      _, posix_time_j, commit_j, fname_j = doc_j.split('_')
      j = doc_lookup[int(posix_time_j)]
      if fname_j not in converted[fname_i]: converted[fname_i][fname_j] = []
      
      # "token" is currently still a string, not a set...fix please
      log_prob, token_count, token = P_dict[doc_i][doc_j]
      converted[fname_i][fname_j].append((i, j,
                    float(log_prob), int(token_count),
                    token, 
                    '%s_%s' % (posix_time_i, commit_i), '%s_%s' % (posix_time_j, commit_j)))
  return converted

def graph_token_probs_pair(output_dir, year_q, user_i, user_j, P_dict):
  print user_i, user_j
  graph_dir = os.path.join(output_dir, year_q, output_probs_dir, output_graph_dir)
  if not os.path.exists(graph_dir):
    os.makedirs(graph_dir)
  doc_lookup = get_doc_lookup(P_dict)
  converted = convert_P_dict_with_lookup(P_dict)
  gen_fpath = os.path.join(graph_dir, '%s_%s_all.png' % (user_i, user_j))
  # all user_i to user_j as intensity map
  
  
  sp_dim = len(doc_lookup.values())
  all_vals = {}
  for fname_i in converted:
    for fname_j in converted[fname_i]:
      indices = np.array([(x[0], x[1]) for x in converted[fname_i][fname_j]])
      log_probs = np.array([x[2] for x in converted[fname_i][fname_j]])
      token_counts = np.array([x[3] for x in converted[fname_i][fname_j]])
      log_probs_np = csr_matrix((log_probs, (indices[:,0], indices[:,1])), shape=(sp_dim, sp_dim)).toarray()
      token_counts_np = csr_matrix((token_counts, (indices[:,0], indices[:,1])), shape=(sp_dim, sp_dim)).toarray()
      
      time_commit_dict = dict([((x[0], x[1]), (x[5], x[6])) for x in converted[fname_i][fname_j]])

      all_vals[(fname_i,fname_j)] = (log_probs_np, token_counts_np, time_commit_dict)

  # max: user_i to user_j, max doc_j time for a given doc_i time
  max_fpath = os.path.join(graph_dir, '%s_%s_max.png' % (user_i, user_j))
  fig_x, fig_y = 8, 6 # default dimensions
  num_plots = len(converted)
  fig, ax1_all = plt.subplots(num_plots, 1, figsize=(fig_x, num_plots*fig_y))
  if num_plots is 1: ax1_all = [ax1_all]
  ax2_all = [ax1.twinx() for ax1 in ax1_all]
  fname_is = converted.keys()
  fname_i_lookup = dict([(fname_is[i], i) for i in range(len(fname_is))])

  fname_len = len(all_vals.keys())
  cNorm  = mplcolors.Normalize(vmin=0, vmax=fname_len)
  b_scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=plt.get_cmap('winter'))
  r_scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=plt.get_cmap('autumn'))
  
  fname_ind = 0
  min_1 = 0
  max_2 = 0
  for fname_i, fname_j in all_vals:
    log_probs_np, token_counts_np, time_commit_dict = all_vals[(fname_i, fname_j)]
    #nz_i, nz_j = np.nonzero(log_probs_np)
    min_log_probs = -1*np.amax(-1*log_probs_np, axis=1) # take the negative
    amin_log_prob = np.unravel_index(np.argmax(-1*log_probs_np), log_probs_np.shape)
    max_token_counts = np.amax(token_counts_np, axis=1)
    amax_token_count = np.unravel_index(np.argmax(token_counts_np), log_probs_np.shape)
    commit_time_min_log_prob = time_commit_dict[amin_log_prob]
    commit_time_max_token_count = time_commit_dict[amax_token_count]
    with open(os.path.join(output_dir, year_q, output_probs_dir, 'argmin_prob'), 'a') as f:
      suffix_i, suffix_j = commit_time_min_log_prob
      f_i = '%s_%s/%s' % (user_i, suffix_i, fname_i)
      f_j = '%s_%s/%s' % (user_j, suffix_j, fname_j)
      f.write('%s,%s,%s\n' % (f_i, f_j, log_probs_np[amin_log_prob]))
    with open(os.path.join(output_dir, year_q, output_probs_dir, 'argmax_token'), 'a') as f:
      suffix_i, suffix_j = commit_time_max_token_count
      f_i = '%s_%s/%s' % (user_i, suffix_i, fname_i)
      f_j = '%s_%s/%s' % (user_j, suffix_j, fname_j)
      f.write('%s,%s,%s\n' % (f_i, f_j, token_counts_np[amax_token_count]))

    nz_j = np.nonzero(min_log_probs)
    plt_ind = fname_i_lookup[fname_i]
    ax1, ax2 = ax1_all[plt_ind], ax2_all[plt_ind]
    ax1.scatter(nz_j, min_log_probs[nz_j], marker='.',
                  color=b_scalarMap.to_rgba(fname_ind),
                  label='%s' % (fname_j))
    if np.amin(min_log_probs[nz_j]) < min_1: min_1 = np.amin(min_log_probs[nz_j])
    nz_j = np.nonzero(max_token_counts)
    ax2.scatter(nz_j, max_token_counts[nz_j], marker='+',
                  color=r_scalarMap.to_rgba(fname_ind),
                  label='%s' % (fname_j))
    if np.amax(max_token_counts[nz_j]) > max_2: max_2 = np.amax(max_token_counts[nz_j])
    print "min", min_1, "max", max_2
    fname_ind += 1

  for fname_i in converted:
    plt_ind = fname_i_lookup[fname_i]
    ax1, ax2 = ax1_all[plt_ind], ax2_all[plt_ind]
    ax1.set_xlabel('Commit number')
    ax1.set_ylabel('Log probabilities')
    ax1.set_ylim((min_1, 0))
    ax1.invert_yaxis() # because minimum
    ax2.set_ylim((0, max_2))
    ax1.set_xlim((0, sp_dim))
    handles,labels = ax1.get_legend_handles_labels()
    #ax1.legend(handles, labels, loc='upper right')
    fontP = mpl.font_manager.FontProperties()
    fontP.set_size('small')
    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0+box.height*0.2,
                   box.width, box.height * 0.8])
    box = ax2.get_position()
    ax2.set_position([box.x0, box.y0+box.height*0.2,
                   box.width, box.height * 0.8])
    # Put a legend to the right of the current axis
    ax1.legend(loc='lower center', bbox_to_anchor=(0.5, -0.40), prop=fontP,
              fancybox=True,ncol=4)

    ax2.legend(loc='lower center', bbox_to_anchor=(0.5, -0.20), prop=fontP,
              fancybox=True,ncol=4)
    
    ax2.set_ylabel('Token counts')
    ax1.set_title('%s/%s' % (user_i, fname_i))

  fig.suptitle('%s vs %s (min probability, max tokens)' % (user_i, user_j))
  fig.savefig(max_fpath)
  plt.close(fig)

def parse_token_probs(output_dir, year_q, use_commitdoc=False):
  max_users = {}
  P_dict = load_token_probs(output_dir, year_q, use_commitdoc=use_commitdoc)
  all_users = P_dict.keys()
  all_users.sort()
  all_pairs_users = []
  max_users = {}
  for user_i in all_users:
    for user_j in P_dict[user_i]: # all pairs users
      log_prob, token_count, token = P_dict[user_i][user_j]
      all_pairs_users.append((user_i, user_j, log_prob, token_count, token))

    max_user = max(P_dict[user_i].keys(), key=sort_function(P_dict[user_i]))
    max_log_prob, token_count, max_token = P_dict[user_i][max_user]
    max_users[user_i] = (user_i, max_user, max_log_prob, token_count, max_token)
  
  with open(os.path.join(output_dir, year_q,
              output_probs_dir, 'max_pairs_users'), 'w') as f:
    f.write('\n'.join(['%s\t%s\t%s\t%s\t%s' % max_users[user] for user in all_users]))

  with open(os.path.join(output_dir, year_q,
              output_probs_dir, 'all_pairs_users'), 'w') as f:
    f.write('\n'.join(['%s\t%s\t%s\t%s\t%s' % stuff for stuff in all_pairs_users]))

  # user_js = [max_users[user][1] for user in all_users]
  # #user_js += all_users
  # user_js_counts = [(user_j, user_js.count(user_j)) for user_j in set(user_js)]
  # sorted_user_js_counts = [(x[1]) for x in sorted(enumerate(user_js_counts), key=lambda x: -x[1][1])]
  # print '\n'.join(['%s\t%s' % x for x in sorted_user_js_counts][:20])
  return [max_users[user][:2] for user in max_users]

def token_probs(output_dir, year_q, use_commitdoc=False, user_pairs=None):
  token_granularity = output_commitdoc_dirname # smaller granularity
  if not use_commitdoc:
    token_granularity = output_user_dirname
  p_i_dict = load_p_numerator(output_dir, year_q, use_commitdoc=use_commitdoc)
  p_denom = load_p_denominator(output_dir, year_q, use_commitdoc=use_commitdoc)
  q_denom = load_q_denominator(p_i_dict)
  if use_commitdoc:
    n_dict = load_commitdoc_counts(output_dir, year_q)
  else:
    n_dict = load_user_counts(output_dir, year_q)

  P_dict = {} # user_i -> {user_j -> (token set, log prob, count)
  token_dir = os.path.join(output_dir, year_q, output_tokens_dir)
  prob_dir = os.path.join(output_dir, year_q, output_probs_dir, token_granularity)
  if not os.path.exists(prob_dir):
    os.makedirs(prob_dir)

  if user_pairs:
    # convert user pairs to dictionary for easier hashing
    user_pairs_temp = {}
    for user_i, user_j in user_pairs:
      user_pairs_temp[user_i] = user_j
    user_pairs = user_pairs_temp

  count = 0
  tot_tokens = len(p_i_dict)
  for token in p_i_dict:
    p_token = float(p_i_dict[token])
    log_p_token = np.log(p_token/p_denom)
    count += 1
    if use_commitdoc:
      user_dict = load_token_to_user(output_dir, year_q, token, use_commitdoc=True)
    else:
      user_dict = load_token_to_user(output_dir, year_q, token, use_commitdoc=False)

    users_token = user_dict.keys()
    if len(users_token) > max_users_per_token and max_users_per_token > 0:
      #print "skipping token %s (user count too high: %d)" % (token, len(users_token))
      continue
    if len(users_token) == 1:
      #print "skipping token %s (single user)" % (token)
      continue
    if count % 500 == 0:
      print "%d/%d token %s, users: %d (p_i_dict %d)" % (count, tot_tokens, token, len(users), p_token)
    # create user_i -> user_j dictionary for different types of comparison
    users = {}
    if user_pairs:
      for user_i in users_token:
        if user_i in user_pairs: # this token user has a pair
          if user_pairs[user_i] in users_token: # this paired user has this token
            users[user_i] = [user_pairs[user_i]]
      if not users: continue
    else:
      for i in range(len(users_token)):
        users[users_token[i]] = []
        for j in range(i+1, len(users_token)): # don't include self
          users[users_token[i]].append(users_token[j])

    print "%d/%d token %s, users_token %d, user pairs %s" % (count, tot_tokens, token, len(users_token), 'not printed') #str(users))
    if use_commitdoc: # per commit document, not user
      for user_i in users:
        for user_j in users[user_i]:
          for doc_i in user_dict[user_i]:
            for doc_j in user_dict[user_j]:
              if doc_i not in P_dict: P_dict[doc_i] = {}
              # undirected, otherwise crap breaks
              #if doc_j not in P_dict: P_dict[doc_j] = {}

              log_factor_i = np.log(1 - (1 - p_token/q_denom) ** n_dict[doc_i])
              log_factor_j = np.log(1 - (1 - p_token/q_denom) ** n_dict[doc_i])
              log_factor_tot = log_factor_i + log_factor_j + log_p_token
      
              if doc_j not in P_dict[doc_i]:
                P_dict[doc_i][doc_j] = [0, 0, set()]
              P_dict[doc_i][doc_j][0] += log_factor_tot
              P_dict[doc_i][doc_j][1] += 1
              P_dict[doc_i][doc_j][2].add(token)
              # undirected, otherwise crap breaks
              # if doc_i not in P_dict[doc_j]:
              #   P_dict[doc_j][doc_i] = [set(), 0, 0]
              # P_dict[doc_j][doc_i][0].add(token)
              # P_dict[doc_j][doc_i][1] += log_factor_tot
              # P_dict[doc_j][doc_i][2] += 1
              # ij_str = '%s___%s' % (doc_i, doc_j)
              # ji_str = '%s___%s' % (doc_j, doc_i)
              # with open(os.path.join(prob_dir, user_i), 'a') as f:
              #   f.write('%s\t%s\t%.15f\n' % (ij_str, token, log_factor_tot))
              # with open(os.path.join(prob_dir, user_j), 'a') as f:
              #   f.write('%s\t%s\t%.15f\n' % (ji_str, token, log_factor_tot))
    else: # per user, not commit document
      permuts = 0
      for user_i in users:
        for user_j in users[user_i]:
          permuts += 1
          if user_i not in P_dict: P_dict[user_i] = {}
          if user_j not in P_dict: P_dict[user_j] = {}

          log_factor_i = np.log(1 - (1 - p_token/q_denom) ** n_dict[user_i])
          log_factor_j = np.log(1 - (1 - p_token/q_denom) ** n_dict[user_j])
          log_factor_tot = log_factor_i + log_factor_j + log_p_token

          if user_j not in P_dict[user_i]:
            P_dict[user_i][user_j] = [0, 0, set()]
          P_dict[user_i][user_j][0] += log_factor_tot
          P_dict[user_i][user_j][1] += 1
          P_dict[user_i][user_j][2].add(token)
          if user_i not in P_dict[user_j]:
            P_dict[user_j][user_i] = [0, 0, set()]
          P_dict[user_j][user_i][0] += log_factor_tot
          P_dict[user_j][user_i][1] += 1
          P_dict[user_j][user_i][2].add(token)
  # for this token granularity, write all P_dict values.
  if use_commitdoc:
    for doc_i in P_dict:
      user_i = doc_i.split('_')[0]
      with open(os.path.join(prob_dir, user_i), 'a') as f:
        f.write('%s\n' % doc_i)
        doc_js = P_dict[doc_i].keys()
        doc_js.sort()
        f.write('\n'.join(['%s\t%s\t%s\t%s' % (doc_j,
                                P_dict[doc_i][doc_j][0],
                                P_dict[doc_i][doc_j][1],
                                ','.join(map(str,list(P_dict[doc_i][doc_j][2])))) \
                            for doc_j in doc_js]))
        f.write('\n')
  else:
    for i in P_dict:
      with open(os.path.join(prob_dir, i), 'w') as f:
        js = P_dict[i].keys()
        js.sort()
        f.write('\n'.join(['%s\t%s\t%s\t%s' % (j,
                                P_dict[i][j][0],
                                P_dict[i][j][1],
                                ','.join(map(str,list(P_dict[i][j][2])))) 
                             for j in js]))

"""
Load dictionary of p_i, the probability that a document contains word i.
p_i = <count of documents with word i> / total number of documents
** here, we assume that total number of documents are those of a token type, otherwise the denom gets too large.
Return two args: dict of p_i numerators, total number of documents
"""
def load_p_i_by_type(output_dir, year_q, token_type):
  p_dict = {}
  count_dir = os.path.join(output_dir, year_q, output_count_dir)
  for count_fname in os.listdir(count_dir):
    tt, f_suffix = count_fname.split('_')
    if tt != token_type: continue
    if f_suffix != doc_suffix: continue
    with open(os.path.join(count_dir, count_fname), 'r') as f:
      lines = f.readlines()
      for line in lines:
        line.strip()
        all_tabs = line.split('\t')
        token, count = '\t'.join(all_tabs[:-1]), int(all_tabs[-1])
        p_dict[token] = count
  with open(os.path.join(count_dir, '%s_unique' % token_type), 'r') as f:
    p_denom_by_type = len(f.readlines())
  # p_denom = 0
  # with open(os.path.join(count_dir, 'unique_docs'), 'r') as f:
  #   p_denom = len(f.readlines())

  #return p_dict, p_denom
  return p_dict, p_denom_by_type

def load_p_numerator(output_dir, year_q, use_commitdoc=False):
  p_dict = {}
  token_granularity = output_commitdoc_dirname
  if not use_commitdoc: token_granularity = output_user_dirname
  count_dir = os.path.join(output_dir, year_q, output_count_dir)
  with open(os.path.join(count_dir, '%s_doc' % token_granularity), 'r') as f:
    for line in f.readlines():
      token, count = line.strip().split('\t')
      p_dict[token] = int(count)
  return p_dict

def load_p_denominator(output_dir, year_q, use_commitdoc=False):
  token_granularity = output_commitdoc_dirname
  if not use_commitdoc: token_granularity = output_user_dirname
  count_dir = os.path.join(output_dir, year_q, output_count_dir)
  with open(os.path.join(count_dir, '%s_unique' % token_granularity), 'r') as f:
    p_denom = len(f.readlines())
    return p_denom

def load_q_denominator(p_dict):
  q_denom = 0
  for token in p_dict:
    q_denom += p_dict[token]
  return q_denom

"""
Load dicionary of q_i, the probability that if a document were to add
  a word to its word set, that it would add i.
q_i = <count of documents with word i> / q_denom
q_denom = sum_{j in all words} (documents with word j)
  separate q_denom by token_type; why not
q_i numerators are p_i numerators.
Return two args: dict of q_i numerators, q_denom
"""
def load_q_i_by_type_denom(output_dir, year_q, token_type, q_dict=None):
  if not q_dict: q_dict, _ = load_p_i_by_type(output_dir, year_q, token_type)
  q_denom = 0
  q_denom_by_type = 0
  for token in q_dict:
    print q_dict[token]
    q_denom += q_dict[token]
    q_denom_by_type += q_dict[token]
  return q_dict, q_denom_by_type

def load_token_probs(output_dir, year_q, use_commitdoc=False):
  token_granularity = output_commitdoc_dirname # smaller granularity
  if not use_commitdoc:
    token_granularity = output_user_dirname
  prob_dir = os.path.join(output_dir, year_q, output_probs_dir, token_granularity)

  doc_i = None
  P_dict = {}
  for user_i in os.listdir(prob_dir):
    if user_i not in P_dict: P_dict[user_i] = {}
    with open(os.path.join(prob_dir, user_i), 'r') as f:
      line = f.readline().strip()
      while line:
        user_j, log_prob, token_count, token = line.split('\t')
        P_dict[user_i][user_j] = (log_prob, token_count, token)
        line = f.readline().strip()
  return P_dict

def load_token_probs_pair(output_dir, year_q, user_i):
  prob_dir = os.path.join(output_dir, year_q, output_probs_dir, output_commitdoc_dirname)
  P_dict = {}
  print user_i
  user_j = None
  with open(os.path.join(prob_dir, user_i), 'r') as f:
    line = f.readline().strip()
    while line:
      if len(line.split('\t')) == 1:
        doc_i = line
        P_dict[doc_i] = {}
      else:
        doc_j, log_prob, token_count, token = line.split('\t')
        user_j_temp = doc_j.split('_')[0]
        if not user_j: user_j = user_j_temp
        elif user_j != user_j_temp:
          print "Error! More than one user_j here: %s, %s" % (user_j, user_j_temp)
          return
        P_dict[doc_i][doc_j] = (log_prob, token_count, token)
      line = f.readline().strip()

  return user_j, P_dict

def argmax_pairwise(P_dict):
  max_per_docs = {}
  for doc_i in P_dict:
    max_doc_j = max(P_dict[doc_i].keys(), key=sort_function(P_dict[doc_i]))
    max_per_docs[(doc_i, max_doc_j)] = P_dict[doc_i][max_doc_j]

  max_all_doc_is = max(max_per_docs.keys(), key=sort_function(max_per_docs))
  return max_all_doc_is, max_per_docs[max_all_doc_is]

def write_p_dict(output_dir, year_q):
  p_i_dict = load_p_numerator(output_dir, year_q)
  p_denom = load_p_denominator(output_dir, year_q)
  q_denom = load_q_denominator(p_i_dict)
  prob_dir = os.path.join(output_dir, year_q, output_probs_dir)
  all_tokens = p_i_dict.keys()
  all_tokens.sort()
  probs = []
  for token in all_tokens:
    if p_i_dict[token] == 1: continue
    if p_i_dict[token] == 0: print "zero token", token
    probs.append((token, np.log(float(p_i_dict[token])/p_denom)))
  with open(os.path.join(prob_dir, 'p_dict'), 'w') as f:
    f.write('\n'.join(['%s\t%s' % x for x in probs]))

def threshold_check(output_dir, year_q, use_commitdoc=False):
  p_i_dict = load_p_numerator(output_dir, year_q, use_commitdoc)
  p_denom = load_p_denominator(output_dir, year_q, use_commitdoc)
  q_denom = load_q_denominator(p_i_dict)
  n_dict = load_commitdoc_counts(output_dir, year_q)

  P_dict = {}
  token_dir = os.path.join(output_dir, year_q, output_tokens_dir)
  token_granularity = output_commitdoc_dirname # smaller granularity
  if not use_commitdoc:
    token_granularity = output_user_dirname
  prob_dir = os.path.join(output_dir, year_q, output_probs_dir)
  if not os.path.exists(prob_dir):
    os.makedirs(prob_dir)

  print p_i_dict
  count = 0
  tot_tokens = len(p_i_dict)
  thresh_count = 0
  thresh_val = 3
  tokens_to_user_count = {}
  for token in p_i_dict:
    count += 1
    user_dict = load_token_to_user(output_dir, year_q, token)
    p_token = float(p_i_dict[token])
    log_p_token = np.log(p_token/p_denom)

    users = user_dict.keys()
    commit_nums = [len(user_dict[user]) for user in users]
    tot_commits = sum(commit_nums)

    if len(users) == 1: continue
    if tot_commits < thresh_val:
      thresh_count += 1

    if len(users) not in tokens_to_user_count:
      tokens_to_user_count[len(users)] = 0
    tokens_to_user_count[len(users)] += 1
    
    if len(users) > 40:
      print "skipping token %s (user count too high: %d)" % (token, len(users))
      continue
    print "%d/%d token %s, users: %d (p_i_dict %d), num commits %d" % (count, tot_tokens, token, len(users), p_token, tot_commits)
    print "\tthresh count (< %d): %d" % (thresh_val, thresh_count)

  print '\n'.join(["%s\t%s" % (x, tokens_to_user_count[x]) for x in tokens_to_user_count])

