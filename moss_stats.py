from helper import *
from git_helper import *
from moss_tool import *
import matplotlib.colors as cl
import matplotlib.cm as cmx

use_annotate = False

def make_moss_graphs_multi(output_dir, regular=True):
  make_moss_graphs(output_dir, year_q=None, regular=regular)

def make_moss_graphs(output_dir, year_q=None, regular=True):
  # (other_username, int(tokens_matched),
  #          float(percent_self), float(percent_other))
  year_q_list = []
  top_sims = {}
  posix_lookup = {}
  gr = {}
  grp_comps = {}
  grp_edges = {}
  grp_only = True
  add_str = 'both_'
  if not year_q:
    # only use grade-based years
    for year_q_dirname in ['2012_1', '2013_1', '2014_1']:
      year_q = year_q_dirname
      top_sims.update(load_top_sims_from_log(output_dir, year_q, add_str=add_str))
      posix_lookup.update(load_posix_to_commit_ind(output_dir, year_q))
      all_grades = load_all_grades(output_dir, year_q)
      gr.update(get_graderank_dict(all_grades))
      if grp_only:
        comps, edges = load_components_info(output_dir, year_q)
        grp_comps.update(comps)
        grp_edges.update(edges)
      year_q_list.append(year_q)
  else:
    top_sims = load_top_sims_from_log(output_dir, year_q, add_str=add_str)
    posix_lookup = load_posix_to_commit_ind(output_dir, year_q)
    all_grades = load_all_grades(output_dir, year_q)
    gr = get_graderank_dict(all_grades)
    if grp_only:
      grp_comps, grp_edges = load_components_info(output_dir, year_q)
    year_q_list = year_q

  graph_percent_vs_token(output_dir, year_q_list, top_sims)
  get_top_commit_with_top_sim(top_sims)


  # sims: token, percent
  # time_types: commit, posix

  same_plot = True
  regular = True # graphing lecture code similarities
  # by commit
  graph_options = list(itertools.product((True, False), (True, False),
              (True, False), (True, False)))
  for use_grades, normalize_flag, use_mt, rank in graph_options:
    gr_dict = {}
    if use_grades:
      gr_dict = gr

    print "norm flag: %s, use_grades: %s, use_mt: %s, rank: %s" % (normalize_flag, use_grades, use_mt, rank)
    include_names = []
    for time_type in ['commit', 'posix']:
      thresh_unames = []
      intersections = []
      for sim in ['percent', 'token', 'percent_other']:
        thresh_unames.append(graph_all_similarities(output_dir, year_q_list,
                                  top_sims, posix_lookup,
                                  sim, time_type,
                                  same_plot=same_plot, only_names=include_names,
                                  gr=gr_dict, normalize_flag=normalize_flag,
                                  use_mt=use_mt, rank=rank,
                                  add_str=add_str,
                                  grp_info=(grp_comps, grp_edges)))
      print "%s: intersection of %s and %s:" % (time_type, 'percent', 'token')
      intersect, _ = intersect_uname_thresh(thresh_unames[0], thresh_unames[1],
          printout=bool(regular))
      intersections.append(intersect)
      if regular:
        include_names = intersect
    if not use_grades: break # because use_grades is the most significant bit?

def intersect_uname_thresh(uname_thresh_1, uname_thresh_2, printout=False):
  # uname_thresh: (uname, percentage)
  all_unames = list(set([x[0] for x in uname_thresh_1]).union([x[0] for x in uname_thresh_2]))
  all_unames.sort()
  intersect_unames = list(set([x[0] for x in uname_thresh_1]).intersection([x[0] for x in uname_thresh_2]))
  intersect_unames.sort()

  all_dict = {}
  for uname in all_unames:
    all_dict[uname] = ['', '']
  for uname, thresh in uname_thresh_1:
    all_dict[uname][0] = thresh
  for uname, thresh in uname_thresh_2:
    all_dict[uname][1] = thresh

  if printout:
    print '\n'.join([('\t'.join([uname] + [str(x) for x in all_dict[uname]])) for uname in all_unames])
    print
    print '\n'.join(intersect_unames)
  return intersect_unames, all_dict

def get_top_commit_with_top_sim(top_sims):
  top_token, top_percent = 0, 0.0
  top_token_commit, top_percent_commit = '',''
  for uname in top_sims:
    for commit in top_sims[uname]:
      _, token, percent, _, _, _ = top_sims[uname][commit]
      if token > top_token:
        top_token = token
        top_token_commit = '%s_%s' % (uname, commit)
      if percent > top_percent:
        top_percent = percent
        top_percent_commit = '%s_%s' % (uname, commit)
  print "max by tokens", top_token, top_token_commit
  print "max by percent", top_percent, top_percent_commit

