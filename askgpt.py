import praw
import random
import time
import os
import openai
import yaml

subnum = 0

#Open secrets.yaml for sensitive info
with open("secrets.yaml", "r") as f:
    secrets = yaml.safe_load(f)

#openAI API key
openai.api_key = secrets["openai_api_key"]

#praw Auth info
reddit = praw.Reddit(client_id= secrets["reddit_client_id"],
                     client_secret=secrets["reddit_client_secret"],
                     username=secrets["reddit_username"],
                     password=secrets["reddit_password"],
                     redirect_uri=secrets["reddit_redirect_uri"],
                     user_agent='GPT Reddit Commenter 1.2b by /u/NermutBundaloy')

def chatgptget(prompt):#Send the prompt to ChatGPT for a response <- Not in use yet, will come into play when I dynamically get questions from ChatGPT
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=[{"role": "user", "content": prompt}]
        )
    return(response)


def findsubtitle(subnum):
    title = str(submission_titles[subnum]) #Get submission number (subnum) out of the list of titles
    title = title.replace("['","") #Clean up the title
    title = title.replace("']","")
    title = title.replace('["','')
    title = title.replace('"]','')
    return(title) #Send the submission title back to the main script

def countdown(t):#Generates a live countdown in the console
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(timer, end="\r")
        time.sleep(1)
        t -= 1
 
def waitthislong(time): #Wait for the number of seconds passed in 'time' before starting the script over
    mins, secs = divmod(time, 60)
    print(f"Waiting for {mins} minutes and {secs} seconds before the next post")
    countdown(int(time))

# MAIN SCRIPT#
os.system('clear') #Clear the console
with open('submission_titles.tsv', 'r') as f: #Get the list of submission titles - This will soon be automatically generated each time
    submission_titles = [line.strip().split('\n') for line in f.readlines()]

while True: #Start the loop
    timetowait=random.randint(21*60, 37*60) #Set how long the script will wait after a successful submission, to make another one.
    title = findsubtitle(subnum) #Get a submission title from the findsubtitle function
    print(title)
    subnum+=1 #increment the number of the submission we'll use by one
    
    try: 
        submission = reddit.subreddit('AskReddit').submit(title, selftext='')# Post the submission to the AskReddit subreddit
        waitthislong(timetowait) #Wait for the random time set at the beginning of the loop
    except Exception as e: #If this doesn't work (usually because we're rate limited)
        print('----------------')
        print(e) #Print the error
        print('----------------')
        if 'RATELIMIT' in str(e): #check if the phrase 'RATELIMIT' is in the error - If it is, we want to wait for the amount of time Reddit requires us to wait before trying again. Add 60 seconds to be safe.
            ratelimittime = str(e)
            ratelimittime = ratelimittime.split('break for ')[1] #Parse the error text by discarding the portion preceding the phrase 'break for '
            ratelimittime = ratelimittime.split( )[0] # Parse the error text by discarding the portion after the next space. This should leave us with the number of minutes we're meant to wait.
            ratelimittime = int(ratelimittime)*60 #Multipy the number of minutes by 60
            timetowait = int(ratelimittime)+60 # Add a minute on the end
            print('As the post did not submit, I will resubmit the following question when the timer expires:')
            subnum -=1 #Decrement the number of the submission we'll use, as it didn't successfully post last time
            waitthislong(timetowait)
            pass
        else:
            print(f"The following error caused the script to crash: {e}")
            
