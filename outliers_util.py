from stats_util import *

def get_whiskers(data, factor=1.5):
    print "IQR factor:", factor
    upper_quartile = np.percentile(data, 75)
    lower_quartile = np.percentile(data, 25)
    iqr = upper_quartile - lower_quartile
    upper_whisker = upper_quartile + factor*iqr
    lower_whisker = lower_quartile - factor*iqr
    print upper_quartile, lower_quartile, iqr, lower_whisker, upper_whisker, "95th", np.percentile(data, 95)
    return lower_whisker, upper_whisker

def get_max_token_pother(top_sims_arr):
    field_ys = ['pself', 'pother', 'token']
    all_avg_max = get_avg_and_max(top_sims_arr, field_ys)
    max_token_param = 'token_max'
    max_pother_param = 'pother_max'
    return all_avg_max[max_token_param], all_avg_max[max_pother_param]

def get_ellipse_coords(x, y, factor=1.5):
    x1, x2 = get_whiskers(x, factor=factor)
    y1, y2 = get_whiskers(y, factor=factor)
    coords = x1, x2, y1, y2
    return coords

def get_abs_coords(x, y, factor=1.5):
    x1, x2 = get_whiskers(x, factor=factor)
    y1, y2 = get_whiskers(y, factor=factor)
    coords = x2, y2
    return coords
    #return 250, 25

def get_ellipse_outliers(x, y, coords_ell, print_stuff=False):
    x1, x2, y1, y2 = coords_ell
    w, h = x2-x1, y2-y1
    a, b = w/2, h/2
    x_c, y_c = (x1+x2)/2, (y1+y2)/2
    x_ell = np.square((x - x_c)/a)
    y_ell = np.square((y - y_c)/b)
    too_small = np.logical_and(x <= x_c, y <= y_c)
    out_inds = np.nonzero(np.logical_and(x_ell+y_ell > 1, np.logical_not(too_small)))[0]
    if print_stuff:
        print out_inds, x_c, y_c, a, b
        print x[out_inds], y[out_inds], x_ell[out_inds], y_ell[out_inds]
        print x_ell[out_inds]+y_ell[out_inds]
    in_inds = np.nonzero(np.logical_or(x_ell+y_ell <= 1, too_small))[0]
    #in_inds = np.nonzero(too_small)[0]
    return out_inds, in_inds

def get_abs_outliers(x, y, coords_abs, print_stuff=False):
    x_thresh, y_thresh = coords_abs
    out_inds = np.nonzero(np.logical_and(x >= x_thresh, y>= y_thresh))[0]
    if print_stuff:
        print out_inds, x_thresh, y_thresh
    in_inds = np.nonzero(np.logical_not(np.logical_and(x >= x_thresh, y>= y_thresh)))[0]
    return out_inds, in_inds

def ell_outliers_helper(coords_ell):
    print coords_ell
    def helper(x, y, print_stuff=False):
        outliers, inliers = get_ellipse_outliers(x, y, coords_ell, print_stuff=print_stuff)
        return outliers
    return helper

def abs_outliers_helper(coords_abs):
    def helper(x, y, print_stuff=False):
        outliers, inliners = get_abs_outliers(x, y, coords_abs, print_stuff=print_stuff)
        return outliers
    return helper

def get_outlier_stats(top_sims_arr, coords, use_abs=False, adjust=False):
    if use_abs:
        outlier_fn = abs_outliers_helper(coords)
    else:
        outlier_fn = ell_outliers_helper(coords)
    outlier_dict = {}
    unames = sorted(top_sims_arr.keys())
    for i, uname in enumerate(unames):
        x, ys = top_sims_arr[uname]
        y_token, y_pother = np.array(ys['token']), np.array(ys['pother'])
        y_online = np.array(ys['type_other'])
        # if adjust:
        #     y_token, y_pother = adjust_slopes(y_token, y_pother)
        outliers = outlier_fn(y_token, y_pother, print_stuff=False)
        num_outliers = len(outliers)
        frac_outliers = num_outliers/float(len(x))
        if num_outliers:
            earliest_outlier = np.amin(np.array(x)[outliers])
            outlier_dict[uname] = [len(outliers), frac_outliers, earliest_outlier, np.amax(y_token), np.amax(y_pother), np.amax(y_online)]
    return outlier_dict


def adjust_slopes(tokens, pothers):
    desired_slope = 50./400
    err = 10
    new_tokens, new_pothers = np.array(tokens), np.array(pothers)
    desired_resid = np.abs(pothers - tokens*desired_slope)
    double_resid = np.abs(pothers - tokens*0.5*desired_slope)
    use_double = err < desired_resid - double_resid # double resid is smaller by an error
    new_tokens[use_double] = tokens[use_double]/2
    return new_tokens, new_pothers

def save_outlier_params(params, name, year_q=None):
    prefix = name
    if year_q:
        prefix = '%s_%s' % (prefix, year_q)
    with open(os.path.join(sim_dir, '%s_outliers.conf' % name), 'w') as f:
        f.write(','.join(map(str,params)))
        print "Wrote outlier params to", f.name

def save_ell_params(params):
    save_outlier_params(params, 'ell')

def save_abs_params(params):
    save_outlier_params(params, 'abs')

def load_params(name, year_q=None):
    prefix = name
    if year_q:
        prefix = '%s_%s' % (prefix, year_q)
    with open(os.path.join(sim_dir, '%s_outliers.conf') % name, 'r') as f:
        line = f.readline()
        return map(float, line.strip().split(','))
