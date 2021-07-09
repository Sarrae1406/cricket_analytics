

from espncricinfo.summary import Summary
from espncricinfo.match import Match 
from espncricinfo.series import Series

import json
import requests
from bs4 import BeautifulSoup
from espncricinfo.exceptions import MatchNotFoundError, NoScorecardError
import urllib.request as urllib2
import re
import pandas as pd
import numpy as np
import pickle
import collections
import matplotlib.pyplot as plt
import statistics
import seaborn as sns
from scipy.stats import skew,norm, kurtosis
from collections import Counter

sys.path.append('E:\AI Engineering\ESPN\mnb')
import espn_func

# generate series_id_list using text file containing IDs of all the series from ESPNCricinfo website.

with open('E:\AI Engineering\ESPN\mnb\series_ids.txt') as f:
    series_id_list = f.read().split('\n')
	
# Get list of match IDs, corresponding to all the series IDs.	

match_id_list_dict = espn_func.get_matchId_by_series(series_id_list)

match_list = [match_id for key in match_id_list_dict.keys() for match_id in match_id_list_dict[key]]

# Scraping scorecard data for all the match_ids from ESPNCricinfo.

match_detail_master = espn_func.get_cric_dict(match_list)

match_stats = espn_func.get_match_stats(match_detail_master)

# Create DataFrame using scraped Data

match_stats_df=pd.DataFrame.from_dict(match_stats,orient='index')

match_stats_df.columns = ['match_type', 'ground_name', 'season', 'host_country', 'match_innings_scores', 'fow', 'match_innings_extras', 'match_innings_dismissals', 'match_individual_scores', 'f/o'] 

# Season Data often comes as YYYY/YY format. Converting it to YYYY format for ease of computations.

match_stats_df['season'] = match_stats_df['season'].apply(lambda x : espn_func.normalize_season(x))

# To get a sense of trends with respect to various facets of the game, lets add another column of "decade", since shifts are better to visualize on a decade by decade basis.

match_stats_df['decade'] = match_stats_df['season'].apply(lambda x : espn_func.get_decade(x))

# 1. Lets see the Top cricketing venues which have hosted most number of Test matches till date.

matches_by_ground_name = match_stats_df[[ 'decade', 'ground_name','host_country']].groupby('ground_name').agg({'ground_name':'count'}).rename(columns={'ground_name': 'matches_hosted'})

matches_by_ground_name = matches_by_ground_name[matches_by_ground_name['matches_hosted'] >= 50]

# Most matches hosted by country

matches_by_country = match_stats_df[[ 'decade', 'ground_name','host_country']].groupby('host_country').agg({'host_country':'count'}).rename(columns={'host_country': 'matches_hosted'}).sort_values('matches_hosted', ascending = False)

matches_by_country = matches_by_country[matches_by_country['matches_hosted'] >= 50]

# Most matches hosted by country by Decade

hosted_matches_by_country_by_decade = match_stats_df[['decade', 'ground_name', 'host_country']].groupby(['host_country','decade']).agg({'host_country':'count'}).rename(columns={'host_country': 'matches_hosted'})

# Count of matches Hosted in Asia vs Outside Asia

match_stats_df['continent'] = match_stats_df['host_country'].apply(lambda x : espn_func.mark_asia(x))

# Spread of the game to Subcontinent :

hosted_matches_by_continent_by_decade = match_stats_df[['decade', 'ground_name','continent']].groupby(['decade','continent']).agg({'continent':'count'}).rename(columns={'continent': 'matches_hosted'})

## 2. Run rates of Batting in Tests improving

# Append Decade info to Run rates for each match

match_stats_df['run_rate'] = match_stats_df['match_innings_scores'].apply(lambda x : espn_func.get_run_rate(x))

match_stats_df['run_rate_decade'] = match_stats_df.apply(espn_func.append_decade_run_rates,axis = 1)

#match_stats_df['run_rates_with_decade'] = match_stats_df.apply(espn_func.append_decade_run_rates,axis = 1)

# Prepare distribution of Run rates by Each Decade.

run_rates_groupby = collections.defaultdict(list)

