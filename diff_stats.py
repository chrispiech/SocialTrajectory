from helper import *
from git_helper import *
from moss_tool import *
from diff_tool import *
import matplotlib.colors as cl
import matplotlib.cm as cmx

INSERT_TYPE, DELETE_TYPE = 1, 2
def plot_diffs(output_dir, year_q):
  #plot_diffs_over_time(output_dir, '2012_1')
  #plot_diff_hist(output_dir, year_q)
  plot_consecline_stats(output_dir, year_q, use_mt=False)

  for diff_type in [INSERT_TYPE, DELETE_TYPE]:
    top_sims = load_top_sims_from_log(output_dir, year_q, use_diff=diff_type)
    plot_diff_moss(output_dir, year_q, top_sims, diff_type=diff_type)

"""
Plots something similar to the regular moss plot.

This one or token one is the best one.
http://52.37.79.5:8000/diff_2012_1_aggr_commit_other_Final_rank_norm.png
"""
line_thresh = 100 # if below this threshold, don't plot.
def plot_diff_moss(output_dir, year_q, top_sims, diff_type=0):
  # don't use grades yet thanks
  exam_grades = load_exam_grades(output_dir, year_q)
  mt_gr, f_gr = get_graderank_dict(exam_grades)
  posix_lookup = load_posix_to_commit_ind(output_dir, year_q)

  use_other = True
  graph_options = list(itertools.product((True, False), (True, False)))
  axes_options = list(itertools.product(('percent', 'token'), ('commit', 'posix')))
  if diff_type == INSERT_TYPE:
    add_str = '_insert'
  elif diff_type == DELETE_TYPE:
    add_str = '_delete'
  for normalize_flag, use_grades in graph_options:
    for sim_type, time_type in axes_options:
      for use_mt, use_rank in graph_options:
        # loading
        diff_stats = {}
        all_diff_stats = []
        all_diff_str_stats = []
        for uname in top_sims:
          uname_stats = []
          uname_str_stats = []
          all_posix = posix_lookup[uname].keys()
          start_posix, end_posix, num_commits = min(all_posix), max(all_posix), len(all_posix)
          for posix_time in top_sims[uname]:
            commit_num = posix_lookup[uname][int(posix_time)]
            for line in top_sims[uname][posix_time]:
              name_other, token, percent_self, percent_other, _, commit_hash = \
                  top_sims[uname][posix_time][line]
              num_lines = line_range(line)
              if num_lines < line_thresh: continue
              mt_gr_uname, f_gr_uname = (1.0,1.0), (1.0,1.0)
              if use_grades:
                if use_mt:
                  if uname not in mt_gr:
                    continue
                  else:
                    mt_gr_uname = mt_gr[uname]
                else:
                  if uname not in f_gr:
                    continue
                  else:
                    f_gr_uname = f_gr[uname]
              uname_stats.append(
                  (int(posix_time), int(commit_num),
                   start_posix, end_posix, num_commits,
                   int(token), float(percent_self), float(percent_other),
                   mt_gr_uname[0], mt_gr_uname[1],
                   f_gr_uname[0], f_gr_uname[1],
                   int('online' in name_other),
                   num_lines))
              commit_name = '%s_%s_%s' % (uname, posix_time, commit_hash)
              uname_str_stats.append((commit_name, line))
          diff_stats[uname] = uname_stats
          all_diff_stats += uname_stats
          all_diff_str_stats += uname_str_stats
        
        #all_diff_np = np.array(all_diff_stats, dtype=dtype)
        print "all elts", len(all_diff_stats)
        all_diff_np = np.array(all_diff_stats)
        all_diff_str_np = np.array(all_diff_str_stats)

        # indexing variables
        posix_ind, commit_ind = 0, 1
        start_ind, end_ind, length_ind = 2, 3, 4
        token_ind, self_ind, other_ind = 5, 6, 7
        mt_g_ind, mt_r_ind = 8, 9
        f_g_ind, f_r_ind = 10, 11
        online_ind = 12
        lr_ind = 13
        # str indexing variables
        commit_name, line_str = 0, 1

        ### plotting
        max_lr = np.amax(all_diff_np[:,lr_ind])
        online_inds = np.nonzero(all_diff_np[:,online_ind])[0]
        offline_inds = np.nonzero(1 - all_diff_np[:,online_ind])[0]
        all_online_np = all_diff_np[online_inds,:]
        all_offline_np = all_diff_np[offline_inds,:]
        all_online_str_np = all_diff_str_np[online_inds,:]
        all_offline_str_np = all_diff_str_np[offline_inds,:]
        all_percent_min = np.amin(all_diff_np[:,self_ind])
        all_percent_max = np.amax(all_diff_np[:,self_ind])
        incr = incr_length
        posix_range = np.arange(all_start_time, all_end_time, step=incr)
        xlabels = [posix_to_time(posix_t) for posix_t in posix_range]
        fig = plt.figure(figsize=(10,10))
        ax = plt.gca()
        if sim_type == 'percent':
          # create addtl figure with y-axis as line number
          fig_lr = plt.figure(figsize=(10,10))
          ax_lr = plt.gca()
        m = set_colormap([0.0, 1.0])
        msize = 100
        for online_ind in [0,1]:
          all_np = [all_offline_np, all_online_np][online_ind]
          all_str_np = [all_offline_str_np, all_online_str_np][online_ind]
          c = ['b', 'r'][online_ind]
          marker = ['o', 'o'][online_ind]
          lrs = all_np[:,lr_ind]
          lr_scale = np.log10(lrs)/(np.log10(float(max_lr))+np.log10(line_thresh))
          #lr_scale = all_np[:,lr_ind]/float(max_lr)

          if sim_type == 'token':
            sims = all_np[:,token_ind]
          else: # percent
            sims = all_np[:,other_ind]
          if time_type == 'commit':
            times = all_np[:,commit_ind]
            if normalize_flag:
              time_lens = all_np[:,length_ind]
              norm_gran = 3 # decimal granularity
              times = np.around(times/time_lens, decimals=norm_gran)
          else:
            times = all_np[:,posix_ind]
          if use_grades:
            if use_mt:
              if use_rank:
                grades = all_np[:,mt_r_ind].flatten()
              else:
                grades = all_np[:,mt_g_ind].flatten()
            else:
              if use_rank:
                grades = all_np[:,f_r_ind].flatten()
              else:
                grades = all_np[:,f_g_ind].flatten()
            c = m.to_rgba(grades) # alpha defaults to 1
            if online_ind == 0: # offline
              c[:,-1] = lr_scale # set alpha to line range scale
          if online_ind == 0:
            #ax.scatter(times, sims, marker=marker, color=c, lw=0, alpha=0.5,
            ax.scatter(times, sims, marker=marker, color=c, lw=0,
                      s=msize*lr_scale)
          else:
            ax.scatter(times, sims, marker=marker, color=c, s=msize*lr_scale,edgecolors='k')

          # print stuff
          if use_other and sim_type == 'percent' \
              and time_type == 'commit' and normalize_flag \
              and use_grades and not use_mt and use_rank:
            sim_thresh = 20
            large_inds = np.nonzero(sims > 20)
            display_text_graph(times, sims, grades, lrs,
                               all_np, all_str_np,
                               sort_by_x=False)
            # print "Above thresholds sim other percent: %s, linecount: %s (norm: %s, online: %s)" % (sim_thresh, line_thresh, normalize_flag, online_ind)
            # print np.array_str(np.array((times[large_inds], sims[large_inds], grades[large_inds])).T, precision=3, suppress_small=True)
            
          # add the extra graph
          if sim_type == 'percent':
            sims_norm = sims/100 # one way
            sims_norm = (sims - all_percent_min)/all_percent_max
            if use_grades:
              c_lr = m.to_rgba(grades)
              c_lr[:,-1] = sims_norm # alpha is sims
              c_lr[:,-1] = 0.8
            else:
              if online_ind == 0:
                c_lr = np.vstack((np.zeros(sims.shape),
                                  np.zeros(sims.shape),
                                  np.ones(sims.shape),
                                  sims_norm))
              else:
                c_lr = np.vstack((np.ones(sims.shape),
                                  np.zeros(sims.shape),
                                  np.zeros(sims.shape),
                                  sims_norm))
            if online_ind == 0:
              ax_lr.scatter(times, lrs, marker=marker,color=c_lr,
                  s=msize*sims_norm, lw=0)
            else:
              ax_lr.scatter(times, lrs, marker=marker, color=c_lr,
                  s=msize*sims_norm, edgecolors='k')

        # add labels and set axes.
        title_str = "%s diff similarities (%s) over %s" % (year_q, sim_type, time_type)
        if sim_type == 'percent' and use_other:
          title_str = "%s diff similarities (other) over %s" % (year_q, time_type)
        ax.set_title(title_str)
        ax.set_xlabel(time_type)
        if sim_type == 'percent':
          ax_lr.set_title(title_str)
          ax_lr.set_xlabel(time_type)
        if time_type == 'commit':
          ax.set_xlim((0, ax.get_xlim()[1]))
          if normalize_flag:
            ax.set_xlim((0.0, 1.0))
            ax.set_xlabel('commit (normalized')
          if sim_type == 'percent':
            ax_lr.set_xlim((0, ax.get_xlim()[1]))
            if normalize_flag:
              ax_lr.set_xlim((0.0, 1.0))
              ax_lr.set_xlabel('commit (normalized')
        else: # posix
          ax.set_xlim(all_start_time, all_end_time)
          ax.set_xticks(posix_range)
          ax.set_xticklabels(xlabels, rotation=45, fontsize=8)
          if sim_type == 'percent':
            ax_lr.set_xlim(all_start_time, all_end_time)
            ax_lr.set_xticks(posix_range)
            ax_lr.set_xticklabels(xlabels, rotation=45, fontsize=8)

        ax.set_ylabel(sim_type)
        if sim_type == 'token':
          ax.set_ylim((0, ax.get_ylim()[1]))
        else: # percent
          ax.set_ylim((0, 100))
          ax_lr.set_ylabel('Line numbers')
          ax_lr.set_ylim((line_thresh, ax_lr.get_ylim()[1]))
          ax_lr.set_yscale('log')

        if use_grades:
          fig.tight_layout()
          cbar_ax = fig.add_axes([0.95, 0.07, 0.02, 0.8])
          cbar_ax.tick_params()#labelsize=tick_fs)
          fig.colorbar(m, cax=cbar_ax)
          if sim_type == 'percent':
            fig_lr.tight_layout()
            cbar_ax_lr = fig_lr.add_axes([0.95, 0.07, 0.02, 0.8])
            cbar_ax_lr.tick_params()#labelsize=tick_fs)
            fig_lr.colorbar(m, cax=cbar_ax_lr)
            

        # figure out prefix name.
        fig_prefix = 'diff%s_%s_aggr_%s_%s' % (add_str, year_q, time_type, sim_type)
        if sim_type == 'percent' and use_other:
          fig_prefix = 'diff%s_%s_aggr_%s_other' % (add_str, year_q, time_type)
          
        if use_grades:
          if use_mt:
            fig_prefix += '_MT'
          else:
            fig_prefix += '_Final'
          if use_rank:
            fig_prefix += '_rank'
          else:
            fig_prefix += '_abs'
        if time_type == 'commit':
          if normalize_flag:
            fig_prefix += '_%s' % 'norm'
        fig_dest = os.path.join(output_dir, '%s.png' % fig_prefix)
        print "Saving", fig_dest
        fig.savefig(fig_dest)
        plt.close(fig)

        if sim_type == 'percent':
          fig_prefix += '_linerange'
          fig_lr_dest = os.path.join(output_dir, '%s.png' % fig_prefix)
          print "Saving", fig_lr_dest
          fig_lr.savefig(fig_lr_dest)
          plt.close(fig_lr)


        if not use_grades: break