"""
Graphs the percent of tokens you share with another by the number of tokens.
Ignore the percent of tokens the other shares with you.
The later timestamps are colored darker.
"""
def graph_percent_vs_token(output_dir, year_q_list, top_sims):
  year_q = '2014_1'
  try: # check if string
    year_q_list.split('_') # is string
    year_q = year_q_list
    year_q_list = []
  except:
    pass
  percent_thresh = 30 # if you want to cut off your graph
  token_thresh_min = 0
  token_thresh_max = 500

  parsed_set = set()
  for uname in top_sims:
    for posix_time in top_sims[uname]:
      _, token, percent_self, _, _,_ = top_sims[uname][posix_time]
      if percent_self <= percent_thresh: continue
      if token <= token_thresh_min: continue
      if token_thresh_max != -1 and token >= token_thresh_max: continue
      parsed_set.add((token, percent_self, int(posix_time)))
  parsed_list = list(parsed_set)
  parsed_np = np.array(parsed_list)
  tokens = parsed_np[:,0]
  percents = parsed_np[:,1]
  posix_times = parsed_np[:,2]
  time_002, time_100 = np.percentile(posix_times, [5,100])
  # Some students start way early (because they dropped last quarter).
  # Convert times to scale between 0 and 1 (0 is black, which should be the latest)
  posix_times_adj = 1 - np.maximum(posix_times - time_002, 0)/(time_100 - time_002)
  #print np.array([posix_times, posix_times_adj])[:10,:].T # to verify black is latest
  
  fig = plt.figure()
  ax1 = plt.gca()
  #plt.rcParams['image.cmap'] = 'gray'
  sc = plt.scatter(tokens, percents, c=posix_times_adj, edgecolors='none')

  xlims = ax1.get_xlim()
  ax1.set_xlim(0, ax1.get_xlim()[1])
  ax1.set_ylim(percent_thresh, 100) # percent max is 100%
  ax1.set_title('(%s) Similarity percent vs tokens (Darker=later) (thresh=%d%%)' % (year_q, percent_thresh))
  if len(year_q_list) > 0:
    ax1.set_title('(%s) Similarity percent vs tokens (Darker=later) (thresh=%d%%)' % ('_'.join(year_q_list), percent_thresh))
  ax1.set_xlabel('Tokens')
  ax1.set_ylabel('Percent similarity to current file')
  
  plt.tight_layout()
  fig_dest = os.path.join(output_dir, '%s_percent_vs_token_thresh_%d_%d.png' % (year_q, percent_thresh, token_thresh_max))
  if len(year_q_list) > 0:
    fig_dest = os.path.join(output_dir, '%s_percent_vs_token_thresh_%d_%d.png' % ('_'.join(year_q_list), percent_thresh, token_thresh_max))
  print "Saving", fig_dest
  fig.savefig(fig_dest)
  plt.close()

