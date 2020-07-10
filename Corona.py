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

new_population_filename = 'COVID-19/csse_covid_19_data/UID_ISO_FIPS_LookUp_Table.csv'
new_population = pd.read_csv(new_population_filename)
population_by_country = new_population.loc[pd.isna(new_population.Province_State)].set_index('Country_Region').loc[:,'Population']
population_millions = population_by_country / 1000000
country_and_iso3 = new_population.loc[pd.isna(new_population.Province_State)].loc[:,['iso3','Country_Region']]  # 2 cruise ships are missing ...

region_filename = 'country_to_region.csv'
regions = pd.read_csv(region_filename).loc[:,['alpha-3', 'region', 'sub-region']]
country_regions = pd.merge( regions, country_and_iso3, left_on='alpha-3', right_on='iso3').drop('alpha-3', axis=1).rename(columns={'Country_Region': 'country'})

population_by_region = pd.merge( population_by_country, country_regions, left_index=True, right_on='country').groupby('region').sum().squeeze()
population_millions_by_region = population_by_region / 1000000

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

def plot_over_time(data, title, pdf=None):
    data.plot( title=title,rot=90)
    after_plot( pdf)

def plot_stats( data, title, pdf=None, with_bars=True):
    print(f'\n{title}\n\n')
    print(data)
    if with_bars:
        plot_bars(data.iloc[:, -1:], title, pdf)
    plot_over_time( data.T, title, pdf)

def plot_confirmed_vs_killed_vs_recovered( confirmed, killed, recovered, pdf=None):
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

    confirmed_by_region = pd.merge( confirmed, country_regions, left_index=True, right_on='country').groupby('region').sum()
    killed_by_region = pd.merge( killed, country_regions, left_index=True, right_on='country').groupby('region').sum()

    confirmed_by_region_per_million = (confirmed_by_region.T/population_millions_by_region).T
    killed_by_region_per_million = (killed_by_region.T/population_millions_by_region).T

    plot_stats( confirmed_by_region, 'confirmed absolute', pdf, with_bars=False)
    plot_stats( killed_by_region, 'killed absolute', pdf, with_bars=False)
    plot_stats( killed_by_region / confirmed_by_region, 'killed per confirmed', pdf, with_bars=False)
    plot_stats( confirmed_by_region_per_million, 'confirmed per million', pdf, with_bars=False)
    plot_stats( killed_by_region_per_million, 'killed per million', pdf, with_bars=False)

    for country in ['Germany','US','Sweden','Norway','Turkey']:
        historyDays=120
        plot_increase_stats(active, confirmed, killed, recovered, country, pdf, historyDays)
        plot_country(active, confirmed, killed, recovered, country, pdf, historyDays)

    # filter data by selected countries
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
else:
    generate_all_plots()
    cumulative_week()