"""
Plots line count vs commit, with sizing for similarity.
This is similar to the lecture plots.
"""
def plot_diff_sims(output_dir, year_q, top_sims):
  posix_lookup = load_posix_to_commit_ind(output_dir, year_q)

def plot_consecline_stats(output_dir, year_q, use_mt=True, rank=True):
  use_trajecs = True
  consec_stats = load_consecline_stats(output_dir, year_q)
  exam_grades = load_exam_grades(output_dir, year_q)
  if use_mt:
    graderanks, _ = get_graderank_dict(exam_grades)
  else:
    _, graderanks = get_graderank_dict(exam_grades)
  all_inserts, all_deletes = [], []
  line_thresh = 50
  for uname in consec_stats:
    if uname not in graderanks: continue
    if not rank:
      grade = graderanks[uname][0]
    else:
      grade = graderanks[uname][1]
    posix_times = consec_stats[uname].keys()
    posix_times.sort()
    temp_list = [(posix_times[i],
                  consec_stats[uname][posix_times[i]][0][j],
                  i,
                  float(i)/len(posix_times),
                  grade,
                  int(uname)) \
                      for i in range(len(posix_times)) \
                      for j in range(len(consec_stats[uname][posix_times[i]][0]))\
                        if consec_stats[uname][posix_times[i]][0] >= line_thresh]
    all_inserts += temp_list
    temp_list = [(posix_times[i],
                  consec_stats[uname][posix_times[i]][1][j],
                  i,
                  float(i)/len(posix_times),
                  grade,
                  int(uname)) \
                      for i in range(len(posix_times)) \
                      for j in range(len(consec_stats[uname][posix_times[i]][1]))\
                        if consec_stats[uname][posix_times[i]][1] >= line_thresh]
    all_deletes += temp_list
  all_inserts_np = np.array(all_inserts)
  all_deletes_np = np.array(all_deletes)

  #### histogram first.
  bin_steps=20
  bins = np.linspace(np.round(np.log10(line_thresh)),
                     np.round(np.log10(np.amax(all_inserts_np[:,1]))),
                     num=bin_steps)
  insert_hist, insert_bin_edges = np.histogram(all_inserts_np[:,1],
      bins=10**bins)
  delete_hist, delete_bin_edges = np.histogram(all_deletes_np[:,1],
      bins=10**bins)

  num_plots = 2
  fig_x, fig_y = 8, 6
  fig, ax_all = plt.subplots(num_plots, 1, figsize=(fig_x, num_plots*fig_y))
  i_ind, d_ind = 0, 1
  #ax_all[i_ind].scatter(insert_bin_edges[1:], insert_hist, c='b')
  n, bins, patches = ax_all[i_ind].hist(all_inserts_np[:,1],bins=insert_bin_edges,
                log=True,alpha=0.5,fill=True,histtype='bar')
  print "insert bin edges", bins, insert_hist
  #rects = ax_all[i_ind].bar(insert_bin_edges[:-1], insert_hist, color='b')
  #rects = ax_all[i_ind].bar(bins, np.log(insert_hist))
  ax_all[i_ind].set_title('Insertions')
  #ax_all[i_ind].set_xticks(insert_bin_edges)
  #ax_all[d_ind].scatter(delete_bin_edges[1:], delete_hist, c='g')
  #rects = ax_all[d_ind].bar(delete_bin_edges[:-1], delete_hist,
  #rects = ax_all[d_ind].bar(bins, np.log(insert_hist))
  n, bins, patches = ax_all[d_ind].hist(all_deletes_np[:,1],bins=delete_bin_edges,
                log=True,alpha=0.5,fill=True,histtype='bar')
  ax_all[d_ind].set_title('deletions')
  ax_all[d_ind].set_xticks(np.linspace(0,1000,11))
  fig.suptitle('Insertions and deletions of consecutive lines')
  fpath = os.path.join(output_dir, '%s_conseclines_hist.png' % year_q)
  print "Saving file", fpath
  fig.savefig(fpath)
  plt.close(fig)

  ### Over time
  for time_type in ['posix', 'commit', 'norm']:
    insert_thresh_inds = np.nonzero(all_inserts_np[:,1] >= line_thresh)[0]
    inserts_np = all_inserts_np[insert_thresh_inds,:]
    delete_thresh_inds = np.nonzero(all_deletes_np[:,1] >= line_thresh)[0]
    deletes_np = all_deletes_np[delete_thresh_inds,:]
    print "num", inserts_np.shape, deletes_np.shape
    insert_times = inserts_np[:,0] # default is posix
    delete_times = deletes_np[:,0]
    if time_type is 'commit':
      insert_times = inserts_np[:,2]
      delete_times = deletes_np[:,2]
    elif time_type is 'norm':
      insert_times = inserts_np[:,3]
      delete_times = deletes_np[:,3]
    insert_lines = inserts_np[:,1]
    delete_lines = deletes_np[:,1]
    insert_c = inserts_np[:,4]
    delete_c = deletes_np[:,4]

    num_plots = 2
    fig_x, fig_y = 8, 6
    fig, ax_all = plt.subplots(num_plots, 1, figsize=(fig_x, num_plots*fig_y))
    i_ind, d_ind = 0, 1
    m = set_colormap([0.0, 1.0])
    if use_trajecs:
      for uname in consec_stats:
        uname = int(uname)
        uname_inds = np.nonzero(inserts_np[:,5] == uname)[0]
        if len(uname_inds):
          uname_insert_c = list(m.to_rgba(insert_c[uname_inds][0]))
          uname_insert_c[-1] = 0.7
          ax_all[i_ind].plot(insert_times[uname_inds], insert_lines[uname_inds],
                             linestyle='-',
                              c=uname_insert_c)
        uname_inds = np.nonzero(deletes_np[:,5] == uname)[0]
        if len(uname_inds):
          uname_delete_c = list(m.to_rgba(delete_c[uname_inds][0]))
          uname_delete_c[-1] = 0.7
          ax_all[d_ind].plot(delete_times[uname_inds], delete_lines[uname_inds],
                             linestyle='-',
                              c=uname_delete_c)
    ax_all[i_ind].scatter(insert_times, insert_lines,
                          c=insert_c, lw=0, alpha=0.7)
    ax_all[i_ind].set_title('Insertions (paste or edits)')
    ax_all[d_ind].scatter(delete_times, delete_lines,
                          c=delete_c, lw=0, alpha=0.7)
    ax_all[d_ind].set_title('deletions (deletes)')

    if time_type is 'posix':
      ax_all[i_ind].plot(insert_times[uname_inds], insert_lines[uname_inds],
                         linestyle='-',
                          c=insert_c, lw=0, alpha=0.7)
      incr = incr_length
      posix_range = np.arange(all_start_time, all_end_time, step=incr_length)
      x_labels = [posix_to_time(posix_t) for posix_t in posix_range]
      for ax_std in ax_all:
        ax_std.set_xlim(all_start_time, all_end_time)
        ax_std.set_xticks(posix_range)
        ax_std.set_xticklabels(x_labels, rotation=45, fontsize=8)
    elif time_type is 'commit':
      for ax_std in ax_all:
        ax_std.set_xlim(0, ax_std.get_xlim()[1])
        ax_std.set_xlabel('Number of commits')
    elif time_type is 'norm':
      for ax_std in ax_all:
        ax_std.set_xlim(0, 1.0)
        ax_std.set_xlabel('Normalized % completion')
    for ax_std in ax_all: # have all start from 0
      #ax_std.set_yscale('log')
      ax_std.set_ylim((line_thresh, max(np.amax(insert_lines), np.amax(delete_lines))))
      # ax_std.set_ylim(0, ax_std.get_ylim()[1])
      ticks = ax_std.get_yticks()
      print ticks
      ax_std.set_yticklabels(ticks)
      # reg_tick_labels = (10**np.array(ticks)).astype(int)
      # ax_std.set_yticklabels(reg_tick_labels)
      ax_std.set_ylabel('log of consecutive lines')


    fig.suptitle('Cut/paste over time')
    fpath = os.path.join(output_dir, '%s_conseclines_vs_%s.png' % (year_q, time_type))
    print "Saving file", fpath
    fig.savefig(fpath)
    plt.close(fig)

