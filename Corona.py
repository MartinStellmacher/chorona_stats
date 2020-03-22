import pandas as pd
import os
import git
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

hopkinsGitDir = "./data/COVID-19"
hopkinsTimeSeries = os.path.join(hopkinsGitDir,"csse_covid_19_data/csse_covid_19_time_series")
hopkinsConfirmed = "time_series_19-covid-Confirmed.csv"
hopkinsDeath = "time_series_19-covid-Deaths.csv"
hopkinsRecovered = "time_series_19-covid-Recovered.csv"
#hopkinsFiles = [ hopkinsConfirmed, hopkinsDeath, hopkinsRecovered]

# todo stl: retrieve online ...
populationDict = {
    'China': 1400.050000,
    'Korea, South': 51.629512,
    'Germany': 83.019213,
    'Switzerland': 8.544527,
    'United Kingdom': 66.435550,
    'Italy': 60.262701,
    'Spain': 46.722980,
    'France': 66.993000,
    'US': 327.167434,
    'Iran': 81.800269,
    'Netherlands': 17.290688
}

def after_plot( pdf):
    if pdf is None:
        plt.show()
    else:
        pdf.savefig()
        plt.close()

def plot_bars(data, title, pdf):
    data.plot.bar( title=title,rot=45)
    after_plot( pdf)

def plot_over_time(data, title, pdf):
    data.plot( title=title,rot=45)
    after_plot( pdf)

def plot_stats( data, title, pdf):
    print(data)
    plot_bars(data.iloc[:, -1:], title, pdf)
    plot_over_time( data.T, title, pdf)

def read_and_cleanup( filename):
    data = pd.read_csv(os.path.join(hopkinsTimeSeries, filename))  # read raw CSV
    data = data.rename(columns={"Province/State": "Province",
                                          "Country/Region": "Country"})  # replace none Pandas conform column headers
    data = data.groupby('Country').sum()  # ignore Province, accumulate Countries
    data = data.iloc[:, 2:]  # remove lat/lon columns
    return data

def generate_all_plots(pdf=None):
    # git update
    hopkinsGit = git.cmd.Git(hopkinsGitDir)
    print( hopkinsGit.pull())
    # read raw data
    confirmed = read_and_cleanup(hopkinsConfirmed)
    killed = read_and_cleanup(hopkinsDeath)
    # select 10 countries with most kills
    selectedCountries = list(killed.sort_values(killed.columns[-1]).tail(10).index)
    # filter data by selected countries
    confirmed = confirmed.loc[selectedCountries]
    killed = killed.loc[selectedCountries]

    plot_stats( confirmed, 'confirmed', pdf)
    plot_stats( killed, 'killed', pdf)

    population_millions = pd.Series( populationDict).loc[selectedCountries]
    plot_stats((confirmed.T/population_millions).T, 'confirmed per million', pdf)
    plot_stats((killed.T/population_millions).T, 'killed per million', pdf)

    plot_stats(100*killed/(confirmed+1), 'killed per confirmed [%]', pdf)

    # todo stl: da muss noch ein Tiefpassfilter drauf
    dailyIncreaseConfirmed=100*((confirmed.T+1)/(confirmed.T.shift()+1)-1).T
    plot_stats(dailyIncreaseConfirmed, 'confirmed daily increase [%]', pdf)
    dailyIncreaseKilled=100*((killed.T+1)/(killed.T.shift()+1)-1).T
    plot_stats(dailyIncreaseKilled, 'killed daily increase [%]', pdf)

# MAIN
with PdfPages('stats.pdf') as pdf:
    generate_all_plots( pdf)
#generate_all_plots()






















''' allermoeglicher unausgereifter kram ... 

import numpy as np
#from scipy.optimize import curve_fit

def ef(x,a,b,c,d):
    return a+b*np.exp(c+x*d)

dailyIncrease=100*((t+1)/(t.shift()+1)-1)

plt.cla()
plt.title('Daily Increase')
dailyIncrease.plot()
plt.show()
'''
'''
for _,row in confirmedOver1000.iterrows():
    print(row.name)
    plt.cla()
    v = row['1/22/20':]
    y=v[v >= 10.0]
    x=np.arange(len(y))
    popt, pcov = curve_fit(ef, x, y, [1,1,-3,0.25])
    print(ef(len(y)+4,*popt))
    #print(popt)
    plt.title( row.name)
    plt.plot(x, y)
    plt.plot(x,ef(x,*popt))
    plt.show()
'''
'''
npGermany = confirmed.loc['Germany','1/22/20':].to_numpy()
xoGermany = np.argmax(npGermany>0.0)
Y=npGermany[xoGermany:]
X=np.arange(0,len(Y))

popt, pcov = curve_fit(ef,X,Y)

npItaly = confirmed.loc['Italy','1/22/20':].to_numpy()
xp=[i for i in range(npItaly.shape[0])]
x=[i for i in range(53,60)]
np.interp( x, xp, npItaly)

pass
'''
