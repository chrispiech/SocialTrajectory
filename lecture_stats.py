from helper import *
from git_helper import *
from time import strptime, mktime
from datetime import datetime
from moss_tool import *
import matplotlib.colors as cl
import matplotlib.cm as cmx
from pytz import timezone

use_annotate = False

pst = timezone('US/Pacific')
all_start_time = mktime(datetime(2012,10,15,tzinfo=pst).timetuple())
all_end_time = mktime(datetime(2012,10,24,15,15,tzinfo=pst).timetuple())
incr_length = 86400/2

def lecture_plot(output_dir, year_q):
  lecture_year_q = 'lecture_%s' % year_q
  top_sims = load_top_sims_from_log(output_dir, lecture_year_q)

  graph_sims_to_lectures(output_dir, lecture_year_q, top_sims)

def graph_lecture_plot(output_dir, lecture_year_q, token_type, time_type, top_sims):
  all_timeseries = {}
  all_times_sims = []

  # parse all top sims and get data
  if sim is 'token': sim_ind = 1
  elif sim is 'percent': sim_ind = 2
  print "Parsing all top sims..."
  max_commits = 0
  for uname in top_sims:
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

def graph_sims_to_lectures(output_dir, lecture_year_q, top_sims):
  year_q = '_'.join(lecture_year_q.split('_')[1:])
  posix_lookup = load_posix_to_commit_ind(output_dir, year_q)

  lecturef_stats = {}
  for uname in top_sims:
    uname_stats = {}
    # get start and end posix times..
    all_posix = posix_lookup[uname].keys()
    start_posix, end_posix, num_commits = min(all_posix), max(all_posix), len(all_posix)
    for posix_time in top_sims[uname]:
      lecture_fname, token, percent_self, percent_other, _, _ = \
        top_sims[uname][posix_time]
      if lecture_fname not in uname_stats:
        uname_stats[lecture_fname] = []
      commit_num = posix_lookup[uname][int(posix_time)]
      uname_stats[lecture_fname].append(
        (int(posix_time), int(commit_num),
         start_posix, end_posix, num_commits,
         int(token), float(percent_self), float(percent_other)))
    for lecture_fname in uname_stats:
      if lecture_fname not in lecturef_stats:
        lecturef_stats[lecture_fname] = {}
      lecturef_stats[lecture_fname][uname] = \
        np.array(uname_stats[lecture_fname])

  # indexing variables
  posix_ind, commit_ind = 0, 1
  start_ind, end_ind, length_ind = 2, 3, 4
  token_ind, self_ind, other_ind = 5, 6, 7

  # one datapoint per lecture fname per user
  max_lecture_stats = {}
  for lecture_fname in lecturef_stats:
    temp = []
    # percent other (% lecture), filtered by number of tokens
    for uname in lecturef_stats[lecture_fname]:
      best_percent_i = np.argmax(lecturef_stats[lecture_fname][uname][:,other_ind])
      temp.append(lecturef_stats[lecture_fname][uname][best_percent_i,:])
    max_lecture_stats[lecture_fname] = np.array(temp)

  # histogram of similarities to different lecture files
  fig = plt.figure()
  ax = plt.gca()

  lecture_files = max_lecture_stats.keys()
  num_lecturef = len(lecture_files)
  lecture_files.sort()
  lecture_hists = []
  lecture_rects = []
  bin_edges = range(0,10,101)
  for lecture_f in lecture_files:
    hist, bin_edges = np.histogram(max_lecture_stats[lecture_fname][:,other_ind],
                        bin_edges)
    lecture_hists.append(hist)
  
  lecture_hists = np.array(lecture_hists)
  # index = np.arange(n_groups)
  # bar_width = 0.35
  print lecture_files
  print num_lecturef
  n_bins = 10
  hist, bins, patches = plt.hist([max_lecture_stats[fname] \
                            for fname in lecture_files],
                          np.arange(0,101, 10),
                          #stacked=True,
                          label=lecture_files)
  cm = cmx.get_cmap('RdYlBu_r')
  for i in range(len(patches)):
    flt = float(i)/num_lecturef
    for p in patches[i]:
      plt.setp(p, 'facecolor', cm(flt))
  ax.set_ylim((0,40))
  plt.legend(lecture_files)
  plt.tight_layout()

  fig_dest = os.path.join(output_dir, '%s_sim_dist.png' % lecture_year_q)
  print "Saving histogram figure", fig_dest
  fig.savefig(fig_dest)
  plt.close()

  # make the heatmap plots...somehow?
  # start of the commit on the bottom
    
  # time axis first
  incr = incr_length
  posix_range = np.arange(all_start_time, all_end_time, step=incr)
  x_labels = [pst.localize(datetime.fromtimestamp(posix_t)).strftime('%m/%d %H:%M') \
                      for posix_t in posix_range]

  # decide colors for similarity
  cm = cmx.get_cmap('Blues')
  #cNorm  = cl.Normalize(vmin=np.amin(sims), vmax=np.amax(sims))
  cNorm  = cl.Normalize(vmin=0, vmax=1)
  scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)

  min_sims = [np.amin(max_lecture_stats[lecture_fname][:,other_ind]) for lecture_fname in lecture_files]
  max_sims = [np.amax(max_lecture_stats[lecture_fname][:,other_ind]) for lecture_fname in lecture_files]
  min_sim, max_sim = min(min_sims), max(max_sims)
  max_commit_length = max([np.amax(max_lecture_stats[lecture_fname][:,length_ind]) for lecture_fname in lecture_files])
  min_commit_length = min([np.amax(max_lecture_stats[lecture_fname][:,length_ind]) for lecture_fname in lecture_files])

  ######## start and end times ########
  fig_x, fig_y = 10, 6
  fig, ax_all = plt.subplots(num_lecturef, 2, figsize=(2*fig_x, num_lecturef*fig_y))

  for i in range(num_lecturef):
    lecture_fname = lecture_files[i]
    start_times = max_lecture_stats[lecture_fname][:,start_ind]
    commit_index = max_lecture_stats[lecture_fname][:,commit_ind]
    commit_length = max_lecture_stats[lecture_fname][:,length_ind]
    sims = max_lecture_stats[lecture_fname][:,other_ind]
    print lecture_fname
    print len(sims)
    print np.amin(sims)
    sim_filt = sims >= 0.4
    sims = sims[sim_filt]
    print len(sims)
    # start time
    ax_all[i,0].scatter(start_times, commit_length, marker='o', s=sims*5, c=scalarMap.to_rgba(sims), lw=0)
    ax_all[i,0].set_ylim(0,max_commit_length)
    ax_all[i,0].set_xlim(all_start_time, all_end_time)
    ax_all[i,0].xaxis.set_ticks(posix_range)
    xtickNames = plt.setp(ax_all[i,0], xticklabels=x_labels)
    plt.setp(xtickNames, rotation=45, fontsize=8)

    ax_all[i,0].set_title('%s' % lecture_fname)
    ax_all[i,0].set_ylabel('Duration of assignment')

    # end time
    ax_all[i,1].scatter(start_times, commit_length, marker='o', s=sims*5, c=scalarMap.to_rgba(sims), lw=0)
    ax_all[i,1].set_ylim(0,max_commit_length)
    ax_all[i,1].set_xlim(all_start_time, all_end_time)
    ax_all[i,1].xaxis.set_ticks(posix_range)
    xtickNames = plt.setp(ax_all[i,1], xticklabels=x_labels)
    plt.setp(xtickNames, rotation=45, fontsize=8)

    ax_all[i,1].set_title('%s' % lecture_fname)
    ax_all[i,1].set_ylabel('Duration of assignment')

  ax_all[-1,0].set_xlabel('Student start time')
  ax_all[-1,1].set_xlabel('Student end time')

  fig_dest = os.path.join(output_dir, '%s_time_start_end.png' % lecture_year_q)
  print "Saving time figure", fig_dest
  fig.tight_layout()
  fig.suptitle('Commit duration vs start/end times.')
  fig.savefig(fig_dest)
  plt.close(fig)

  ######## times and commits ########
  fig_x, fig_y = 10, 6
  fig, ax_all = plt.subplots(num_lecturef, 2, figsize=(2*fig_x, num_lecturef*fig_y))

  # by duration of commit. People who worked longer are darker
  cm = cmx.get_cmap('Blues')
  cNorm  = cl.Normalize(vmin=0, vmax=max_commit_length)
  scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)

  for i in range(num_lecturef):
    lecture_fname = lecture_files[i]
    end_times = max_lecture_stats[lecture_fname][:,end_ind]
    commit_index = max_lecture_stats[lecture_fname][:,commit_ind]
    commit_length = max_lecture_stats[lecture_fname][:,length_ind]
    times = max_lecture_stats[lecture_fname][:,posix_ind]
    sims = max_lecture_stats[lecture_fname][:,other_ind]
    sim_filt = sims >= 0.2
    sims = sims[sim_filt]
    # commits
    ax_all[i,0].scatter(commit_index/commit_length, commit_length, marker='o', c='g', s=sims*5, lw=0)
    ax_all[i,0].set_ylim(0,max_commit_length)
    ax_all[i,0].set_xlim(0,1) # progress

    ax_all[i,0].set_title('%s' % lecture_fname)
    ax_all[i,0].set_ylabel('Duration of assignment')

    # times
    ax_all[i,1].scatter(times, commit_length, marker='o', c='b',s=sims*5, lw=0)
    ax_all[i,1].set_ylim(0,max_commit_length)
    ax_all[i,1].set_xlim(all_start_time, all_end_time)
    ax_all[i,1].xaxis.set_ticks(posix_range)
    xtickNames = plt.setp(ax_all[i,1], xticklabels=x_labels)
    plt.setp(xtickNames, rotation=45, fontsize=8)

    ax_all[i,1].set_title('%s' % lecture_fname)
    ax_all[i,1].set_ylabel('Duration of assignment')
  #ax_all[-1,0].set_xlabel('Commit index')
  ax_all[-1,0].set_xlabel('Progress % through assigment')
  ax_all[-1,1].set_xlabel('Commit time')

  fig_dest = os.path.join(output_dir, '%s_time_index.png' % lecture_year_q)
  print "Saving time figure", fig_dest
  fig.tight_layout()
  fig.suptitle('Commit duration')
  fig.savefig(fig_dest)
  plt.close(fig)