def plot_diffs_over_time(output_dir, year_q):
  all_diffs = load_diff_stats(output_dir, year_q)
  all_diffs_list = []
  all_timeseries = {}
  max_commits = 0
  for uname in all_diffs:
    posix_times = all_diffs[uname].keys()
    posix_times.sort()
    temp_list = [(int(posix_times[i]),
                  i, 
                  all_diffs[uname][posix_times[i]][0],
                  all_diffs[uname][posix_times[i]][1],
                  all_diffs[uname][posix_times[i]][2]) \
                for i in range(len(posix_times))]
    all_diffs_list += temp_list
    all_timeseries[uname] = np.array(temp_list)
    max_commits = max(max_commits, len(temp_list))

  all_diffs_np = np.array(all_diffs_list)
  all_times_np = all_diffs_np[:,0]
  all_commits_np = all_diffs_np[:,1]
  all_filecounts_np = all_diffs_np[:,2]
  fc_min, fc_max = np.percentile(all_filecounts_np, [0,100])
  all_insertions_np = all_diffs_np[:,3]
  all_deletions_np = all_diffs_np[:,4]

  max_commits = np.amax(all_commits_np)
  insertions_bins = np.percentile(all_insertions_np, [10,50,70,80,90,95,99,100])
  deletions_bins = np.percentile(all_deletions_np, [10,50,70,80,90,95,99,100])
  print "insertion", insertions_bins
  print "deletion", deletions_bins

  # med calc for black line stuff
  temp_np = med_calc(all_commits_np, all_filecounts_np,med_thresh=99)
  med_times_fc, meds_fc = temp_np[:,0], temp_np[:,1]
  temp_np = med_calc(all_commits_np, all_insertions_np,med_thresh=99)
  med_times_i, meds_i = temp_np[:,0], temp_np[:,1]
  temp_np = med_calc(all_commits_np, all_deletions_np,med_thresh=99)
  med_times_d, meds_d = temp_np[:,0], temp_np[:,1]
  
  num_plots = 3 # 0: file counts, 1: insertions, 2: deletions
  fig_x, fig_y = 40, 10
  fig, ax_all = plt.subplots(num_plots, 1, figsize=(fig_x, num_plots*fig_y))
  fc_ind, i_ind, d_ind = 0, 1, 2
  thresh_unames = [[],[],[]]
  for uname in all_timeseries:
    time_array, commit_strs = all_timeseries[uname]
    posix_times = time_array[:,0]
    commits = time_array[:,1]
    filecounts = time_array[:,2]
    insertions = time_array[:,3]
    deletions = time_array[:,4]

    # file counts
    ax_std = ax_all[fc_ind]
    ax_std.scatter(commits, filecounts, c='b', edgecolors='none')
    max_ind, max_sim, thresh_perc = \
      get_label_if_thresh(commits, filecounts,
        dict([(med_times_fc[i], meds_fc[i]) for i in range(len(med_times_fc))]))
    if max_sim != -1:
      ax_std.annotate(uname[6:], xy=(max_ind, max_sim), size=10, textcoords='data')
      thresh_unames[fc_ind].append((uname[6:], thresh_perc))

    # insertions
    ax_std = ax_all[i_ind]
    ax_std.scatter(commits, insertions, c='b', edgecolors='none')
    max_ind, max_sim, thresh_perc = \
      get_label_if_thresh(commits, insertions,
        dict([(med_times_i[i], meds_i[i]) for i in range(len(med_times_i))]))
    if max_sim != -1:
      ax_std.annotate(uname[6:], xy=(max_ind, max_sim), size=10, textcoords='data')
      thresh_unames[i_ind].append((uname[6:], thresh_perc))
    
    # deletions
    ax_std = ax_all[d_ind]
    ax_std.scatter(commits, deletions, c='b', edgecolors='none')
    max_ind, max_sim, thresh_perc = \
      get_label_if_thresh(commits, deletions,
        dict([(med_times_d[i], meds_d[i]) for i in range(len(med_times_d))]))
    if max_sim != -1:
      ax_std.annotate(uname[6:], xy=(max_ind, max_sim), size=10, textcoords='data')
      thresh_unames[d_ind].append((uname[6:], thresh_perc))
    
  ax_fc = ax_all[fc_ind]
  ax_fc.plot(med_times_fc, meds_fc, c='k')
  ax_fc.set_xlabel('Commits')
  ax_fc.set_ylabel('Files modified')
  ax_fc.set_title('Files modified vs Commits')

  ax_i = ax_all[i_ind]
  ax_i.plot(med_times_i, meds_i, c='k')
  #ax_i.set_yticks(insertions_bins)
  ax_i.set_yscale('log')
  ax_i.set_xlim((0,max_commits))
  ax_i.set_xlabel('Commits')
  ax_i.set_ylabel('Lines inserted')
  ax_i.set_title('Lines inserted vs Commits')

  ax_d = ax_all[d_ind]
  ax_d.plot(med_times_d, meds_d, c='k')
  #ax_d.set_yticks(deletions_bins)
  ax_d.set_yscale('log')
  ax_d.set_xlim((0,max_commits))
  ax_d.set_xlabel('Commits')
  ax_d.set_ylabel('Lines deleted')
  ax_d.set_title('Lines deleted vs Commits')

  fig_dest = os.path.join(output_dir, '%s_fc_insertions_deletions.png' % year_q)
  print "Saving insertions and deletions figure", fig_dest
  fig.savefig(fig_dest)
  plt.close(fig)

