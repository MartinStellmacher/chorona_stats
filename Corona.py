import pandas as pd
import os
import git
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

hopkinsGitDir = "./COVID-19"
hopkinsTimeSeries = os.path.join(hopkinsGitDir,"csse_covid_19_data/csse_covid_19_time_series")
hopkinsConfirmed = "time_series_covid19_confirmed_global.csv" # "time_series_19-covid-Confirmed.csv"
hopkinsDeath = "time_series_covid19_deaths_global.csv" # "time_series_19-covid-Deaths.csv"

populationFile = './cia_world_population_202007.txt'
population = pd.read_fwf( populationFile,colspecs=[(8,53),(65,78)],header=1,thousands=',')
population = population.rename(columns={'Unnamed: 0':'country','Unnamed: 1':'population'})
population = population.set_index('country')
population = population.rename({
    'United States':'US',
    'Holy See (Vatican City)':'Holy See',
    'Bahamas, The': 'Bahamas',
    'Gaza Strip': 'West Bank and Gaza',
    'Congo, Republic of the': 'Congo (Brazzaville)',
    'Macedonia': 'North Macedonia',
    'Congo, Democratic Republic of the': 'Congo (Kinshasa)',
    'Gambia, The': 'Gambia',
    'Taiwan': 'Taiwan*'
})

def after_plot( pdf):
    # fix borders around charts
    plt.tight_layout()
    if pdf is None:
        plt.show()
    else:
        pdf.savefig()
        plt.close()

def plot_bars(data, title, pdf):
    data.plot.bar( title=title,rot=90)
    after_plot( pdf)

def plot_increase_bars_rel(data, title, pdf):
    inc = 100 * ((data.T + 1) / (data.T.shift() + 1) - 1).T
    inc.plot.bar( title=title,rot=90)
    after_plot( pdf)

def plot_increase_bars_abs(data, title, pdf):
    inc = data - data.shift()
    inc.plot.bar( title=title,rot=90)
    after_plot( pdf)

def plot_over_time(data, title, pdf):
    data.plot( title=title,rot=90)
    after_plot( pdf)

def plot_stats( data, title, pdf):
    print(f'\n{title}\n\n')
    print(data)
    plot_bars(data.iloc[:, -1:], title, pdf)
    plot_over_time( data.T, title, pdf)

def plot_confirmed_vs_killed( confirmed, killed, pdf):
    for country in confirmed.index:
        confirmed.loc[country].plot(title=f'{country}', legend=True, logy=True, rot=45)
        killed.loc[country].plot(title=f'{country}', legend=True, logy=True, rot=45)
        plt.legend(['confirmed','killed'])
        after_plot( pdf)

def read_and_cleanup( filename):
    data = pd.read_csv(os.path.join(hopkinsTimeSeries, filename))  # read raw CSV
    data = data.rename(columns={"Province/State": "Province",
                                          "Country/Region": "Country"})  # replace none Pandas conform column headers
    data = data.groupby('Country').sum()  # ignore Province, accumulate Countries
    data = data.iloc[:, 2:]  # remove lat/lon columns
    return data

def topN( df, n):
    return df.sort_values(df.columns[-1],na_position='first').tail(n)

def generate_all_plots(pdf=None):
    # git update
    hopkinsGit = git.cmd.Git(hopkinsGitDir)
    print( hopkinsGit.pull())
    # read raw data
    confirmed = read_and_cleanup(hopkinsConfirmed)
    killed = read_and_cleanup(hopkinsDeath)

    #Teutscheland
    historyDays=14
    german_confirmed = confirmed.loc['Germany'].tail(historyDays)
    german_killed = killed.loc['Germany'].tail(historyDays)
    plot_increase_bars_rel( german_confirmed, f'German Confirmed {historyDays} Day Increase [%]',pdf )
    plot_increase_bars_rel( german_killed, f'German Killed {historyDays} Day Increase [%]',pdf )
    plot_increase_bars_abs( german_confirmed, f'German Confirmed {historyDays} Day Increase',pdf )
    plot_increase_bars_abs( german_killed, f'German Killed {historyDays} Day Increase',pdf )

    # filter data by selected countries
    countries_with_many_confirmed=confirmed.loc[confirmed.iloc[:,-1]>500].index
    confirmed = confirmed.loc[countries_with_many_confirmed]
    killed = killed.loc[countries_with_many_confirmed]

    plot_stats(topN( confirmed, 10), 'confirmed', pdf)
    plot_stats(topN( killed, 10), 'killed', pdf)

    population_millions = population['population']/1000000.0
    plot_stats(topN((confirmed.T/population_millions).T,10), 'confirmed per million', pdf)
    plot_stats(topN((killed.T/population_millions).T,10), 'killed per million', pdf)

    plot_stats(topN(100*killed/(confirmed+1),10), 'killed per confirmed [%]', pdf)

    # todo stl: da muss noch ein Tiefpassfilter drauf
    dailyIncreaseConfirmed=100*((confirmed.T+1)/(confirmed.T.shift()+1)-1).T
    plot_stats(topN(dailyIncreaseConfirmed,10), 'confirmed daily increase [%]', pdf)
    dailyIncreaseKilled=100*((killed.T+1)/(killed.T.shift()+1)-1).T
    plot_stats(topN(dailyIncreaseKilled,10), 'killed daily increase [%]', pdf)

    plot_confirmed_vs_killed(topN(confirmed,10), killed, pdf)


########################### MAIN ###########################
if True:
    with PdfPages('stats.pdf') as pdf:
        generate_all_plots( pdf)
else:
    generate_all_plots()






















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
