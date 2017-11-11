For all git processing:
  python run.py // Comment and uncomment out functions as you need them.

To run moss:
  python3 moss_run_p3.py // Runs each in-progress commit against the set of final submissions.

To process moss:
  python run.py // get moss processing functions from moss_tool.py

To perform tokenizer:
  python run.py // use tokenizer functions from tokenizer_tool.py

Code dependencies:
sudo apt-get install python-dev
sudo apt-get install python-numpy python-scipy
sudo apt-get install python-matplotlib
git clone https://github.com/yanlisa/javalang.git
cd javalang
sudo python setup.py install
sudo apt-get install python-lxml

#sudo apt-get install python-matplotlib
#pip install numpy
#sudo apt-get install libxml2-dev libxslt1-dev zlib1g-dev

If running with SSH, SSH -X or -Y for plotting.

#######
To run preprocessing:
1) all top_sims in a top_sim dir (sim_dir in preprocess)
python preprocess.py creates norm time step

2) Make outliers
Currently I think you just run via ipython notebook

top_sims_arr = top_sims_to_array
get_max_token_pother(top_sims_arr)
# to print
headers, all_items = get_avg_and_max_full(top_sims_arr, ['pother', 'token'])
print ','.join(headers)
print '\n'.join([','.join(map(str, item)) for item in all_items])
IQR_factor = 1.5
# honestly this isn't the 95th percentile but it's the IQR? So 1.5 stdevs away..neem
coords_ell = get_ellipse_coords(max_tokens, max_pothers, factor=IQR_factor)
coords_abs = get_abs_coords(max_tokens, max_pothers, factor=IQR_factor)
save_ell_params(coords_ell)
save_abs_params(coords_abs)
get_and_save_outliers(year_q, use_abs=True, adjust=False) # at end of outlier_stats. ipynb

Make a new <year_q>_uname.csv file:
python preprocess_per_user.py
