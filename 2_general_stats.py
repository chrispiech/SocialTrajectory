from helper import *
from git_helper import *
from moss_tool import *
import matplotlib.colors as cl
import matplotlib.cm as cm
import numpy as np
import matplotlib.pyplot as plt
import os

def sarah_plot(output_dir, year_q):
  exam_grades = load_exam_grades(output_dir, year_q)

  top_sims = load_top_sims_from_log(output_dir, year_q)
  #example(output_dir, year_q, top_sims, exam_grades)

  # boxplots
  # does not work; fix later
  #graph_stats(output_dir, year_q, top_sims, exam_grades)

  # gradetime code -- don't work on it unless you're done with part one :)
  graph_gradetime(output_dir, year_q, top_sims, exam_grades)

  # lecture code
  lecture_year_q = 'lecture_%s' % year_q
  lecture_top_sims = load_top_sims_from_log(output_dir, lecture_year_q)

def example(output_dir, year_q, top_sims, exam_grades):
  print "Exam grades"
  for uname in exam_grades:
    print uname, exam_grades[uname]
  for uname in top_sims:
    posix_times = top_sims[uname].keys()
    posix_times.sort()
    print "student: %s" % (uname)
    # print posix_times # just the weird posix time strings

    # readable time versions
    # make sure to convert posix_t to an int before calling posix_to_time
    real_times = [posix_to_time(int(posix_t)) for posix_t in posix_times]
    print '\n'.join(real_times) # this prints it out fancily

    # this is the pythonic version that uses just a few lines to print
    # everything nicely
    print '\n'.join(['%s\t%s\t%s' % \
              (uname, posix_t, posix_to_time(int(posix_t))) \
                for posix_t in posix_times])

  # end of per-student processing

  # look at graph_sims_to_gradetimes in gradetime_stats.py for how to store
  # all student information to numpy arrays.

  # how to save a text file to proc_output
  test_outputs = ['hello', 'this is a new line', 'another new line']
  with open(os.path.join(output_dir, 'text_file.txt'), 'w') as f:
    f.write('\n'.join(test_outputs))

  # how to draw a figure and save to proc_output
  fig = plt.figure()
  ax1 = plt.gca()
  x = np.arange(0,10)
  y = x ** 2
  plt.scatter(x, y, marker='x')

  ax1.set_title("Test figure")
  ax1.set_xlabel("x")
  ax1.set_ylabel("y = x^2")

  plt.tight_layout() # always call this right before saving.
  graph_name = 'test_%s.png' % year_q
  print "Saving test figure to %s" % graph_name
  fig.savefig(os.path.join(output_dir, graph_name))

"""
Returns start, end, and ranges sorted by uname.
"""
def get_time_info(top_sims, posix_lookup):
  time_info = []
  unames = top_sims.keys()
  unames.sort()

  for uname in unames:
    set_stats = {}
    # get start and end posix times..
    all_posix = [int(posix) for posix in posix_lookup[uname].keys()]
    start_posix, end_posix = min(all_posix), max(all_posix)
    range_posix = end_posix - start_posix
    time_info.append((start_posix, end_posix, range_posix))
  return zip(*time_info)
  
def get_grades(grades):
  midterm_grades = {}
  final_grades = {}
  unames = grades.keys()
  unames.sort()
  for uname in unames:
    set_grades0 = {}
    set_grades1={}
    # get midterm and final grades
    #for info in grades[uname]:
    grade0=grades[uname][0]
    grade1=grades[uname][1]
    #print grade0, grade1
    if grade0 not in set_grades0:
      set_grades0[grade0] = []
    set_grades0[grade0].append((int(grade0)))
    for grade0 in set_grades0:
      if uname not in midterm_grades:
        midterm_grades[uname] = {}
      midterm_grades[uname] = \
        np.array(set_grades0[grade0])
    if grade1 not in set_grades1:
      set_grades1[grade1] = []
    set_grades1[grade1].append((int(grade1)))
    for grade1 in set_grades1:
      if uname not in final_grades:
        final_grades[uname] = {}
      final_grades[uname] = \
        np.array(set_grades1[grade1])
  return midterm_grades, final_grades

def get_student_posix_info(top_sims, posix_lookup):
  all_posix = {}
  for uname in top_sims:
    set_posix = {}
    # get all data
    all_info = posix_lookup[uname].keys()

    for posix_time in top_sims[uname]:
      student_name=top_sims[uname][posix_time][0]
      if student_name not in set_posix:
        set_posix[student_name] = []
      commit_num = posix_lookup[uname][int(posix_time)]
      set_posix[student_name].append(int(posix_time))
      for student_name in set_posix:
        if student_name not in all_posix:
          all_posix[student_name] = {}
        all_posix[student_name] = \
          np.array(set_posix[student_name])
  return all_posix
 
def find_time_info(all_posix):
  starttimes=[]
  endtimes=[]
  duration=[] 
  for id in all_posix:
    num0= int(all_posix[id][0][0])
    num1= int(all_posix[id][0][1])
    num2= int(all_posix[id][0][2])
    starttimes.append(num0)
    endtimes.append(num1)
    duration.append(num2)
  return starttimes, endtimes, duration

def find_grade_info(all_grades, convert):
  converted_grades=[]
  for id in all_grades:
    num2= int(all_grades[id][0])
    converted_grades.append(float(num2/convert))
  return converted_grades

def sort_rank_info(stime, etime, dur, grades):
  starttimes=[]
  endtimes=[]
  duration=[]
  converted_grades=[]
  
  converted_grades, starttimes, endtimes, duration= \
    (list(t) for t in zip(*sorted(zip(grades, stime, etime, dur))))
  grade_ranks=np.arange(len(starttimes),0).astype(float)/len(starttimes)
  return grade_ranks, starttimes, endtimes, duration

def graph_stats(output_dir, year_q, top_sims, exam_grades):
  for year_q in os.listdir(output_dir):
    if len(year_q.split('_')) != 2: continue
    if not os.path.isdir(os.path.join(output_dir, year_q)):
        continue
    output_stats_path = os.path.join(output_dir, year_q)

    print "Getting posix lookup"
    posix_lookup = load_posix_to_commit_ind(output_dir, year_q)

    all_posix= get_student_posix_info(top_sims, posix_lookup)
    print 'How many students in top_sims 2012_1?', len(all_posix.keys())
    for uname in all_posix:
      all_posix[uname].sort()
      print 'creating a figure'
      fig=plt.figure(1, figsize=(18,6))
      print 'creating axes'
      ax=plt.gca()
      fig.canvas.set_window_title('%s' % year_q)
      print 'creating boxplot'
      bp=plt.boxplot([all_posix[id2] for id2 in all_posix])
      ylims = ax.get_ylim()
      new_lb = 1349000000
      new_ub= 1750000000
      ax.set_ylim(new_lb, new_ub)
      print "Adding x labels."
      numBoxes = len(all_posix.keys())
      xtickNames = plt.setp(ax, xticklabels=uname)
      plt.setp(xtickNames, rotation=90, fontsize=8)
      fig.savefig(str(uname)+'fig.png', bbox_inches='tight')
'''

'''
OPD=os.path.join(load_path(), "proc_output")
year_q='2012_1'
# top_sims=load_top_sims_from_log(OPD, year_q)
# exam_grades=load_exam_grades(OPD, year_q)
sarah_plot(OPD, '2012_1')
