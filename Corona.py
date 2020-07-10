from distutils.command.config import config

import pandas as pd
import os
import git
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

hopkinsGitDir = "./COVID-19"
hopkinsTimeSeries = os.path.join(hopkinsGitDir,"csse_covid_19_data/csse_covid_19_time_series")
hopkinsConfirmed = "time_series_covid19_confirmed_global.csv"
hopkinsDeath = "time_series_covid19_deaths_global.csv"
hopkinsRecovered = "time_series_covid19_recovered_global.csv"

nyt_git_dir = './covid-19-data'
nyt_counties = 'us-counties.csv'
nyt_states = 'us-states.csv'

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

population_millions = population['population'] / 1000000.0

nTop = 3

def after_plot( pdf):
    # fix borders around charts
    plt.tight_layout()
    if pdf is None:
        plt.show()
    else:
        pdf.savefig()
        plt.close()

def plot_bars(data, title, pdf):
    data.plot.bar( title=title,rot=90,legend=False)
    after_plot( pdf)

def plot_increase_bars(data, name, pdf, relative, count):
    title = name + f' {count} Days Increase'
    if relative:
        title += ' [%]'
    data_tail = data.tail(count)
    if relative:
        inc = 100 * ((data_tail.T + 1) / (data_tail.T.shift() + 1) - 1).T
    else:
        inc = data_tail - data_tail.shift()
    filtered(inc).plot.bar( title=title,rot=90)
    #inc.plot.bar( title=title,rot=90)
    after_plot( pdf)

def plot_increase_stats(active, confirmed, killed, recovered, location, pdf, historyDays):
    for rel in [False]: # [True, False]:
        plot_increase_bars(active.loc[location], f'Active {location}', pdf, rel, historyDays)
        plot_increase_bars(confirmed.loc[location], f'Confirmed {location}', pdf, rel, historyDays)
        plot_increase_bars(killed.loc[location], f'Killed {location}', pdf, rel, historyDays)
        plot_increase_bars(recovered.loc[location], f'Recovered {location}', pdf, rel, historyDays)

def filtered( data, width=3):
    return data.rolling( width, center=True, win_type='gaussian',min_periods=1).mean(std=width)

def plot_country(active, confirmed, killed, recovered, location, pdf, historyDays):
    filtered( active.loc[ location]).plot( legend=True, logy=False, rot=75)
    filtered( confirmed.loc[ location]).plot( legend=True, logy=False, rot=75)
    filtered( killed.loc[ location]).plot( legend=True, logy=False, rot=75)
    ax = filtered( recovered.loc[ location]).plot( title=location,legend=True, logy=False, rot=75)
    ax.legend(['active', 'confirmed', 'killed', 'recovered'])
    after_plot(pdf)

    dActive=(active.T-active.T.shift()).T
    dConf=(confirmed.T-confirmed.T.shift()).T
    dKilled=(killed.T-killed.T.shift()).T
    dRecovered=(recovered.T-recovered.T.shift()).T
    filtered( dActive.loc[ location]).plot( legend=True, logy=True, rot=75)
    filtered( dConf.loc[ location]).plot( legend=True, logy=True, rot=75)
    filtered( dKilled.loc[ location]).plot( legend=True, logy=True, rot=75)
    ax = filtered( dRecovered.loc[ location]).plot( title=location+" absolute increase",legend=True, logy=True, rot=75)
    ax.legend(['active', 'confirmed', 'killed', 'recovered'])
    after_plot(pdf)



def plot_over_time(data, title, pdf):
    data.plot( title=title,rot=90)
    after_plot( pdf)

def plot_stats( data, title, pdf):
    print(f'\n{title}\n\n')
    print(data)
    plot_bars(data.iloc[:, -1:], title, pdf)
    plot_over_time( data.T, title, pdf)

def plot_confirmed_vs_killed_vs_recovered( confirmed, killed, recovered, pdf):
    for country in confirmed.index:
        confirmed.loc[country].plot(title=f'{country}', legend=True, logy=True, rot=45)
        killed.loc[country].plot(title=f'{country}', legend=True, logy=True, rot=45)
        recovered.loc[country].plot(title=f'{country}', legend=True, logy=True, rot=45)
        plt.legend(['confirmed','killed','recovered'])
        after_plot( pdf)

def read_and_cleanup( filename):
    data = pd.read_csv(os.path.join(hopkinsTimeSeries, filename))  # read raw CSV
    data = data.rename(columns={"Province/State": "Province",
                                          "Country/Region": "Country"})  # replace none Pandas conform column headers
    data = data.groupby('Country').sum()  # ignore Province, accumulate Countries
    data = data.iloc[:, 2:]  # remove lat/lon columns
    return data

def topN( df, n):
    #return df.sort_values(df.columns[-1],na_position='first').tail(n)
    top =  df.sort_values(df.columns[-1],na_position='first').tail(n)
    selectedCountries = set(top.index.values)
    countries_with_many_confirmed=['Sweden','US','Germany','Norway','Denmark','Finland','Turkey']
    selectedCountries.update(countries_with_many_confirmed)
    selectedData = df.loc[selectedCountries]
    return selectedData.sort_values(selectedData.columns[-1])

