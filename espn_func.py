
# Function to Obtain IDs of Test matches given a test series ID.
def get_matchId_by_series(series_id_list):
	#global match_id_list_dict
	#global match_id_list
	match_id_list_dict = {} 
	#print(match_id_list_dict)
	for series_id in series_id_list:
		print(series_id)
		try:
			s = Series(series_id)
			series_url = 'https://www.espncricinfo.com/series/england-in-nz-test-2019-20-%s/match-results' %series_id
			page = urllib2.urlopen(series_url)
			soup = BeautifulSoup(page, 'html.parser')
			script = soup.find('script', id="__NEXT_DATA__")
			script_dict = json.loads(script.get_text())
			match_id_list = []
			x = script_dict['props']['pageProps']['data']['pageData']['content']['matches']
			for i in range(len(x)):
				match_id_list.append(x[i]['objectId'])
		except Exception as e: print(e)
		print(match_id_list)
		match_id_list_dict[series_id] = match_id_list
	return match_id_list_dict
	
# Function to scrape Test match scorecard web page.
def get_cric_dict(match_list):
    match_detail_master = {}
    for match_id in match_list:
        try:
            print(match_id)
            m = Match(match_id)
            match_type = m.match_class
            ground = m.ground_name
            season = m.season
            lsu = ('https://www.espncricinfo.com/series/australia-tour-of-india-1979-80-61434/india-vs-australia-6th-test-%s/full-scorecard' %match_id).replace(' ','')
            page = urllib2.urlopen(lsu)
            soup = BeautifulSoup(page, 'html.parser')
            script = soup.find('script', id="__NEXT_DATA__")
            if script is None:
                match_detail_master[match_id] = (match_type,ground,season,soup,'legacy')
            else:
                json_text = json.loads(script.get_text())
                match_detail_master[match_id] = (match_type,ground,season,json_text,'new')
        except:
            print("An error occurred")
    return (match_detail_master)


# Function to extract various info from scrapped web page
def get_match_stats(match_detail_master):
	match_stats = {}
	for match in match_detail_master.keys():
		if match_detail_master[match][4] == 'new':
			print(match)
			x = match_detail_master[match] 
			match_type = x[0]
			match_ground = x[1]
			match_season = x[2]
			match_country = x[3]['props']['pageProps']['data']['pageData']['match']['ground']['country']['name']
			Innings_list = x[3]['props']['pageProps']['data']['pageData']['content']['scorecard']['innings']


			match_innings_list = []
			overs_extras_per_innings = []
			dismissal_type = []
			runs_list_per_match = []
			try :
				for i in range(len(Innings_list)):
					# Get team, runs, overs per innings
					#print(i)
					match_innings_list.append((Innings_list[i]['team']['name'],Innings_list[i]['runs'],Innings_list[i]['overs']))

					# Get overs, extras conceded per innings
					overs_extras_per_innings.append ((Innings_list[i]['overs'], Innings_list[i]['extras']))

					# Get distribution of dismissal types
					type_dismissal = []
					for j in range(len(Innings_list[i]['inningBatsmen'])):
						type_dismissal.append (Innings_list[i]['inningBatsmen'][j]['dismissalType'])
					dismissal_type.append(type_dismissal)

					# Get runs scored per innings
					runs_list_per_innings=[]
					for j in range(len(Innings_list[i]['inningBatsmen'])):
						runs_list_per_innings.append(Innings_list[i]['inningBatsmen'][j]['runs'])
					runs_list_per_match.append((Innings_list[i]['team']['name'],runs_list_per_innings))

			except IndexError:
				print('Innings not available')
			except Exception as e: 
				print(e)

			# Get fow in the innings data
			fow_list_match =[]
			for i in range(len(Innings_list)):
				print(i)
				fow_innings = Innings_list[i]['inningFallOfWickets']
				fow_list_innings = []
				for j in range(len(fow_innings)):
					fow_list_innings.append((fow_innings[j]['fowWicketNum'],fow_innings[j]['fowRuns']))
					#print(fow_list_innings)
				fow_list_match.append((Innings_list[i]['team']['name'],fow_list_innings))	

			# Get Follow-On data 
			try:
				if ("f/o" in x[3]['props']['pageProps']['data']['pageData']['match']['teams'][0]['score']) or ("f/o" in x[3]['props']['pageProps']['data']['pageData']['match']['teams'][1]['score']):
					follow_on_by_match_id = 'y'
				else:
					follow_on_by_match_id = 'n'
			except TypeError:
				follow_on_by_match_id = 'n'
				print('match abandoned')


		match_stats[match] = [match_type,match_ground,match_season,match_country,match_innings_list,fow_list_match,overs_extras_per_innings,dismissal_type,runs_list_per_match,follow_on_by_match_id]
	return match_stats
	
