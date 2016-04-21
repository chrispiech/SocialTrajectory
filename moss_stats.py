from helper import *
from git_helper import *
from time import strptime
from datetime import datetime
from moss_tool import *
import matplotlib.colors as cl
import matplotlib.cm as cmx

add_str = ''
def make_moss_graphs(output_dir, year_q):
  # (other_username, int(tokens_matched),
  #          float(percent_self), float(percent_other))
  top_sims = load_top_sims_from_log(output_dir, year_q)
  get_top_commit_with_top_sim(top_sims)
  graph_percent_vs_token(output_dir, year_q, top_sims)

  # sims: token, percent
  # time_types: commit, posix
  # graph_similarities_over_time(output_dir, year_q, top_sims, 'token', 'posix')
  # graph_similarities_over_time(output_dir, year_q, top_sims, 'percent', 'posix')
  # graph_similarities_over_time(output_dir, year_q, top_sims, 'token', 'commit')
  # graph_similarities_over_time(output_dir, year_q, top_sims, 'percent', 'commit')
  same_plot = True
  # by commit
  thresh_unames_percent_commit = graph_all_similarities_over_time(output_dir, year_q, top_sims, 'percent', 'commit', same_plot)
  thresh_unames_token_commit = graph_all_similarities_over_time(output_dir, year_q, top_sims, 'token', 'commit', same_plot)
  print "intersection of percent v commit and token v commit:"
  intersect_uname_thresh(thresh_unames_percent_commit, thresh_unames_token_commit)

  # by posix
  thresh_unames_percent_posix = graph_all_similarities_over_time(output_dir, year_q, top_sims, 'percent', 'posix', same_plot)
  thresh_unames_token_posix = graph_all_similarities_over_time(output_dir, year_q, top_sims, 'token', 'posix', same_plot)
  print "intersection of percent v posix and token v posix:"
  intersect_uname_thresh(thresh_unames_percent_posix, thresh_unames_token_posix)