"""
Histogram of data with bin size bin_size.

Finds and returns a spline function spline_f of the data.
  The knot factor is 5 for insertions (hardcoded)
                  and 6 for deletions.

Returns critical points of the spline function, where a 
  zero first-derivative is those that fall below the deriv_thresh threshold.
"""
def hist_and_split(data, insert=True, bin_size=10, deriv_thresh=0.1):
  hist, bin_edges = np.histogram(data,
        bins=range(0,np.amax(data),bin_size))
  nz_hist_ind = np.nonzero(hist)
  nz_hist_log = np.log10(hist[nz_hist_ind][1:]) # ignore "0-bin_size" bin
  nz_bins_log = np.log10(bin_edges[nz_hist_ind][1:]) # ignore "0-bin_size" bin

  knot_factor = 33
  if insert: knot_factor = 20

  spline_f = UnivariateSpline(nz_bins_log, nz_hist_log,
                              s=len(nz_hist_log)/knot_factor)

  newx = np.linspace(min(nz_bins_log), max(nz_bins_log), num=10000)
  derivs = spline_f(newx, nu=1) # find the first derivative of newx points
  critpoint_inds = np.nonzero(np.abs(derivs) < deriv_thresh)
  cp_counts, cp_bins = np.histogram(newx[critpoint_inds])
  nz_cp_bins = cp_bins[cp_counts.nonzero()]
  nz_cp_counts = cp_counts[cp_counts.nonzero()]
  if insert: print "insert"
  else: print "delete"
  print nz_cp_bins
  
  critpoint_x = 0
  if len(nz_cp_bins) > 0:
    critpoint_x = nz_cp_bins[1]
  critpoint_y = spline_f(critpoint_x, nu=1)
  print "critpoint", critpoint_x, critpoint_y, spline_f(critpoint_x)
  
  return nz_hist_log, nz_bins_log, spline_f, critpoint_x
  