def generate_new_york_plots(pdf=None):
    # git update
    nyt_git = git.cmd.Git(nyt_git_dir)
    print( nyt_git.pull())

    data = pd.read_csv(os.path.join(nyt_git_dir, nyt_counties))
    data['county_state'] = data['county']+'/'+data['state']
    confirmed = data.loc[:, ['date', 'county_state', 'cases']]
    confirmed = confirmed.set_index(['date', 'county_state']).unstack(0)
    confirmed = confirmed.T.droplevel(0).T
    killed = data.loc[:, ['date', 'county_state', 'deaths']]
    killed = killed.set_index(['date', 'county_state']).unstack(0)
    killed = killed.T.droplevel(0).T

    us_states = ['New York City/New York','Orleans/Louisiana']
    historyDays = 14
    for state in us_states:
        plot_increase_stats(confirmed, killed, None, state, pdf, historyDays)

def updateData():
    # git update
    hopkinsGit = git.cmd.Git(hopkinsGitDir)
    print( hopkinsGit.pull())
    # read raw data
    confirmed = read_and_cleanup(hopkinsConfirmed)
    killed = read_and_cleanup(hopkinsDeath)
    recovered = read_and_cleanup(hopkinsRecovered)
    active = confirmed - killed - recovered

    return confirmed, killed, recovered, active

def generate_all_plots(pdf=None):

    confirmed, killed, recovered, active = updateData()

    for country in ['Germany','US','Sweden','Norway','Turkey']:
        historyDays=120
        plot_increase_stats(active, confirmed, killed, recovered, country, pdf, historyDays)
        plot_country(active, confirmed, killed, recovered, country, pdf, historyDays)

    # filter data by selected countries
    '''
    countries_with_many_confirmed=confirmed.loc[confirmed.iloc[:,-1]>500].index
    confirmed = confirmed.loc[countries_with_many_confirmed]
    killed = killed.loc[countries_with_many_confirmed]
    recovered = recovered.loc[countries_with_many_confirmed]
    '''
    countries_with_many_active=active.loc[confirmed.iloc[:,-1]>500].index
    active = active.loc[countries_with_many_active]
    confirmed = confirmed.loc[countries_with_many_active]
    killed = killed.loc[countries_with_many_active]
    recovered = recovered.loc[countries_with_many_active]

    plot_stats(topN( active, nTop), 'active', pdf)
    plot_stats(topN( confirmed, nTop), 'confirmed', pdf)
    plot_stats(topN( killed, nTop), 'killed', pdf)
    plot_stats(topN( recovered, nTop), 'recovered', pdf)

    plot_stats(topN((active.T/population_millions).T,nTop), 'active per million', pdf)
    plot_stats(topN((confirmed.T/population_millions).T,nTop), 'confirmed per million', pdf)
    plot_stats(topN((killed.T/population_millions).T,nTop), 'killed per million', pdf)
    plot_stats(topN((recovered.T/population_millions).T,nTop), 'recovered per million', pdf)

    #plot_stats(topN(100*killed/(confirmed+1),nTop), 'killed per confirmed [%]', pdf)
    #plot_stats(topN(100*recovered/(confirmed+1),nTop), 'recovered per confirmed [%]', pdf)

    # todo stl: da muss noch ein Tiefpassfilter drauf
    dailyIncreaseConfirmed=100*((confirmed.T+1)/(confirmed.T.shift()+1)-1).T
    plot_stats(topN(dailyIncreaseConfirmed,nTop), 'confirmed daily increase [%]', pdf)
    dailyIncreaseKilled=100*((killed.T+1)/(killed.T.shift()+1)-1).T
    plot_stats(topN(dailyIncreaseKilled,nTop), 'killed daily increase [%]', pdf)

    cf = filtered(confirmed, 5)
    kf = filtered(killed, 5)
    weeklyIncreaseConfirmed=100*((cf.T+1)/(cf.T.shift(7)+1)-1).T
    plot_stats(topN(weeklyIncreaseConfirmed,nTop), 'confirmed weekly increase [%]', pdf)
    weeklyIncreaseKilled=100*((kf.T+1)/(kf.T.shift(7)+1)-1).T
    plot_stats(topN(weeklyIncreaseKilled,nTop), 'killed weekly increase [%]', pdf)

    plot_confirmed_vs_killed_vs_recovered(topN(confirmed,nTop), killed,recovered, pdf)


def cumulative_week(pdf=None):
    confirmed, killed, _, _ = updateData()

    killed_7 = killed.diff(7,1)
    killed_7_pm = (killed_7.T/population_millions).T
    print(killed_7_pm)
    plot_stats(topN(killed_7_pm, nTop), 'killed last 7 days per million', pdf)

    confirmed_7 = confirmed.diff(7,1)
    confirmed_7_pm = (confirmed_7.T/population_millions).T
    print(confirmed_7_pm)
    plot_stats(topN(confirmed_7_pm, nTop), 'confirmed last 7 days per million', pdf)


########################### MAIN ###########################

if True:
    with PdfPages('stats.pdf') as pdf:
        generate_all_plots(pdf)
        cumulative_week(pdf)
        #generate_new_york_plots( pdf)
else:
    generate_all_plots()
    cumulative_week()
    #generate_new_york_plots()