def intersect_uname_thresh(uname_thresh_1, uname_thresh_2):
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
Returns the number of times "online" appears in this list of usernames.
"""
def get_number_online(other_array):
  return ['online' in x for x in other_array].count(True)

"""
Calls get_number_online for all commits of each user in top_sims.
"""
def get_top_sims_online(top_sims):
  online_sims = {}
  for uname in top_sims:
    online_sims[uname] = get_number_online(\
        [top_sims[uname][posix_time][0] \
            for posix_time in top_sims[uname]])
  return online_sims

"""
Graphs the percent of tokens you share with another by the number of tokens.
Ignore the percent of tokens the other shares with you.
The later timestamps are colored darker.
"""
def graph_percent_vs_token(output_dir, year_q, top_sims):
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
  plt.rcParams['image.cmap'] = 'gray'
  sc = plt.scatter(tokens, percents, c=posix_times_adj, edgecolors='none')

  xlims = ax1.get_xlim()
  ax1.set_xlim(0, ax1.get_xlim()[1])
  ax1.set_ylim(percent_thresh, 100) # percent max is 100%
  ax1.set_title('(%s) Similarity percent vs tokens (Darker=later) (thresh=%d%%)' % (year_q, percent_thresh))
  ax1.set_xlabel('Tokens')
  ax1.set_ylabel('Percent similarity to current file')
  
  plt.tight_layout()
  fig_dest = os.path.join(output_dir, '%s_percent_vs_token_thresh_%d_%d.png' % (year_q, percent_thresh, token_thresh_max))
  print "Saving", fig_dest
  fig.savefig(fig_dest)
  plt.close()

"""
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
    if sim is 'token': sim_ind = 1
    elif sim is 'percent': sim_ind = 2
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
  x_labels = [(datetime.fromtimestamp(posix_t)).strftime('%m/%d %H:%M') \
                      for posix_t in posix_range]

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
    keep_inds = posix_times >= time_002 # cut off graph a bit
    posix_times_sort = posix_times[keep_inds]
    sims_sort = sims[keep_inds]
    online_bools_sort = online_bools[keep_inds]
    scatter_online = \
      [(sims_sort[i], posix_times_sort[i],
          i, datetime.fromtimestamp(posix_times_sort[i]).strftime('%m/%d %H:%M'))\
        for i in range(len(posix_times_sort)) \
        if online_bools_sort[i]]
    if scatter_online: # instead of online_sims, in case the online part happened before time_002.
      sims_online, posix_online, commits_online, date_times = zip(*scatter_online)

    plt_color = 'b' # in class
    if online_sims[uname] != 0: # this might mean that online sim before 2nd percentile
      plt_color = 'r' # online

    # single student plot
    if graph_indiv:
      fig = plt.figure()
      ax1 = plt.gca()
        
      if time_type is 'posix':
        plt.plot(posix_times_sort, sims_sort, color=plt_color)
        if scatter_online:
          plt.scatter(posix_online, sims_online, marker='o', c='r')
      elif time_type is 'commit':
        plt.plot(sims_sort, color=plt_color)
        if scatter_online:
          plt.scatter(commits_online, sims_online, marker='o', c='r')

      if sim is 'token':
        ax1.set_ylim(sim_min, sim_max)
      elif sim is 'percent':
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
      if sim is 'token':
        title_str = '%s (%s, %s)' % (title_str, sim_min, sim_max) 
      if sim is 'posix':
        title_str = '%s [%s-%s]' % (title_str, x_labels[0], x_labels[-1])
      elif sim is 'commit':
        title_str = '%s [%s max commits]' % (title_str, max_commits)
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
      ax_std.plot(posix_times_sort, sims_sort, color=plt_color)
      if scatter_online:
        ax_std.scatter(posix_online, sims_online, marker='o', c='r')
    elif time_type is 'commit':
      ax_std.plot(sims_sort, color=plt_color)
      if scatter_online:
        ax_std.scatter(commits_online, sims_online, marker='o', c='r')
    ax_std.set_title('%04d' % (uname_ind))
    plt.setp(ax_std,xticklabels=[],yticklabels=[])
    if sim is 'token':
      ax_std.set_ylim(sim_min, sim_max)
    elif sim is 'percent':
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

"""Plot black line on the aggregate student plot.
This marks the 95th percentile for similarities at any given timestep.
"""
def med_calc(times, sims, med_thresh=95):
  points_by_time = {}
  for i in range(len(times)):
    #   
    # for times, sims in points_std:
    #   for i in range(len(times)):
    time = times[i]
    if time not in points_by_time:
      points_by_time[time] = []
    points_by_time[time].append(sims[i])
  meds = []
  for time in points_by_time:
    sims_bound = np.percentile(np.array(points_by_time[time]), med_thresh)
    meds.append([time, sims_bound])
  meds_np = np.array(meds)
  meds_np = meds_np[meds_np[:,0].argsort()]
  print "loaded times for median."
  return meds_np

"""
Returns the coordinates of the username label if there
are similarities above the 95th percentile (from med_calc).
"""
def get_label_if_thresh(times, sims, med_lookup):
  times = np.array(times)
  sims = np.array(sims)
  above_thresh = [i for i in range(len(times)) if \
                        sims[i] > med_lookup[times[i]]]
  # almost everyone was above the threshold at some point,
  # so only count a significant number
  min_violations = 0.02
  if above_thresh and len(above_thresh)/float(len(times)) > min_violations:
    fraction_above = sims[above_thresh]/np.array([med_lookup[time] for time in times[above_thresh]])
    max_frac_ind = np.argmax(fraction_above)
    max_time, max_sim = times[above_thresh][max_frac_ind], sims[above_thresh][max_frac_ind]
    return max_time, max_sim, len(above_thresh)/float(len(times))
  return -1, -1, -1

