import random
import os, sys
import numpy as np
import pandas as pd
from scipy.signal import medfilt
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from preprocess import *

plt.rcParams['figure.figsize'] = (10.0, 8.0) # set default size of plots
plt.rcParams['image.interpolation'] = 'nearest'
plt.rcParams['image.cmap'] = 'gray'

def top_sims_to_array(subset, field_x, field_ys):
    out = {}
    for uname in subset:
        x = [int(sims_uname[get_header_ind(field_x)]) for sims_uname in subset[uname]]
        ys = {}
        for field_y in field_ys:
            if field_y == 'type_other': # record online
                ys[field_y] = [int(sims_uname[get_header_ind(field_y)] == 'online') for sims_uname in subset[uname]]
            else:
                ys[field_y] = [float(sims_uname[get_header_ind(field_y)]) for sims_uname in subset[uname]]
        out[uname] = (x, ys)
    return out

def expfit(x, y):
    # log fit
    # y = Ae^(Bx) <--> log y = log A + B x
    b, a = np.polyfit(x, np.log(y), 1, w=np.sqrt(y)).tolist()
    y_fit = np.exp(a) * np.exp(b * x)
    return y_fit, (a, b)

    # # exp fit directly
    # def expfunc(x, a, b, c):
    #     return a * np.exp(-b * x) + c
    # popt, pcov = curve_fit(expfunc, x, y)
    # return expfunc(x, *popt), popt

def logfit(x, y):
    # y = A + B log x
    b, a = np.polyfit(np.log(x), y, 1).tolist()
    y_fit = a + b * np.log(x)
    return y_fit, (a, b)

def get_fit(subset_dict, field_ys):
    out = {}
    for uname in subset_dict:
        x, ys = subset_dict[uname]
        x = np.array(x)
        fits = {}
        for field_y in field_ys:
            y = ys[field_y]
            y = np.array(y)
            if field_y == 'pself':
                y_fit, coeffs = expfit(x, y)
            else:
                y_fit, coeffs = logfit(x, y)
            fits[field_y] = [y, y_fit, coeffs]
        out[uname] = [x, fits]
    return out

def group_by_progress(subset, field_x, field_ys):
    out = {}
    for uname in subset:
        xs = [int(sim[get_header_ind(field_x)]) for sim in subset[uname]]
        for x in xs:
            if x not in out:
                out[x] = [[] for field_y in field_ys]
        for i, field_y in enumerate(field_ys):
            ys = [float(sim[get_header_ind(field_y)]) for sim in subset[uname]]
            for x, y in zip(xs, ys):
                out[x][i].append(y)
    return out

def percentile_by_time(subset_time, perc):
    percentiles = {}
    for x in subset_time:
        percentiles[x] = np.percentile(np.array(subset_time[x]), perc, axis=1)
    return percentiles

def upper_whisker_by_time(subset_time, factor=1.5):
    percentiles = {}
    for x in subset_time:
        data = np.array(subset_time[x])
        upper_quartile = np.percentile(data, 75, axis=1)
        lower_quartile = np.percentile(data, 25, axis=1)
        iqr = upper_quartile - lower_quartile
        upper_whisker = upper_quartile + factor*iqr
        percentiles[x] = upper_whisker
    return percentiles


def percentiledict_to_array(percentiles, field_ys):
    xs = sorted(percentiles.keys())
    ys = np.zeros((len(xs),len(field_ys)))
    for i, x in enumerate(xs):
        ys[i,:] = percentiles[x]
    return np.array(xs), ys

def get_percentiles(subset, field_x, field_ys, max_factor=1500, perc=50):
    subset_time = group_by_progress(subset, field_x, field_ys)
    percentiles = percentile_by_time(subset_time, perc)
    x, y = percentiledict_to_array(percentiles, field_ys)
    return interpolate_y(x, y, field_ys, max_factor)

def get_upper_whiskers(subset, field_x, field_ys, max_factor=1500, factor=1.5):
    subset_time = group_by_progress(subset, field_x, field_ys)
    upper_whiskers = upper_whisker_by_time(subset_time, factor=1.5)
    x, y = percentiledict_to_array(upper_whiskers, field_ys)
    return interpolate_y(x, y, field_ys, max_factor)

from scipy.interpolate import spline
from scipy.signal import medfilt
def interpolate_y(x, y, field_ys, max_factor, smooth=True):
    interp_y = {}
    for i, field_y in enumerate(field_ys):
        interp_y[field_y] = spline(x, y[:,i], range(max_factor))
    if smooth:
        for field_y in field_ys:
            interp_y[field_y] = medfilt(interp_y[field_y], kernel_size=3)

    return range(max_factor), interp_y