"""
Creates multiple graphs, not just one.
Creates one line graph per student looking at moss trends over time.
  Plots the top similarity number per timestep and ignores *who* the other
  person is.
  Plots similarity by tokens OR by percent similar to self.
Also graphs all students on 10x10 graphs.
"""
def graph_similarities_over_time(output_dir, year_q, top_sims, sim, time_type, graph_indiv=True):
  print "%s: Similarities by %s over %s" % (year_q, sim, time_type)
  all_timeseries = {}
  all_times_sims = []

  # parse all top sims and get data
  print "Parsing all top sims..."
  max_commits = 0
  for uname in top_sims:
    if sim == 'token': sim_ind = 1
    elif sim == 'percent': sim_ind = 2
    elif sim == 'percent_other': sim_ind = 3
    temp_list = [(int(posix_time),
                  top_sims[uname][posix_time][sim_ind],
                 int('online' in top_sims[uname][posix_time][0])) \
          for posix_time in top_sims[uname]]
    max_commits = max(max_commits, len(temp_list))
    all_times_sims += temp_list
    other_names = [top_sims[uname][posix_time][0] \
          for posix_time in top_sims[uname]]
    temp_np = np.array(temp_list)
    all_timeseries[uname] = (other_names, temp_np[temp_np[:,0].argsort()])

  # get online sim information
  online_sims = get_top_sims_online(top_sims)
    
  all_times_sims_np = np.array(all_times_sims)
  
  all_posix_times_np = all_times_sims_np[:,0]
  all_sims_np = all_times_sims_np[:,1]

  # cutting off the graph a bit
  time_002, time_100 = np.percentile(all_posix_times_np, [2,100])
  sim_min, sim_max = np.percentile(all_sims_np, [0,100])
  incr = (time_100 - time_002)/10
  posix_range = np.arange(time_002, time_100, step=incr)
  # using days only?
  incr = incr_length
  posix_range = np.arange(all_start_time, all_end_time, step=incr)
  x_labels = [posix_to_datetime(posix_t) for posix_t in posix_range]

  # make the student graph dir if it doesn't exist
  indiv_output_dir = os.path.join(output_dir, year_q, 'graphs')
  if not os.path.exists(indiv_output_dir):
    os.makedirs(indiv_output_dir)
  # create the figure handles for the all student graphs
  print "Creating handles for all student graphs..."
  num_unames = len(all_timeseries)
  fig_all, ax_all = [0]*(num_unames/100+1), [0] * (num_unames/100+1)
  for plt_ind in range(num_unames/100+1):
    fig_all[plt_ind], ax_all[plt_ind] = plt.subplots(10, 10, figsize=(40,20))

  print "Graphing data each student..."
  #### graph all students
  uname_ind = 0
  for uname in all_timeseries:
    other_names, time_array = all_timeseries[uname]
    posix_times = time_array[:,0]
    sims = time_array[:,1]
    online_bools = time_array[:,2].astype(bool)
    keep_inds = posix_times >= 0#time_002 # cut off graph a bit
    posix_times_sort = posix_times[keep_inds]
    sims_sort = sims[keep_inds]
    online_bools_sort = online_bools[keep_inds]
    scatter_highlight = \
      [(sims_sort[i], posix_times_sort[i],
          i, posix_to_datetime(posix_times_sort[i])) \
        for i in range(len(posix_times_sort)) \
        if online_bools_sort[i]]
    if scatter_highlight: # instead of online_sims, in case the online part happened before time_002.
      sims_online, posix_online, commits_online, date_times = zip(*scatter_highlight)

    plt_c = 'b' # in class
    if online_sims[uname] != 0: # this might mean that online sim before 2nd percentile
      plt_c = 'r' # online

    # single student plot
    if graph_indiv:
      fig = plt.figure()
      ax1 = plt.gca()
        
      if time_type is 'posix':
        plt.plot(posix_times_sort, sims_sort, color=plt_c)
        if scatter_highlight:
          plt.scatter(posix_online, sims_online, marker='o', c='r')
      elif time_type is 'commit':
        plt.plot(sims_sort, color=plt_c)
        if scatter_highlight:
          plt.scatter(commits_online, sims_online, marker='o', c='r')

      if sim is 'token':
        ax1.set_ylim(sim_min, sim_max)
      elif sim in ['percent', 'percent_other']:
        ax1.set_ylim(0, 100)
      ax1.set_ylabel(sim)
      if time_type is 'posix':
        ax1.set_xlim(time_002, time_100)
        xtickNames = plt.setp(ax1, xticklabels=x_labels)
        plt.setp(xtickNames, rotation=45, fontsize=8)
      else:
        ax1.set_xlim(0, max_commits)
      ax1.set_xlabel(time_type)
      title_str = '%s, %s top similarity (%s) over %s' % \
            (year_q, uname_ind, sim, time_type)
      if sim == 'token':
        title_str = '%s (%s, %s)' % (title_str, sim_min, sim_max) 
      if time_type == 'posix':
        title_str = '%s [%s-%s]' % (title_str, x_labels[0], x_labels[-1])
      elif sim is 'commit':
        #title_str = '%s [%s max commits]' % (title_str, max_commits)
        pass
      ax1.set_title(title_str)
      plt.tight_layout()

      fig_dest = os.path.join(indiv_output_dir, '%s_%s_%s_%04d.png' % (time_type, sim, year_q, uname_ind))
      print "Saving", fig_dest
      fig.savefig(fig_dest)
      plt.close()

    # all student plot
    plt_ind = uname_ind/100
    plt.figure(plt_ind)
    fig_all[plt_ind].hold(True)
    plt_uname_ind_y, plt_uname_ind_x = (uname_ind % 100)/10, (uname_ind % 100) % 10
    ax_std = ax_all[plt_ind][plt_uname_ind_y, plt_uname_ind_x]
    if time_type is 'posix':
      ax_std.plot(posix_times_sort, sims_sort, color=plt_c)
      if scatter_highlight:
        ax_std.scatter(posix_online, sims_online, marker='o', c='r')
    elif time_type is 'commit':
      ax_std.plot(sims_sort, color=plt_c)
      if scatter_highlight:
        ax_std.scatter(commits_online, sims_online, marker='o', c='r')
    ax_std.set_title('%04d' % (uname_ind))
    plt.setp(ax_std,xticklabels=[],yticklabels=[])
    if sim == 'token':
      ax_std.set_ylim(sim_min, sim_max)
    elif sim == 'percent':
      ax_std.set_ylim(0,100)
    if time_type is 'posix':
      ax_std.set_xlim(time_002, time_100)
    elif time_type is 'commit':
      ax_std.set_xlim(0, max_commits)
      
    uname_ind += 1

  # format and save all student plots
  title_str = '%s top similarity (%s) over %s' % (year_q, sim, time_type)
  if sim is 'token':
    title_str = '%s (%s, %s)' % (title_str, sim_min, sim_max) 
  if time_type is 'posix':
    title_str = '%s [%s-%s]' % (title_str, x_labels[0], x_labels[-1])
  elif time_type is 'commit':
    title_str = '%s [%s max commits]' % (title_str, max_commits)
  all_fig_dest_prefix = '%s_%s_%s' % (year_q, time_type, sim)
  if sim is 'token':
    all_fig_dest_prefix += '_%s_%s' % (sim_min, sim_max)

  for plt_ind in range(num_unames/100+1):
    plt.figure(plt_ind)
    title_str_ind = '%s (Part %s)' % (title_str, plt_ind)
    fig_all[plt_ind].suptitle(title_str_ind)
    all_fig_dest_ind = os.path.join(output_dir,
              '%s_%s.png' % (all_fig_dest_prefix, plt_ind))
    print "Saving the all student fig", all_fig_dest_ind
    fig_all[plt_ind].savefig(all_fig_dest_ind)
    plt.close(fig_all[plt_ind])

  # write lookup file for uname ind to uname.
  write_ind = 0
  with open(os.path.join(output_dir, '%s_lookup_index_to_uname' % year_q), 'w') as f:
    for uname in all_timeseries:
      f.write('%04d,%s\n' % (write_ind, uname))
      write_ind += 1

