#Final Project
# Name= Brandon Punturo
#Importing Libraries
import requests
import facebook
import json
import time
import requests
import sqlite3
import plotly
from wordcloud import WordCloud
import plotly.plotly as py
import plotly.graph_objs as Go
import matplotlib.pyplot as plt
import keys

#Tokens
facebook_token=keys.facebook_token
tastekid_delve=keys.tastekid_delve
NY_times_key=keys.NY_times_key
newsapi_key=keys.newsapi_key
plotly_key=keys.plotly_key

#base_urls
newsapi_endpoint="https://newsapi.org/v2/everything"
nytimes="https://api.nytimes.com/svc/search/v2/articlesearch.json"
taste_kid="https://tastedive.com/api/similar"
plotly.tools.set_credentials_file(username='bpunt', api_key=plotly_key)

#setting up Facebook, and pyplot
graph = facebook.GraphAPI(access_token=facebook_token)
plotly.tools.set_credentials_file(username='bpunt', api_key=plotly_key)

#Cache Stuff
CACHE_FNAME="results.json"
CACHE_FNAME2="results2.json"

#Initiating Cache1
try:
    cache_file = open(CACHE_FNAME, 'r') # Try to read the data from the file
    cache_contents = cache_file.read()  # If it's there, get it into a string
    CACHE_DICTION = json.loads(cache_contents) # And then load it into a dictionary
    cache_file.close() # Close the file, we're good, we got the data in a dictionary.
except:
    CACHE_DICTION = {}
#Initiating Cache2
try:
    cache_file = open(CACHE_FNAME2, 'r') # Try to read the data from the file
    cache_contents = cache_file.read()  # If it's there, get it into a string
    CACHE_DICTION2 = json.loads(cache_contents) # And then load it into a dictionary
    cache_file.close() # Close the file, we're good, we got the data in a dictionary.
except:
    CACHE_DICTION2 = {}

 #This function is retrieving My Facebook Likes
def get_facebook_likes():
    global CACHE_DICTION
    if "likes" in CACHE_DICTION.keys():
        print("Data was in the cache")
        return(CACHE_DICTION)
    else:
        print("fetching Facebook Likes")
        posts = graph.get_object(id="me", fields="likes")
        try:
            CACHE_DICTION=posts
            dumped_json_cache=json.dumps(CACHE_DICTION)
            fw=open(CACHE_FNAME,"w")
            fw.write(dumped_json_cache)
            fw.close
            return CACHE_DICTION
        except:
            print("Wasn't in cache and wasn't valid search either")
            return None

#Runnning Function
likes=get_facebook_likes()

#Initializing Sqlite3 Database
connection=sqlite3.connect("Final_Project_206.sqlite")
cursor=connection.cursor()

#Dropping Tables
cursor.execute("DROP TABLE IF EXISTS Facebook_Likes")
cursor.execute("DROP TABLE IF EXISTS Recommendations")
cursor.execute("DROP TABLE IF EXISTS news_API_articles")
cursor.execute("DROP TABLE IF EXISTS NY_Times_articles")

#Creating Facebook_Likes Table
cursor.execute("CREATE TABLE Facebook_Likes(Object_Liked TEXT NOT NULL PRIMARY KEY , id TEXT, date_liked date)")

#Adding My Facebook Like Data to the table
for likes in likes["likes"]["data"]:
	name=likes["name"]
	ID=likes["id"]
	created_time=likes["created_time"]
	tup=name,ID,created_time
	cursor.execute("INSERT INTO Facebook_Likes(Object_Liked,id,date_liked) VALUES (?,?,?)", tup)
connection.commit()

#FIRST VISUALIZATION
#Seeing how many of my likes correspond to what year
dates=cursor.execute("SELECT date_liked FROM Facebook_Likes")
fetch=dates.fetchall()

new_dict={}
for date in fetch:
	date_of_like=str(json.loads(date[0][:4]))
	if date_of_like in new_dict:
		new_dict[date_of_like]+=1
	else:
		new_dict[date_of_like]=1