for x in match_stats_df['run_rate_decade']:
    run_rates_groupby[x[0]].append(x[1])


run_rates_flattened = collections.defaultdict(list)
for key in run_rates_groupby.keys():
    flattened_list = [ y for x in run_rates_groupby[key] for y in x]
    run_rates_flattened[key].append(flattened_list)
	
# Plot the distribution of Run rates.



## 3 Power Law Distribution : Distribution of Runs scored by Batsman in a Test Innings.

# Flatten the individual scores for each innings of Test Match into a single list

match_stats_df['flattened_individual_scores'] = match_stats_df['match_individual_scores'].apply(lambda x : espn_func.flatten_individual_scores(x))

# Append decade info to the flattened individual scores.

match_stats_df['flattened_individual_scores_year'] = match_stats_df.apply(espn_func.append_year_flattened_individual_scores,axis = 1)	

# 
Flattened_scores = [x for x in match_stats_df['flattened_individual_scores_year'] if len (x) ==2]

Flattened_scores_groupby = collections.defaultdict(list)

for x in Flattened_scores:
    Flattened_scores_groupby[x[0]].extend(x[1])

Flattened_scores_list = collections.defaultdict(list)
for key in Flattened_scores_groupby.keys():
    flattened_list = [x for x in Flattened_scores_groupby[key] if x is not None]
    Flattened_scores_list[key].extend(flattened_list)
	
# Plot the distribution of scores	
	
ncols = 2

#run_rates_flattened.pop('2020s')

keys = Flattened_scores_list.keys()

nrows = (len(Flattened_scores_list) // ncols)

fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(18, 18))

counter = 0
stats = {}
for i in range(nrows):
    for j in range(ncols):
        ax = axes[i][j]
        if counter < len(Flattened_scores_list):
            key = list(Flattened_scores_list.keys())[counter]
            #means[key] = statistics.mean(Flattened_scores_list[key])
            ax.hist(Flattened_scores_list[key], bins=50, color='blue', alpha=0.5, range= (0,200))
            x = Flattened_scores_list[key]
            stats_dict = {'mean' : statistics.mean(x), 'median' : statistics.median(x), 'st_dev':statistics.pstdev(x), 'skew':skew(x), 'kurt':kurtosis(x)}
            stats[key] = stats_dict
            ax.set_xlabel('Player score')
            ax.set_ylabel(key)
            #ax.set_ylim([0, 5])
            leg = ax.legend(loc='upper left')
            leg.draw_frame(False)
        else:
             ax.set_axis_off()
        counter += 1
plt.show()

stats_df = pd.DataFrame(stats)

print(stats_df)

## 4. Gradually becoming a Batsman Game ?

# 400+ Runs scored in an inning / Number of Matches

match_stats_df['count_400'] = match_stats_df['match_innings_scores'].apply(lambda x : espn_func.get_400_score_count(x))

# Group all the 400+ score counts by country, by decade.

count_400_by_decade = match_stats_df[['count_400','decade']]

count_400_dict = collections.defaultdict(list)
for i in range(len(count_400_by_decade)):
    if len(count_400_by_decade.iloc[i,0]) > 0:
        count_400_dict[count_400_by_decade.iloc[i,1]].append(count_400_by_decade.iloc[i,0])

count_400_dict_final = collections.defaultdict(list)
for i in count_400_dict.keys():
    for j in count_400_dict[i]:
        count_400_dict_final[i].extend(j)
		
count_400 = {}
for key in count_400_dict_final.keys():
    count_400[key] = Counter(count_400_dict_final[key])

count_400.pop('2020s')
count_400_df = pd.DataFrame([(i,j,count_400[i][j]) for i in count_400.keys() for j in count_400[i].keys()], columns=["decade", "country", "400_count"])

# Plot the 400+ score by country with hue for Decade.

fig = plt.figure(figsize=(15,15))
ax = sns.barplot(x="country", y="400_count", hue="decade" ,data=count_400_df)
plt.xticks(rotation=45)
plt.show()

## 5. Centuries per match by Ground 

# Finding Avg centuries scored on each ground