"""
Basically the same as the regular similarities graph, but only scatter plot the times and token/percents.
Grouped into every 100 students as usual. Turn this off with same_plot=True.
Also graph a threshold indicating 95th or 99th percentile (specify this in
  the call to med_calc), and label the usernames that exceed that threshold.

Returns all usernames that are labeled, in thresh_unames (with the threshold).
"""
def graph_all_similarities(output_dir, year_q_list, top_sims, posix_lookup,
            sim, time_type,
            same_plot=False, only_names=None,
            gr=None, normalize_flag=False,
            use_mt=False, rank=False, add_str=None,
            grp_info=None):
  print "%s: Similarities by %s over %s, scatter all on one graph" % (year_q_list, sim, time_type)
  year_q = '2014_1'
  try:
    '_'.split(year_q_list) # would mean string
    year_q = year_q_list
    year_q_list = []
    print "is year", year_q, year_q_list
  except:
    pass
  all_start_time, all_end_time = all_startend_times[year_q]

  all_timeseries = {}
  all_times_sims = []
  use_grades = bool(gr)
  if only_names:
    only_names = set(only_names)
  else:
    only_names = set()
  # change snapshot times to value between 0 to 1 (% completion)
  norm_gran = 3 # decimal granularity

  # only graph certain groups
  grp_comps, grp_edges = grp_info
  grp_only = bool(grp_comps) and bool(grp_edges)
  print "grp only!!!!" , grp_only

  # parse all top sims and get data
  if sim == 'token': sim_ind = 1
  elif sim == 'percent': sim_ind = 2
  elif sim == 'percent_other': sim_ind = 3
  print "Parsing all top sims..."
  max_commits = 0
  for uname in top_sims:
    uname_year, uname_q = uname[:4], uname[4:6]
    uname_year_q = '%s_%s' % (int(uname_year), int(uname_q))

    posix_times = top_sims[uname].keys()
    posix_times.sort()
    if uname not in posix_lookup:
      print "%s not in posix_lookup :(" % uname
      continue
    try:
      commit_inds = np.array([posix_lookup[uname][int(posix_time)] for posix_time in posix_times]).astype(float)
    except:
      print "posix_time %s did not exist for uname" % str(posix_times), uname
      continue
    scaled_posix_times = scale_days(np.array(posix_times).astype(int), uname_year_q, year_q)
    #commit_inds = np.arange(len(posix_times)).astype(float)
    if normalize_flag:
      commit_inds = np.around(commit_inds/len(posix_lookup[uname].keys()), decimals=norm_gran)
    # if normalize_flag:
    #   commit_inds_sort = np.around(commit_inds_sort/len(posix_times_sort),
    #                                decimals=norm_gran)

    grade = 1.0 # doesn't matter
    if use_grades:
      if uname not in gr: continue
      grade = gr[uname][int(rank)][int(not use_mt)]
    temp_list = [(int(scaled_posix_times[i]),
                 top_sims[uname][posix_times[i]][sim_ind],
                 int('online' in top_sims[uname][posix_times[i]][0]),
                 commit_inds[i],
                 grade) \
          for i in range(len(posix_times))]
          #for posix_time in top_sims[uname]]
    max_commits = max(max_commits, len(temp_list))
    all_times_sims += temp_list
    other_names = [top_sims[uname][posix_time][0] \
          for posix_time in top_sims[uname]]
    temp_np = np.array(temp_list)
    all_timeseries[uname] = (other_names, temp_np[temp_np[:,0].argsort()])
  all_times_sims_np = np.array(all_times_sims)
  all_posix_times_np = all_times_sims_np[:,0]
  all_sims_np = all_times_sims_np[:,1]
  all_online_np = all_times_sims_np[:,2]
  all_commits_np = all_times_sims_np[:,3]
  meds_commit = med_calc(all_commits_np, all_sims_np)
  meds_posix = med_calc(all_posix_times_np, all_sims_np)
  if time_type is 'posix':
    med_times, med_sims = meds_posix[:,0], meds_posix[:,1]
  elif time_type is 'commit':
    med_times, med_sims = meds_commit[:,0], meds_commit[:,1]
  med_lookup = {}
  for i in range(len(med_times)):
    med_lookup[med_times[i]] = med_sims[i]

  # cutting off the graph a bit
  time_002, time_100 = np.percentile(all_posix_times_np, [0.8,100])
  incr = (time_100 - time_002)/10
  #posix_range = np.arange(time_002, time_100, step=incr)
  # using days only?
  incr = incr_length
  posix_range = get_day_range(year_q, plus_minus=[0,1], incr=incr)
  sim_min, sim_max = np.percentile(all_sims_np, [0,100])
  x_labels = [posix_to_datetime(posix_t) for posix_t in posix_range]
  print x_labels

  # create the figure handles for the all student graphs
  print "Creating handles for all student graphs..."
  num_unames = len(all_timeseries)
  fig_all, ax_all = [0]*(num_unames/100+1), [0] * (num_unames/100+1)
  points_all = [0]*(num_unames/100+1)
  for plt_ind in range(num_unames/100+1):
    fig_all[plt_ind] = plt.figure(figsize=(10,10))
    ax_all[plt_ind] = plt.gca()
    points_all[plt_ind] = []
    if same_plot: break
  m = set_colormap([0.0, 1.0]) # for coloring

  #### graph all students
  thresh_unames = []
  uname_ind = 0
  online_list = []
  offline_list = []
  for uname in all_timeseries:
    if uname_ind % 50 == 1: print uname_ind
    uname_ind += 1
    other_names, time_array = all_timeseries[uname]
    posix_times = time_array[:,0]
    keep_inds = posix_times >= time_002 # cut off graph a bit
    keep_inds = posix_times >= all_start_time # use start_time

    posix_times_sort = posix_times[keep_inds]
    sims_sort = time_array[keep_inds,1]
    online_bools_sort = time_array[keep_inds,2].astype(bool)
    commit_inds_sort = time_array[keep_inds,3]
    #np.arange(len(posix_times_sort)).astype(float)
    grades_sort = time_array[keep_inds,4]
    if use_grades: # filter by grade
      #if not np.any(np.logical_and(grades_sort > 0.1, grades_sort < 0.8)):
      # if not np.any(np.logical_or(grades_sort < 0.2, grades_sort > 0.7)):
      #   continue
      pass

    if len(sims_sort) == 0:
      print "%s has no moss after %s" % (uname, x_labels[0])
      continue
    
    # check if name should be different color
    highlight_flag = False
    highlight_c = 'k'
    if only_names:
      if uname[6:] in only_names:
        highlight_flag = True
      #else: uname_ind += 1; continue

    # add label
    max_ind = np.argmax(sims_sort ** 2 + np.array(range(len(sims_sort))) ** 2)
    max_sim, max_posix = sims_sort[max_ind], posix_times_sort[max_ind]

    # online/offline
    def default_highlight():
      return lambda tup: tup[-1]

    highlight_fn = default_highlight()
    if grp_only:
      if uname not in grp_comps:
        continue
      def grp_highlight():
        edge_posix = set()
        if uname not in grp_edges:
          # uname is only pointed to; it is a sink!
          print "sink in comp", uname, "info", grp_comps[uname]
          return lambda x: False
        def above_thresh(tup):
          posix_check = tup[1]
          grp_num = grp_comps[uname][0]
          if uname in grp_edges:
            for uname_other in grp_edges[uname]:
              thresh_result = False
              try:
                thresh_result = check_thresh(*map(float,
                  grp_edges[uname][uname_other][str(posix_check)][2:]))
              except: pass
              if thresh_result:
                return grp_num == 0
          return False

        return lambda tup: above_thresh(tup)
      # don't care about those that don't have any online
      #continue
      highlight_fn = grp_highlight()

    all_info = [(sims_sort[i], posix_times_sort[i],
                 commit_inds_sort[i],
                 posix_to_datetime(posix_times_sort[i]),
                 grades_sort[i],
                 online_bools_sort[i]) \
                     for i in range(len(posix_times_sort))]
    scatter_highlight = filter(highlight_fn, all_info)
    scatter_offline = filter(lambda x: not highlight_fn(x), all_info)

    # scatter_highlight = \
        
    #   [(sims_sort[i], posix_times_sort[i],
    #       commit_inds_sort[i], posix_to_datetime(posix_times_sort[i]),
    #       grades_sort[i])\
    #     for i in range(len(posix_times_sort)) \
    #     if online_bools_sort[i]]

    # scatter_offline = \
    #   [(sims_sort[i], posix_times_sort[i],
    #       commit_inds_sort[i], posix_to_datetime(posix_times_sort[i]),
    #       grades_sort[i])\
    #     for i in range(len(posix_times_sort)) \
    #     if not online_bools_sort[i]]
    online_c, offline_c = 'r', 'b'
    on_c, off_c = online_c, offline_c # colors to graph circles
    if scatter_highlight: # instead of online_sims, in case the online part happened before time_002.
      sims_online, posix_online, commits_online, _, grades_online,_ = zip(*scatter_highlight)
      # print uname
      # print zip(sims_online, posix_online)
      if use_grades: on_c = m.to_rgba(grades_online)
      #print uname, grades_online[0]
    if scatter_offline:
      sims_offline, posix_offline, commits_offline, _, grades_offline,_ = zip(*scatter_offline)
      if use_grades: off_c = m.to_rgba(grades_offline)

    # all student plot
    plt_ind = uname_ind/100
    if same_plot:
      plt_ind = 0
    plt.figure(plt_ind)
    fig_all[plt_ind].hold(True)
    ax_std = ax_all[plt_ind]
    points_std = points_all[plt_ind]

    if use_grades:
      c_plot = m.to_rgba(grades_sort[0])
    else:
      c_plot = 'b'
    first_last = [0, len(sims_sort)-1]
    if time_type is 'posix':
      ax_std.plot(posix_times_sort, sims_sort, '-', lw=1, c=c_plot, alpha=0.2)
      # ax_std.scatter(posix_times_sort[0], sims_sort[0], marker='^',s=30,lw=0,c=c_plot,alpha=0.8)
      # ax_std.scatter(posix_times_sort[-1], sims_sort[-1], marker='s',s=30,lw=0,c=c_plot,alpha=0.8)
    elif time_type is 'commit':
      if grp_only:
        ax_std.plot(commit_inds_sort, sims_sort, '-', lw=1, c=c_plot, alpha=0.2)
      # ax_std.scatter(commit_inds_sort[0], sims_sort[0], marker='^',s=30,lw=0,c=c_plot,alpha=0.8)
      # ax_std.scatter(commit_inds_sort[-1], sims_sort[-1], marker='s',s=30,lw=0,c=c_plot,alpha=0.8)
      pass

    if time_type is 'posix':
      if scatter_highlight: # outline the online
        online_list.append((posix_online, sims_online, on_c))
      if scatter_offline:
        offline_list.append((posix_offline, sims_offline, off_c))
      points_std.append([posix_times_sort, sims_sort])
    elif time_type is 'commit':
      # max_ind, max_sim, thresh_perc = get_label_if_thresh(commit_inds_sort, sims_sort, med_lookup)
      # if max_sim != -1:
      #   thresh_unames.append((uname[6:], thresh_perc))
      #   if use_annotate:
      #     ax_std.annotate(uname[6:], xy=(max_ind, max_sim), size=10, textcoords='data')
      if scatter_highlight: # outline the online
        online_list.append((commits_online, sims_online, on_c))
      if scatter_offline:
        offline_list.append((commits_offline, sims_offline, off_c))
      points_std.append([range(len(sims_sort)), sims_sort])


  # plot all offline first, then online
  for time_x, sim_y, c in offline_list:
    ax_std.scatter(time_x, sim_y, marker='.', color=c, lw=0, alpha=0.3)
  for time_x, sim_y, c in online_list:
    ax_std.scatter(time_x, sim_y, marker='o', color=c, lw=0, s=30, alpha=0.5)

  # format and save all student plots
  title_str = '%s top similarity (%s) over %s' % (year_q, sim, time_type)
  if len(year_q_list) > 0:
    title_str = '%s top similarity (%s) over %s' % ('_'.join(year_q_list), sim, time_type)
  if sim == 'token':
    title_str = '%s (%s, %s)' % (title_str, sim_min, sim_max) 
  if time_type == 'posix':
    try:
      print "possible", x_labels
      title_str = '%s [%s-%s]' % (title_str, x_labels[0], x_labels[-1])
    except:
      pass
  elif time_type == 'commit':
    title_str = '%s [%s max commits]' % (title_str, max_commits)
  if use_grades:
    exam_str = 'MT' if use_mt else 'Final'
    rank_str = 'Rankings' if rank else 'Absolute'
    title_str = '%s (with %s %s grades)' % (title_str, rank_str, exam_str)
  if add_str:
    title_str = '%s (%s)' % (title_str, add_str)

  all_fig_dest_prefix = '%s_aggr_%s_%s' % (year_q, time_type, sim)
  if len(year_q_list) > 0:
    all_fig_dest_prefix = '%s_aggr_%s_%s' % ('_'.join(year_q_list), time_type, sim)
  if grp_only:
    all_fig_dest_prefix += "_group"
  #all_fig_dest_prefix += "_special"
  if normalize_flag and time_type is 'commit':
    all_fig_dest_prefix = '%s_%s' % (all_fig_dest_prefix, 'norm')
  if sim == 'token':
    all_fig_dest_prefix += '_%s_%s' % (sim_min, sim_max)
  if use_grades:
    if use_mt:
      all_fig_dest_prefix += '_%s' % 'MT'
    else:
      all_fig_dest_prefix += '_%s' % 'Final'
    if rank:
      all_fig_dest_prefix += '_%s' % 'rank'
    else:
      all_fig_dest_prefix += '_%s' % 'abs'
  if add_str:
    all_fig_dest_prefix = '%s%s' % (add_str, all_fig_dest_prefix)

  for plt_ind in range(num_unames/100+1):
    plt.figure(plt_ind)
    ax_std = ax_all[plt_ind]
    if sim == 'token':
      ax_std.set_ylim(sim_min, sim_max)
    elif sim in ['percent', 'percent_other']:
      ax_std.set_ylim(0,100)
    if time_type == 'posix':
      #ax_std.set_xlim(time_002, time_100)
      # use start times
      ax_std.set_xlim(posix_range[0], posix_range[-1])
      ax_std.set_xticks(posix_range)
      ax_std.set_xticklabels(x_labels, rotation=45, fontsize=8)
      #ax_std.plot(med_times[::5], med_sims[::5], c='k')
    elif time_type == 'commit':
      if normalize_flag:
        ax_std.set_xlim(0, 1.0)
      else:
        ax_std.set_xlim(0, max_commits)
      ax_std.plot(med_times, med_sims, c='k')

    plt.figure(plt_ind)
    if use_grades:
      fig_all[plt_ind].tight_layout()
      cbar_ax = fig_all[plt_ind].add_axes([0.95, 0.07, 0.02, 0.8])
      cbar_ax.tick_params()#labelsize=tick_fs)
      fig_all[plt_ind].colorbar(m, cax=cbar_ax)
    title_str_ind = '%s (Part %s)' % (title_str, plt_ind)
    if same_plot:
      #title_str_ind = '%s (all)' % (title_str)
      title_str_ind = '%s' % (title_str)
    ax_all[plt_ind].set_title(title_str_ind)
    ax_all[plt_ind].set_xlabel(time_type)
    if normalize_flag and time_type is 'commit':
      ax_all[plt_ind].set_xlabel('commit (normalized)')
    ax_all[plt_ind].set_ylabel(sim)
    all_fig_dest_ind = os.path.join(output_dir,
              '%s_%s.png' % (all_fig_dest_prefix, plt_ind))
    if same_plot:
      all_fig_dest_ind = os.path.join(output_dir,
              '%s_all.png' % (all_fig_dest_prefix))
    print "Saving the all student fig", all_fig_dest_ind
    fig_all[plt_ind].savefig(all_fig_dest_ind)
    plt.close(fig_all[plt_ind])
    if same_plot: break
  # return the unames exceeding med_calc threshold (probably 95th percentile)
  return thresh_unames
    
  #points_std.append(np.array([range(len(sims_sort)), sims_sort]))