#Appending years to a lists
keys=[]
for key in new_dict.keys():
	keys.append(key)

#Appending the corresponding values to a list
values=[]
for value in new_dict.values():
	values.append(value)
layout = Go.Layout(
    title='Likes Per Year',
    xaxis=dict(
        title='Year',
        titlefont=dict(
            family='Courier New, monospace',
            size=18,
            color='#7f7f7f'
        )
    ),
    yaxis=dict(
        title='Number of Likes',
        titlefont=dict(
            family='Courier New, monospace',
            size=18,
            color='#7f7f7f'
        )
    )
)
#Creating a Bar Plot
data=[Go.Bar(x=[keys[0],keys[1],keys[2],keys[3],keys[4]],y=[values[0],values[1],values[2],values[3],values[4]])]
fig = Go.Figure(data=data, layout=layout)
py.iplot(fig,filename="Years")

#Defining a Function that gets a list of recommendations given my likes
def get_recommendations(x):
	global CACHE_DICTION
	if x in CACHE_DICTION.keys() or x in CACHE_DICTION2.keys():
		print("Retrieving Retrieving Recommendation Data")
		return CACHE_DICTION
	else:
		print("Print Fetching Recommendation Data")
		params={"k":tastekid_delve,"q":x,"verbose":"1"}
		get_recommendation=requests.get(taste_kid,params=params)
		recommended=json.loads(get_recommendation.text)
		if recommended["Similar"]["Info"][0]["Type"]=="unknown":
			try:
				CACHE_DICTION2[x]=recommended
				
				dumped_json_cache=json.dumps(CACHE_DICTION2)
				fw=open(CACHE_FNAME2,"w")
				fw.write(dumped_json_cache)
				return CACHE_DICTION2
			except:
				print("something went wrong")
		else:
			
			try:
				CACHE_DICTION[x]=recommended
				dumped_json_cache=json.dumps(CACHE_DICTION)
				fw=open(CACHE_FNAME,"w")
				fw.write(dumped_json_cache)
				fw.close()
				return CACHE_DICTION
			except:
				print("Something went wrong")

#Running the function
names_of_likes=cursor.execute("SELECT Object_Liked FROM Facebook_Likes")
liked_data=names_of_likes.fetchall()

for like in liked_data:
	get_recommendations(like[0])

#Creating a table in the database for the recommendations
cursor.execute("CREATE TABLE Recommendations(Liked_Object TEXT , Type TEXT, Recommendation date, FOREIGN KEY(Liked_Object) REFERENCES Facebook_Likes(Object_Liked))")

i=0
#This long for loop adds the recommendations to the database
for key in CACHE_DICTION.keys():
	if i <3 or i >=12:
		"stop"
	else:
		cached=CACHE_DICTION[key]
		name=cached["Similar"]["Info"][0]["Name"]
		Type=cached["Similar"]["Info"][0]["Type"]
		Recommendation=cached["Similar"]["Results"][0]["Name"]
		Recommendation_2=cached["Similar"]["Results"][1]["Name"]
		Recommendation_3=cached["Similar"]["Results"][2]["Name"]
		tup=name,Type,Recommendation
		tup2=name,Type,Recommendation_2
		tup3=name,Type,Recommendation_3
		cursor.execute("INSERT INTO Recommendations(Liked_Object,Type,Recommendation) VALUES (?,?,?)", tup)
		cursor.execute("INSERT INTO Recommendations(Liked_Object,Type,Recommendation) VALUES (?,?,?)", tup2)
		cursor.execute("INSERT INTO Recommendations(Liked_Object,Type,Recommendation) VALUES (?,?,?)", tup3)
	i+=1	
connection.commit()