match_stats_df['centuries_scored'] = match_stats_df['match_individual_scores'].apply(lambda x : espn_func.get_centuries_in_match(x))


century_stats_df = match_stats_df[['centuries_scored','ground_name','match_type']].groupby('ground_name').agg({'centuries_scored':['sum','mean'], 'match_type':'count'})

print(century_stats_df)

# Centuries per match by Ground - Top 10 

Centuries_per_match_by_Ground_Top10 = century_stats_df[century_stats_df['match_type']['count'] >= 20].sort_values([('centuries_scored','mean')], ascending=False).iloc[:10,:]

fig = plt.figure(figsize = (15, 8))
plt.bar(Centuries_per_match_by_Ground_Top10.index, Centuries_per_match_by_Ground_Top10['centuries_scored']['mean'], color ='maroon',width = 0.6,align="center")
plt.xlabel("Venue")
plt.xticks(rotation=90)
plt.ylabel("Avg. Centuries per match")
plt.title("Avg Centuries per match by Ground - Top 10")
plt.show()


# Centuries per match by Ground - Bottom 5 

Centuries_per_match_by_Ground_Bottom_5 = century_stats_df[century_stats_df['match_type']['count'] >= 20].sort_values([('centuries_scored','mean')], ascending=True).iloc[:5,:]

fig = plt.figure(figsize = (10, 6))
plt.bar(Centuries_per_match_by_Ground_Bottom_5.index, Centuries_per_match_by_Ground_Bottom_5['centuries_scored']['mean'], color ='maroon',width = 0.4,align="center")
plt.xlabel("Venue")
plt.xticks(rotation=90)
plt.ylabel("Avg. Centuries per match")
plt.title("Avg. Centuries per match by Ground - Bottom 5")
plt.show()

# 6. Contribution of the lower order

match_stats_df['lower_5_by_country_year_individual'] = match_stats_df.apply(espn_func.append_year_lower_5_by_country_individual,axis = 1)

lower_5_by_decade_by_inning = collections.defaultdict(list)
for list1 in match_stats_df['lower_5_by_country_year_individual']:
    for list2 in list1:
        if len(list2[1][1]) > 10 :
            if None not in list2[1][1]:
                lower_5_contri = (sum(list2[1][1][6:]) / sum(list2[1][1])) * 100
                lower_5_by_decade_by_inning[list2[0]].append((list2[1][0],lower_5_contri))

lower_5_by_decade_by_country = collections.defaultdict(list)
for key in lower_5_by_decade_by_inning.keys():
	lower5_by_decade_by_country = collections.defaultdict(list)
	for list1 in lower_5_by_decade_by_inning[key]:
		lower5_by_decade_by_country[list1[0]].append(list1[1])
	lower_5_by_decade_by_country[key].append(lower5_by_decade_by_country)
		
lower_5_by_decade_by_country_mean = collections.defaultdict(list)
for decade in lower_5_by_decade_by_country.keys():
	lower_5_individual_contri = collections.defaultdict(list)
	for country in lower_5_by_decade_by_country[decade][0].keys():
		lower_5_individual_contri[country] = statistics.mean(lower_5_by_decade_by_country[decade][0][country])
	lower_5_by_decade_by_country_mean[decade].append(lower_5_individual_contri)
	
lower_5_df = pd.DataFrame([(i,j,lower_5_by_decade_by_country_mean[i][0][j]) for i in lower_5_by_decade_by_country_mean.keys() for j in lower_5_by_decade_by_country_mean[i][0].keys()], columns=["decade", "Country", "Lower_5_contribution_percentage"])

## 7. Distribution of Dismissals

match_stats_df['dismissal_distrib'] = match_stats_df['match_innings_dismissals'].apply(lambda x : espn_func.flatten_dismissals(x)) 

match_stats_df['dismissal_type_year'] = match_stats_df.apply(espn_func.append_decade_dismissal,axis = 1)

dismissal_type_decade = collections.defaultdict(list)
for list1 in match_stats_df['dismissal_type_year']:
    dismissal_type_decade[list1[0]].extend(list1[1])