############## BELOW THIS LINE IS DEPRECATED CODE #############

# Messy approximate graphs that don't really matter.
def make_moss_graphs_messy(output_dir, year_q):
  all_sims = load_all_sims_from_log(output_dir, year_q)
  all_output_f = get_all_output_f(all_sims)
  top_sims = {}
  for uname in all_sims:
    top_sims[uname] = {}
    for commit in all_sims[uname]:
      if len(all_sims[uname][commit]) == 0: continue
      other_f_path, _, _, percent, _ = all_sims[uname][commit][0]
      top_sims[uname][commit] = (get_uname_from_f(other_f_path), percent)
  graph_moss_all_student(all_sims, all_output_f, output_dir, year_q) 
  graph_aggr_top_moss(top_sims, all_output_f, output_dir, year_q)

"""
Creates one graph per student for moss similarities.
"""
def graph_moss_all_student(all_sims, y_labels, output_dir, year_q):
  y_labels = list(y_labels)
  y_labels.sort()
  y_ref_dict = dict([(y_labels[i], i) for i in range(len(y_labels))])
  for uname in all_sims:
    all_times = []
    for posix_time in all_sims[uname]:
      for sim in all_sims[uname][posix_time]:
        other_path, other_html, tokens, percent_self, percent_other = sim
        y_ind = y_ref_dict[get_uname_from_f(other_path)]
        
        all_times.append((int(posix_time), y_ind, float(percent_self)/100))
    if not all_times: continue
    x_scatter, y_scatter, z_cs = zip(*all_times)
    
    print "Making plot."
    fig = plt.figure(figsize=(7,max(int(len(y_labels)/7), 7)))
    ax1 = plt.gca()
    marker_size = 100
    print "Graphing scatter."
    #plt.rcParams['image.cmap'] = 'gray'
    sc = plt.scatter(x_scatter, y_scatter, marker_size, c=z_cs)
    plt.colorbar()

    # put students on y axis
    #y_real_labels = [''] +  y_labels + ['']
  
    ax1.set_ylim(0, len(y_labels)-1)
    ax1.set_yticks(np.arange(len(y_labels)))
    ytickNames = plt.setp(ax1, yticklabels=y_labels)
    plt.setp(ytickNames, fontsize=8)

    # put times on x axis
    # ax_std.set_xlim(all_start_time, all_end_time)
    # ax_std.set_xlim(posix_range[0], posix_range[-1])
    # ax_std.set_xticks(posix_range)
    # ax_std.set_xticklabels(xlabels, rotation=45, fontsize=8)
    xlims = ax1.get_xlim()
    incr = (xlims[1] - xlims[0])/10
    posix_range = np.arange(xlims[0], xlims[1], step=incr)

    x_labels = [posix_to_datetime(posix_t) for posix_t in posix_range]
    xtickNames = plt.setp(ax1, xticklabels=x_labels)
    plt.setp(xtickNames, rotation=45, fontsize=8)

    ax1.set_title('%s, %s Moss similarity' % (year_q, uname))
    # resize
    plt.tight_layout()

    fig_dest = os.path.join(output_dir, 'moss_%s_%s.png' % (year_q, uname))
    print "Saving", fig_dest
    fig.savefig(fig_dest)
    plt.close()