# Season Data often comes as YYYY/YY format. Converting it to YYYY format for ease of computations.
def normalize_season(season):
	season = re.sub(r'/[0-9]+', '', season)
	return season
	
# To get a sense of trends with respect to various facets of the game, lets add another column of "decade", since shifts are better to visualize on a decade by decade basis.

def get_decade(season):
    decade =  str((int(season) // 10)) + '0s'
    return decade
	
# Add Continent info basis Host country for a Test Match.
def mark_asia(host_country):
    if host_country in ['India', 'Pakistan', 'Bangladesh','Sri Lanka (and Ceylon)','United Arab Emirates']:
        continent = 'Asia'
    else :
        continent = 'ROW'
    return continent
	
# Get run rate info
def get_run_rate(match_innings_scores):
    return [inning[1]/inning[2] for inning in match_innings_scores if len(inning)==3 and inning[2]!=0]
    
	
# Append Decade info to Run rates for each match
def append_decade_run_rates(x):
    y = [x['decade'],x['run_rate'] ] 
    return y
	
# Flatten the individual scores for each innings of Test Match into a single list

def flatten_individual_scores(match_individual_scores):
    flattened_individual_scores = []
    for inning in match_individual_scores:
        flattened_individual_scores.extend(inning[1])
    return flattened_individual_scores
	
# Append decade info to the flattened individual scores.

def append_year_flattened_individual_scores(x):
    y = [x['decade'],x['flattened_individual_scores'] ] 
    return y
	
# 400+ Runs scored in an inning / Number of Matches

def get_400_score_count(match_innings_scores):
    count_list = ([x[0]for x in match_innings_scores if x[1] >= 400 ])
    counters = Counter(count_list)
    return counters
	
# Append Decade info to Dismissal Types.

def append_decade_dismissal(x):
    y = [x['decade'],x['dismissal_distrib']]
    return y
	
# Mapping Dismissal types to Dismissal names.

def get_dismissal_name(number):
    if number == 1:
        dismissal = "Catch Out"
    elif number == 2:
        dismissal = "Bowled"
    elif number == 3:
        dismissal = "LBW"
    elif number == 4:
        dismissal = "Run Out"
    elif number == 5:
        dismissal = "Stumping"
    elif number == 6:
        dismissal = "Hit wicket"
    elif number == 13:
        dismissal = "Retired Hurt"
    elif number == 7:
        dismissal = "Handle the Ball"
    elif number == 8:
        dismissal = "Obstructing the field"
    elif number == 11:
        dismissal = "Retired out"
    return dismissal
	

# Get Avg number of Extras conceded in a Test match, per 100 overs bowled.
def get_extras_per_100_overs(match_innings_extras):
	extras_total = sum([overs[1] for overs in match_innings_extras])
	overs_total = sum([overs[0] for overs in match_innings_extras])
	if overs_total != 0:
		x = round(( extras_total/ overs_total )*100,2)
	else :
		x = 0
	return x
	
# Get Number of centuries scored in a match
def get_centuries_in_match(match_individual_scores):	
    scores = [score for inning in match_individual_scores for score in inning[1]]
    scores_without_nulls = [score for score in scores if score is not None]
    centuries_scored = len([score for score in scores_without_nulls if score >= 100])
    return centuries_scored
	
# Add Deacde info to the individual scores in all innings of a Match.

def append_year_lower_5_by_country_individual(x):
    y = []
    for i in x['match_individual_scores']:
        y.append([x['decade'],i]) 
    return y
	
# Flatten Dismissal types of all the innings in a Test Match.

def flatten_dismissals(match_innings_dismissals):
    dismissals = [y for x in match_innings_dismissals for y in x if y is not None]
    return dismissals
	
# Map the instances where follow-on opportunity was available to the bowling Team.

def fo_opportunity_exists(match_innings_scores):
    if len(match_innings_scores) >= 2:
        first_inning_deficit = match_innings_scores[0][1] - match_innings_scores[1][1]
        if first_inning_deficit >= 200:
            fo_opportunity = 'yes'
        else :
            fo_opportunity = 'no'
    else :
        fo_opportunity = 'no'
    return fo_opportunity
	
#############################################################

	