dismissal_type_count_by_decade = collections.defaultdict(list)
for keys in list(dismissal_type_decade):
    print(keys)
    removed_not_outs = [x for x in dismissal_type_decade[keys] if x!= 12]
    dismissal_type_count_by_decade[keys] = removed_not_outs

dismissal_set = []
for key1 in dismissal_type_count_by_decade.keys():
    for key2 in collections.Counter(dismissal_type_count_by_decade[key1]).keys():
        dismissal_set.append(key2)

dismissal_set = set(dismissal_set)

for key in dismissal_type_count_by_decade.keys():
    for x in dismissal_set:
        if x not in dismissal_type_count_by_decade[key] :
            dismissal_type_count_by_decade[key].append(x)

for key in dismissal_type_count_by_decade.keys():
    dismissal_type_count_by_decade[key] = collections.Counter(dismissal_type_count_by_decade[key])

for key1 in dismissal_type_count_by_decade:
    key_sum = sum(dismissal_type_count_by_decade[key1].values())
    for key2 in dismissal_type_count_by_decade[key1].keys():
        new_value = round((dismissal_type_count_by_decade[key1][key2]/key_sum) * 100, 2)
        dismissal_type_count_by_decade[key1][key2] = new_value	

dismissal_df = pd.DataFrame([(i,j,dismissal_type_count_by_decade[i][j]) for i in dismissal_type_count_by_decade.keys() for j in dismissal_type_count_by_decade[i].keys()], columns=['decade','dismissal_type','dismissal_percentage'])

dismissal_df['dismissal_type'] = dismissal_df['dismissal_type'].apply(lambda x :espn_func.get_dismissal_name(x))

dismissal_df= dismissal_df.set_index('decade')

## 8. Follow-Ons inflicted over the decades.

match_stats_df['season'] = match_stats_df['season'].astype(int)

match_stats_df[match_stats_df['season']<=1980]['fo_opportunity'] = 'NA'

match_stats_df['fo_opportunity'] = match_stats_df['match_innings_scores'].apply(lambda x : espn_func.fo_opportunity_exists(x))

fo_opportunity_df = match_stats_df[match_stats_df['fo_opportunity'] == 'yes'][['fo_opportunity', 'decade', 'f/o']].groupby('decade').agg({'fo_opportunity':'count'})

fo_inflicted_df  = match_stats_df[(match_stats_df['f/o'] == 'y') & (match_stats_df['season']>=1980)][['fo_opportunity', 'decade', 'f/o']].groupby('decade').agg({'f/o':'count'})

fo_opportunity_inflicted = pd.merge(fo_opportunity_df, fo_inflicted_df, left_index=True, right_index=True)

fo_opportunity_inflicted['follow-on inflicted percent'] = ( fo_opportunity_inflicted['f/o'] / fo_opportunity_inflicted['fo_opportunity']) * 100

from matplotlib.pyplot import figure

figure(figsize=(10, 8), dpi=80)
plt.ylim(0, 100)
plt.ylabel('Match Count')
plt.xlabel('Decade')
plt.plot( fo_opportunity_inflicted.index, 'fo_opportunity', data=fo_opportunity_inflicted, marker='o', markerfacecolor='blue', markersize=12, color='skyblue', linewidth=4, label = 'f/o opportunity ')
plt.plot( fo_opportunity_inflicted.index, 'f/o', data=fo_opportunity_inflicted, marker='', color='blue', linewidth=2, linestyle='dashed', label="f/o inflicted")
plt.plot( fo_opportunity_inflicted.index, 'follow-on inflicted percent', data=fo_opportunity_inflicted, marker='', color='olive', linewidth=2)

# show legend
plt.legend()

# show graph
plt.show()

################################################################

## 9. Distribution of extras conceded.

match_stats_df['extras_per_100_overs'] = match_stats_df['match_innings_extras'].apply(lambda x : espn_func.get_extras_per_100_overs(x))

match_stats_df[['fo_opportunity', 'decade', 'f/o','extras_per_100_overs']].groupby('decade').agg(np.mean)

#################################################################