"""
Plots the file counts, insertions, and deletions as a histogram.
From this, fits a curve to the insertions/deletions.
Record the insert/deletes that are over a given threshold (the
  "critical point" in each fitted curve) and ...
Writes the commits that are above this insert/delete critical point.
"""
def plot_diff_hist(output_dir, year_q):
  all_diffs = load_diff_stats(output_dir, year_q)
  all_diffs_list = []
  all_timeseries = {}
  max_commits = 0
  for uname in all_diffs:
    posix_times = all_diffs[uname].keys()
    posix_times.sort()
    temp_list = [(int(posix_times[i]),
                  i, 
                  all_diffs[uname][posix_times[i]][0],
                  all_diffs[uname][posix_times[i]][1],
                  all_diffs[uname][posix_times[i]][2]) \
                for i in range(len(posix_times))]
    commit_list = [all_diffs[uname][posix_times[i]][3] \
                for i in range(len(posix_times))]
    all_diffs_list += temp_list
    all_timeseries[uname] = [np.array(temp_list), commit_list]
    max_commits = max(max_commits, len(temp_list))

  all_diffs_np = np.array(all_diffs_list)
  all_times_np = all_diffs_np[:,0]
  all_commits_np = all_diffs_np[:,1]
  all_filecounts_np = all_diffs_np[:,2]
  fc_min, fc_max = np.percentile(all_filecounts_np, [0,100])
  all_insertions_np = all_diffs_np[:,3]
  all_deletions_np = all_diffs_np[:,4]
  insert_min_max = np.percentile(all_insertions_np, [0,99])
  delete_min_max = np.percentile(all_deletions_np, [0,99])
  id_min = min(insert_min_max[0], delete_min_max[0])
  id_max = max(insert_min_max[1], delete_min_max[1])
  print "fc bounds", fc_min, fc_max
  print "insert delete bounds", id_min, id_max
  print "max delete bound", np.percentile(all_deletions_np, [99, 100])
  print "max insert bound", np.percentile(all_insertions_np, [99, 100])

  insertions_bins = np.percentile(all_insertions_np, [10,50,70,80,90,95,99,100])
  deletions_bins = np.percentile(all_deletions_np, [10,50,70,80,90,95,99,100])

  num_plots = 3 # 0: file counts, 1: insertions (g), 2: deletions (r)
  fig_x, fig_y = 8, 6
  fig, ax_all = plt.subplots(num_plots, 1, figsize=(fig_x, num_plots*fig_y))
  fc_ind, i_ind, d_ind = 0, 1, 2

  # per commit
  ax_std = ax_all[fc_ind]
  #fc_n, fc_bins, fc_patches = ax_std.hist(all_filecounts_np, np.amax(all_filecounts_np), normed=0)
  hist, bin_edges = np.histogram(all_filecounts_np, bins=range(0,1000,100))
  ax_std.set_title('Files modified')
  ax_std.set_xlabel('File counts changed')

  # insertions and deletions
  print insertions_bins
  print deletions_bins
  ax_std = ax_all[i_ind]
  #in_n, in_bins, in_patches = ax_std.hist(all_insertions_np, insertions_bins)
  hist, bin_edges = np.histogram(all_insertions_np, bins=range(0,1000,10))
  print "insert", all_insertions_np
  for i in range(len(hist)):
    print '%d\t%d' % (bin_edges[i], hist[i])
  nz_hist_log_i, nz_bins_log_i, spline_f_i, critpoint_log_i = \
    hist_and_split(all_insertions_np, insert=True)
  newx = np.linspace(min(nz_bins_log_i), max(nz_bins_log_i), num=1000)
  ax_std.plot(nz_bins_log_i, nz_hist_log_i, 'o',
              newx, spline_f_i(newx), '--')
  ax_std.plot([critpoint_log_i], spline_f_i([critpoint_log_i]), 'o', c='r')
  ax_std.set_title('Lines inserted')
  ax_std.set_ylabel('# commits (log)')
  ax_std.set_xlabel('insertions over time (log)')

  ax_std = ax_all[d_ind]
  #de_n, de_bins, de_patches = ax_std.hist(all_deletions_np, deletions_bins)
  #ax_std.set_xticks(deletions_bins)
  hist, bin_edges = np.histogram(all_deletions_np, bins=range(0,1000,10))
  for i in range(len(hist)):
    print '%d\t%d' % (bin_edges[i], hist[i])
  nz_hist_log_d, nz_bins_log_d, spline_f_d, critpoint_log_d = \
    hist_and_split(all_deletions_np, insert=False)
  newx = np.linspace(min(nz_bins_log_d), max(nz_bins_log_d), num=1000)
  ax_std.plot(nz_bins_log_d, nz_hist_log_d, 'o',
              newx, spline_f_d(newx), '--')
  ax_std.plot([critpoint_log_d], spline_f_d([critpoint_log_d]), 'o', c='r')
  ax_std.set_title('Lines deleted')
  ax_std.set_ylabel('# commits (log)')
  ax_std.set_xlabel('deletions over time (log)')

  # file counts
  fig.suptitle('Histograms of file counts and insertions/deletions')
  # ax_std.set_ylim(fc_min, fc_max)
  file_count_dest = os.path.join(output_dir, '%s_fc_insertions_deletions_hist.png' % year_q)
  print "Saving file count figure", file_count_dest
  fig.savefig(file_count_dest)
  plt.close(fig)

  many_inserts = set()
  many_deletes = set()
  critpoint_i, critpoint_d = np.exp(critpoint_log_i), np.exp(critpoint_log_d)
  for uname in all_timeseries:
    time_array, commit_strs = all_timeseries[uname]
    posix_times = time_array[:,0]
    commits = time_array[:,1]
    filecounts = time_array[:,2]
    insertions = time_array[:,3]
    deletions = time_array[:,4]

    i_past_crit = np.nonzero(insertions > critpoint_i)
    for i in i_past_crit[0].tolist():
      many_inserts.add(commit_strs[i])
    numi_past_crit = np.sum(np.nonzero(insertions > critpoint_i))

    d_past_crit = np.nonzero(deletions > critpoint_d)
    numd_past_crit = np.sum(np.nonzero(deletions > critpoint_d))
    for d in d_past_crit[0].tolist():
      many_deletes.add(commit_strs[i])

  inserts = list(many_inserts)
  deletes = list(many_deletes)
  with open(os.path.join(output_dir, year_q, 'diffs', 'commits_inserts'), 'w') as f:
    inserts.sort()
    f.write('\n'.join(inserts))
  with open(os.path.join(output_dir, year_q, 'diffs', 'commits_deletes'), 'w') as f:
    deletes.sort()
    f.write('\n'.join(deletes))