"""
Creates one graph per class for moss similarities...?
"""
def graph_aggr_moss(similarities, ):
  pass

"""
Creates one graph per class for only the top moss
similarity per commit.
"""
def graph_aggr_top_moss(top_sims, y_labels, output_dir, year_q):
  y_labels = list(y_labels)
  y_labels.sort()
  y_ref_dict = dict([(y_labels[i], i) for i in range(len(y_labels))])
  print y_ref_dict
  fig = plt.figure()
  ax1 = plt.gca()
  jet = plt.get_cmap('jet')
  cNorm = cl.Normalize(vmin=0, vmax=len(y_labels))
  uname_scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)
  print uname_scalarMap.get_clim()
  for uname in top_sims:
    all_times = []
    for posix_time in top_sims[uname]:
      other_f, percent = top_sims[uname][posix_time]
      all_times.append((int(posix_time), y_ref_dict[other_f], float(percent)/100))
    x_scatter, y_scatter, gray_cs = zip(*all_times)
    
    marker_size = 100
    uname_c = uname_scalarMap.to_rgba(y_ref_dict[uname])
    uname_c_norm = [float(0.5*uc)/max(uname_c) for uc in uname_c]
    colors=[map(lambda x: 0.25+x*gc, uname_c_norm) \
                for gc in gray_cs]
    sc = plt.scatter(x_scatter, y_scatter, marker_size, c=colors)
    plt.show()

  # put students on y axis
  #y_real_labels = [''] +  y_labels + ['']
  
  ax1.set_ylim(0, len(y_labels)-1)
  ytickNames = plt.setp(ax1, yticklabels=y_labels)
  plt.setp(ytickNames, rotation=45, fontsize=8)

  # put times on x axis
  xlims = ax1.get_xlim()
  incr = (xlims[1] - xlims[0])/10
  posix_range = np.linspace(xlims[0], xlims[1], 10)
  x_labels = [posix_to_datetime(posix_t) for posix_t in posix_range]
  xtickNames = plt.setp(ax1, xticklabels=x_labels)
  plt.setp(xtickNames, rotation=45, fontsize=8)

  ax1.set_title('All %s Moss similarity' % (year_q))
  # resize
  plt.tight_layout()

  fig_dest = os.path.join(output_dir, '%s_all_moss.png' % (year_q))
  print "Saving aggregate figure", fig_dest
  fig.savefig(fig_dest)
  plt.close()
  pass