def get_residuals_from_line(subset_dict, field_ys, line_dict):
    resids = {}
    unames = sorted(subset_dict.keys())
    for field_y in field_ys:
        avg_param = '%s_avg' % field_y
        max_param = '%s_max' % field_y
        resids[avg_param] = np.zeros((len(unames),))
        resids[max_param] = np.zeros((len(unames),))

    for i, uname in enumerate(unames):
        x, ys = subset_dict[uname]
        x = np.array(x)
        for field_y in field_ys:
            y = ys[field_y]
            y_fit = line_dict[field_y][x.astype(int)-1]
            residuals = y - y_fit
            avg_param = '%s_avg' % field_y
            max_param = '%s_max' % field_y
            resids[avg_param][i] = np.average(np.abs(residuals))
            resids[max_param][i] = np.max(residuals)
    return resids

def get_avg_and_max(subset_dict, field_ys):
    vals = {}
    unames = sorted(subset_dict.keys())
    for field_y in field_ys:
        avg_param = '%s_avg' % field_y
        max_param = '%s_max' % field_y
        vals[avg_param] = np.zeros((len(unames),))
        vals[max_param] = np.zeros((len(unames),))

    for i, uname in enumerate(unames):
        x, ys = subset_dict[uname]
        x = np.array(x)
        for field_y in field_ys:
            y = ys[field_y]
            avg_param = '%s_avg' % field_y
            max_param = '%s_max' % field_y
            vals[avg_param][i] = np.average(np.abs(y))
            vals[max_param][i] = np.max(y)
            ind = np.amax(y)
    return vals

def get_avg_and_max_full(subset_dict, field_ys):
    all_items = []
    unames = sorted(subset_dict.keys())
    for i, uname in enumerate(unames):
      x, ys = subset_dict[uname]
      items = []
      all_ys = np.array([ys[field_y] for field_y in field_ys])
      for i, field_y in enumerate(field_ys):
        ind = np.argmax(all_ys[i,:])
        #items.append(field_y)
        items += all_ys[:,ind].tolist()
      all_items.append([uname] + items)

    headers = ['uname', 'max_pother_po', 'max_pother_t', 'max_token_po', 'max_token_t']
    return headers, all_items

##### binning
def make_bins(llim, rlim, num):
    bins = np.linspace(llim, rlim, num=50)
    for i, llim in enumerate(bins[:-1]):
        rlim = bins[i]
        print "bin %i: (%s, %s)" % (i, llim, rlim)
    return bins

# bins x, and returns y values and indices for each bin
def get_binned_data(x, y, bins):
    digit_inds = np.digitize(x, bins)
    binned_data = []
    binned_inds = []
    for i, _ in enumerate(bins[:-1]):
        i = i+1
        inds = np.where(digit_inds == i)[0]
        yvals = []
        if inds is not None:
            yvals = y[inds]
            xvals = x[inds]
        binned_data.append(yvals)
        binned_inds.append(inds)
    return binned_data, binned_inds

####### plotting
def plot_subset(fit_out, year_q, field_x, field_ys, outliers=None, axs=None, plot_fn=None):
    if outliers is None:
        outliers = set()
    if axs is None:
        fig, axs = plt.subplots(len(field_ys), 1, figsize=(10, 6*len(field_ys)))
 
    unames = sorted(fit_out.keys())
    if outliers and plot_fn is not None:
        cols, lses, mses, alphas = zip(*map(lambda uname: plot_fn(outliers, uname),
                          unames))
        outlier_inds = [i for i in range(len(cols)) if cols[i] != 'k']
        inlier_inds = [i for i in range(len(cols)) if cols[i] == 'k']
    else:
        outlier_inds = [i for i in range(len(unames))]
        inlier_inds = []
        cols = ['b' for i in range(len(unames))]
        lses = ['-' for i in range(len(unames))]
    
    for i in inlier_inds:
        x, fits = fit_out[unames[i]]
        for j, field_y in enumerate(field_ys):
            y, y_fit, coeffs = fits[field_y]
            #axs[j].semilogy(x, y, '%s%s' % (cols[i], lses[i]), ms=1, lw=1, alpha=0.1)
            axs[j].plot(x, y, '%s%s' % (cols[i], lses[i]), ms=1, lw=1, alpha=0.1)
            axs[j].plot(x, y_fit, '%s%s' % (cols[i], lses[i]), ms=1, lw=1, alpha=0.1)
    
    for i in outlier_inds:
        x, fits = fit_out[unames[i]]
        for j, field_y in enumerate(field_ys):
            y, y_fit, coeffs = fits[field_y]
            #axs[j].semilogy(x, y, '%s%s' % (cols[i], lses[i]), ms=1, lw=1, alpha=0.7)
            axs[j].plot(x, y, '%s%s' % (cols[i], lses[i]), ms=1, lw=1, alpha=0.7)
            axs[j].plot(x, y_fit, '%s%s' % (cols[i], lses[i]), ms=1, lw=1, alpha=0.7)

    for i, field_y in enumerate(field_ys):
        axs[i].set_ylabel(field_y)
        axs[i].set_xlabel(field_x)
        axs[i].set_title(field_y)