"""
Displays the graph in the terminal in text form,
with additional lookups of which commit is which.
The default sort is x-wise, then y-wise.
To sort y-wise, set sort_by_x=False.

Note that this must be called for online and offline separately,
  since the two are graphed using two separate scatter commands.
"""
def display_text_graph(xs, ys, grades, lrs,
                       all_np, all_str_np,
                       sort_by_x=True):
  dtype = [('x', float), ('y', float)]
  if sort_by_x:
    xy_np = np.array([xs, ys],
        dtype=[('x', float), ('y', float)])
    xy_inds = np.argsort(xy_np, order=['x', 'y'])[0]
  else:
    print "sorting by y"
    xy_np = np.array([ys, xs],
        dtype=[('y', float), ('x', float)])
    xy_inds = np.argsort(xy_np, order=['y', 'x'])[0]
  xy_sort = (xy_np.T)[xy_inds,:]
  grades_sort = grades[xy_inds]
  lrs_sort = lrs[xy_inds]
  all_sort = all_np[xy_inds]
  all_str_sort = all_str_np[xy_inds]
  # show x, y, grade
  # show time, line range, commit number
  # show everything in top_sims
  # show commit name
  # show grade
  print "all xy sort", xy_sort.shape
  for xy_coord in range(xy_sort.shape[0]):
    if sort_by_x:
      x, y = xy_sort[xy_coord,:]
      print "x: %s, y: %s, color: %s, lines: %s" % \
          (x[0], y[0], grades_sort[xy_coord], lrs_sort[xy_coord])
    else:
      y, x = xy_sort[xy_coord,:]
      print "y: %s, x: %s, color: %s, lines: %s" % \
          (y[0], x[0], grades_sort[xy_coord], lrs_sort[xy_coord])
    print "\t%s" % str(all_sort[xy_coord,:])
    print "\t%s" % str(all_str_sort[xy_coord,:])
    print