"""
Basically the same as the regular similarities graph, but only scatter plot the times and token/percents.
Grouped into every 100 students as usual. Turn this off with same_plot=True.
Also graph a threshold indicating 95th or 99th percentile (specify this in
  the call to med_calc), and label the usernames that exceed that threshold.

Returns all usernames that are labeled, in thresh_unames (with the threshold).
"""
def graph_all_similarities_over_time(output_dir, year_q, top_sims, sim, time_type, same_plot=False):
  print "%s: Similarities by %s over %s, scatter all on one graph" % (year_q, sim, time_type)
  all_timeseries = {}
  all_times_sims = []

  # parse all top sims and get data
  print "Parsing all top sims..."
  max_commits = 0
  for uname in top_sims:
    if sim is 'token': sim_ind = 1
    elif sim is 'percent': sim_ind = 2
    posix_times = top_sims[uname].keys()
    posix_times.sort()
    temp_list = [(int(posix_times[i]),
                  top_sims[uname][posix_times[i]][sim_ind],
                 int('online' in top_sims[uname][posix_times[i]][0]), i) \
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
  time_002, time_100 = np.percentile(all_posix_times_np, [2,100])
  sim_min, sim_max = np.percentile(all_sims_np, [0,100])
  incr = (time_100 - time_002)/10
  posix_range = np.arange(time_002, time_100, step=incr)
  x_labels = [(datetime.fromtimestamp(posix_t)).strftime('%m/%d %H:%M') \
                      for posix_t in posix_range]

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

  #### graph all students
  thresh_unames = []
  uname_ind = 0
  for uname in all_timeseries:
    if uname_ind % 50 == 1: print uname_ind
    other_names, time_array = all_timeseries[uname]
    posix_times = time_array[:,0]
    sims = time_array[:,1]
    online_bools = time_array[:,2].astype(bool)
    keep_inds = posix_times >= time_002 # cut off graph a bit
    posix_times_sort = posix_times[keep_inds]
    sims_sort = sims[keep_inds]
    online_bools_sort = online_bools[keep_inds]

    

    # add label
    max_ind = np.argmax(sims_sort ** 2 + np.array(range(len(sims_sort))) ** 2)
    max_sim, max_posix = sims_sort[max_ind], posix_times_sort[max_ind]

    # online/offline
    scatter_online = \
      [(sims_sort[i], posix_times_sort[i],
          i, datetime.fromtimestamp(posix_times_sort[i]).strftime('%m/%d %H:%M'))\
        for i in range(len(posix_times_sort)) \
        if online_bools_sort[i]]
    scatter_offline = \
      [(sims_sort[i], posix_times_sort[i],
          i, datetime.fromtimestamp(posix_times_sort[i]).strftime('%m/%d %H:%M'))\
        for i in range(len(posix_times_sort)) \
        if not online_bools_sort[i]]
    if scatter_online: # instead of online_sims, in case the online part happened before time_002.
      sims_online, posix_online, commits_online, date_times = zip(*scatter_online)
    if scatter_offline:
      sims_offline, posix_offline, commits_offline, date_times = zip(*scatter_offline)

    # all student plot
    plt_ind = uname_ind/100
    if same_plot:
      plt_ind = 0
    plt.figure(plt_ind)
    fig_all[plt_ind].hold(True)
    ax_std = ax_all[plt_ind]
    points_std = points_all[plt_ind]
    if time_type is 'posix':
      max_posix, max_sim, thresh_perc = get_label_if_thresh(posix_times_sort, sims_sort, med_lookup)
      if max_sim != -1:
        ax_std.annotate(uname[6:], xy=(max_posix, max_sim), size=10, textcoords='data')
        thresh_unames.append((uname[6:], thresh_perc))
      if scatter_online:
        ax_std.scatter(posix_online, sims_online, marker='.',facecolor='r', edgecolor='r',lw = 0)
      if scatter_offline:
        ax_std.scatter(posix_offline, sims_offline, c='b', edgecolor='b', alpha=0.08)
      points_std.append([posix_times_sort, sims_sort])
    elif time_type is 'commit':
      max_ind, max_sim, thresh_perc = get_label_if_thresh(range(len(sims_sort)), sims_sort, med_lookup)
      if max_sim != -1:
        ax_std.annotate(uname[6:], xy=(max_ind, max_sim), size=10, textcoords='data')
        thresh_unames.append((uname[6:], thresh_perc))
      if scatter_online:
        ax_std.scatter(commits_online, sims_online, c='r', lw=0)
      if scatter_offline:
        ax_std.scatter(commits_offline, sims_offline, marker='.',c='b', lw=0,alpha=0.08)
      points_std.append([range(len(sims_sort)), sims_sort])

    uname_ind += 1

  # format and save all student plots
  title_str = '%s top similarity (%s) over %s' % (year_q, sim, time_type)
  if sim is 'token':
    title_str = '%s (%s, %s)' % (title_str, sim_min, sim_max) 
  if time_type is 'posix':
    title_str = '%s [%s-%s]' % (title_str, x_labels[0], x_labels[-1])
  elif time_type is 'commit':
    title_str = '%s [%s max commits]' % (title_str, max_commits)
  all_fig_dest_prefix = '%s_aggr_%s_%s' % (year_q, time_type, sim)
  if sim is 'token':
    all_fig_dest_prefix += '_%s_%s' % (sim_min, sim_max)

  for plt_ind in range(num_unames/100+1):
    plt.figure(plt_ind)
    ax_std = ax_all[plt_ind]
    if sim is 'token':
      ax_std.set_ylim(sim_min, sim_max)
    elif sim is 'percent':
      ax_std.set_ylim(0,100)
    if time_type is 'posix':
      ax_std.set_xlim(time_002, time_100)
      xtickNames = plt.setp(ax_std, xticklabels=x_labels)
      plt.setp(xtickNames, rotation=45, fontsize=8)
      ax_std.plot(med_times[::5], med_sims[::5], c='k')
    elif time_type is 'commit':
      ax_std.set_xlim(0, max_commits)
      ax_std.plot(med_times, med_sims, c='k')

    plt.figure(plt_ind)
    title_str_ind = '%s (Part %s)' % (title_str, plt_ind)
    if same_plot:
      title_str_ind = '%s (all)' % (title_str)
    ax_all[plt_ind].set_title(title_str_ind)
    ax_all[plt_ind].set_xlabel(time_type)
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
    x_scatter, y_scatter, z_colors = zip(*all_times)
    
    print "Making plot."
    fig = plt.figure(figsize=(7,max(int(len(y_labels)/7), 7)))
    ax1 = plt.gca()
    marker_size = 100
    print "Graphing scatter."
    plt.rcParams['image.cmap'] = 'gray'
    sc = plt.scatter(x_scatter, y_scatter, marker_size, c=z_colors)
    plt.colorbar()

    # put students on y axis
    #y_real_labels = [''] +  y_labels + ['']
  
    ax1.set_ylim(0, len(y_labels)-1)
    ax1.set_yticks(np.arange(len(y_labels)))
    ytickNames = plt.setp(ax1, yticklabels=y_labels)
    plt.setp(ytickNames, fontsize=8)

    # put times on x axis
    xlims = ax1.get_xlim()
    incr = (xlims[1] - xlims[0])/10
    posix_range = np.arange(xlims[0], xlims[1], step=incr)
    x_labels = [(datetime.fromtimestamp(posix_t)).strftime('%m/%d %H:%M') \
                    for posix_t in posix_range]
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
    x_scatter, y_scatter, gray_colors = zip(*all_times)
    
    marker_size = 100
    uname_color = uname_scalarMap.to_rgba(y_ref_dict[uname])
    uname_color_norm = [float(0.5*uc)/max(uname_color) for uc in uname_color]
    colors=[map(lambda x: 0.25+x*gc, uname_color_norm) \
                for gc in gray_colors]
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
  x_labels = [(datetime.fromtimestamp(posix_t)).strftime('%m/%d %H:%M') \
                  for posix_t in posix_range]
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