def make_moss_pair_graphs(output_dir, pair, pair_prefix):
  year_q = '_'.join([pair[:4], str(int(pair[4:6]))])
  posix_lookup = load_posix_to_commit_ind(output_dir, year_q)

  pair_output_dir = os.path.join(output_dir, pair_prefix)
  top_sims = load_top_sims_from_log(pair_output_dir, pair)
  uname_stats = {}
  for uname in top_sims:
    # get start and end posix times..
    uname_stats[uname] = []
    all_posix = posix_lookup[uname].keys()
    for posix_time in top_sims[uname]:
      other_path, token, percent_self, percent_other, _, _ = \
        top_sims[uname][posix_time]
      commit_num = posix_lookup[uname][int(posix_time)]

      # get posix and commit of other person
      other_name = '_'.join(other_path.split('_')[-3:])
      other_uname, other_posix = other_name.split('_')[:2]
      other_commit_num = posix_lookup[other_uname][int(other_posix)]

      uname_stats[uname].append(
        (int(posix_time), int(commit_num),
         int(other_posix), int(other_commit_num),
         int(token), float(percent_self), float(percent_other)))

  # top figure is time, bottom figure is commits
  # x is uname_1, y is uname_2
  fig_x, fig_y = 10, 6
  fig, ax_all = plt.subplots(2, 1, figsize=(fig_x, 2*fig_y))

  colors = ['b', 'g']
  uname_1, uname_2 = pair.split('_')
  stats = np.array(uname_stats[uname_1])
  times = stats[:,0]
  commits = stats[:,1]
  other_times = stats[:,2]
  other_commits = stats[:,3]
  tokens = stats[:,4]
  percents = stats[:,5]
  colors = np.zeros((len(stats),4))
  colors[:,2] = 1.0 # blue
  #colors[:,3] = percents/100
  colors[:,3] = 1

  ax_all[0].scatter(times, other_times, marker='o', c=colors, lw=0, s=tokens)
  ax_all[1].scatter(commits, other_commits, marker='o', c=colors, lw=0, s=tokens)

  stats = np.array(uname_stats[uname_2])
  times = stats[:,0]
  commits = stats[:,1]
  other_times = stats[:,2]
  other_commits = stats[:,3]
  tokens = stats[:,4]
  percents = stats[:,5]
  colors = np.zeros((len(stats),4))
  colors[:,1] = 1.0 # green
  colors[:,3] = 1

  ax_all[0].scatter(other_times, times, marker='o', c=colors, lw=0, s=tokens)
  ax_all[1].scatter(other_commits, commits, marker='o', c=colors, lw=0, s=tokens)

  # time
  start_1, end_1 = min(posix_lookup[uname_1].keys()), max(posix_lookup[uname_1].keys())
  start_2, end_2 = min(posix_lookup[uname_2].keys()), max(posix_lookup[uname_2].keys())
  incr = incr_length
  posix_range_1 = np.arange(start_1, end_1, step=incr)
  x_labels = [posix_to_datetime(posix_t) for posix_t in posix_range_1]
  posix_range_2 = np.arange(start_2, end_2, step=incr)
  y_labels = [posix_to_datetime(posix_t) for posix_t in posix_range_2]
  ax_all[0].xaxis.set_ticks(posix_range_1)
  xtickNames = plt.setp(ax_all[0], xticklabels=x_labels)
  plt.setp(xtickNames, rotation=45, fontsize=8)
  ax_all[0].yaxis.set_ticks(posix_range_2)
  ytickNames = plt.setp(ax_all[0], yticklabels=y_labels)
  plt.setp(ytickNames, rotation=45, fontsize=8)
  ax_all[0].set_xlabel('%s' % uname_1)
  ax_all[0].set_ylabel('%s' % uname_2)
  ax_all[0].set_title('Times')
  
  # commit
  max_sim_1 = len(posix_lookup[uname_1].keys())
  max_sim_2 = len(posix_lookup[uname_2].keys())
  ax_all[1].set_xlim((0, max_sim_1))
  ax_all[1].set_ylim((0, max_sim_2))
  ax_all[1].set_xlabel('%s commits' % uname_1)
  ax_all[1].set_ylabel('%s commits' % uname_2)
  ax_all[1].set_title('Commits')

  fig_dest = os.path.join(pair_output_dir, 'moss_%s.png' % pair)
  print "Saving pair %s figure" % pair, fig_dest
  fig.tight_layout()
  fig.suptitle('%s (b: %s, g: %s)' % (pair, uname_1, uname_2))
  fig.savefig(fig_dest)
  plt.close(fig)