# Creating a Function that uses the nytimes api to serach articles from the recommendations list
def cache_nytimesarticles(x):
	global CACHE_DICTION
	if x in CACHE_DICTION.keys():
		print("Retrieving NY Times Articles")
		return CACHE_DICTION
	else:
		print("Fetching NY Times articles")
		params={"q": x,"api-key":"153aa45089f141d0ba1bed4bb257f056"}
		nytimes_articles=requests.get(nytimes,params=params)
		text=json.loads(nytimes_articles.text)
		time.sleep(2)#NY Times API only allows 1 request per second- so I cause a pause.
		try:
			CACHE_DICTION[x]=text
			dumped_json_cache=json.dumps(CACHE_DICTION)
			fw=open(CACHE_FNAME,"w")
			fw.write(dumped_json_cache)
			return CACHE_DICTION
		except:
			print("something went wrong")

#Running the Function
names_of_recommendations=cursor.execute("SELECT Recommendation FROM Recommendations")
recommendations_data=names_of_recommendations.fetchall()
for recommended in recommendations_data:	
	cache_nytimesarticles(recommended[0])

cursor.execute("CREATE TABLE NY_Times_articles(Recommended_item TEXT , web_url TEXT, snippet TEXT,publication_date Date)")
#Creating the NY_Times database

#Adding the data into the database
i=0
for keys in CACHE_DICTION.keys():
	if i <=12:
		"stop"
	else:
		cached=CACHE_DICTION[keys]
		try:
			for recommendation_articles in cached["response"]["docs"]:
				name=keys
				url=recommendation_articles["web_url"]
				snipp=recommendation_articles["snippet"]
				pub_date=recommendation_articles["pub_date"]
				tup=name,url,snipp,pub_date
				cursor.execute("INSERT INTO NY_Times_articles(Recommended_item ,web_url,snippet,publication_date) VALUES (?,?,?,?)", tup)
		except:
			print("NY Times screwed this up")
		#There is a try and except here because sometimes the nytimes api could not convert some recommendations into searches
	i+=1
connection.commit()

#Defining a function that uses the newsapi function to retrieve articles about the recommended items
def cache_newsapiarticles(x):
	global CACHE_DICTION2
	if x in CACHE_DICTION2.keys():
		print("Retrieving Newsapi Articles")
		return CACHE_DICTION2
	else:
		print("Fetching Newsapi Articles")
		params={"q": x,"apiKey":newsapi_key}
		newsapi_articles=requests.get(newsapi_endpoint,params=params)
		text=json.loads(newsapi_articles.text)
		try:
			CACHE_DICTION2[x]=text
			dumped_json_cache=json.dumps(CACHE_DICTION2)
			fw=open(CACHE_FNAME2,"w")
			fw.write(dumped_json_cache)
			return CACHE_DICTION2
		except:
			print("something went wrong")
#Running the function
for recommended in recommendations_data:	
	cache_newsapiarticles(recommended[0])

cursor.execute("CREATE TABLE news_API_articles(Recommended_item TEXT , web_url TEXT, snippet TEXT,publication_date Date, Website,TEXT )")
#Creating the database table for this data
#Adding the data to the database

i=0
for key in CACHE_DICTION2.keys():
	if i <= 15:
		
		"pass"
	else:
		
		for article in CACHE_DICTION2[key]["articles"]:
			title=article["title"]
			url=article["url"]
			pub_date=article["publishedAt"]
			web_site=article["source"]["name"]
			tup=key,url,title,pub_date,web_site
			cursor.execute("INSERT INTO news_API_articles(Recommended_item ,web_url,snippet,publication_date,Website) VALUES (?,?,?,?,?)", tup)
	i+=1
connection.commit()
#Creating a Wordcloud
website=cursor.execute("SELECT Website FROM news_API_articles")
website_name=website.fetchall()
all_websites=[]
for website in website_name:
	all_websites.append(website[0])
website_blurb=""
for website in all_websites:
	website_blurb= website_blurb + " " + website

wordcloud = WordCloud(max_font_size=40).generate(website_blurb)
plt.figure()
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.title("WordCloud with websites that Newsapi brings up most often ")
plt.savefig("Wordcloud.png")
plt.show()

