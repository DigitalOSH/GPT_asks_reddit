import yaml
import openai
import praw
from praw.models import Message
import random
import simplejson as json
import time
import os

#Open secrets.yaml for sensitive info
with open("secrets.yaml", "r") as f:
	secrets = yaml.safe_load(f)

#openAI
openai.api_key = secrets["openai_api_key"]

#praw
reddit = praw.Reddit(client_id= secrets["reddit_client_id"],
					 client_secret=secrets["reddit_client_secret"],
					 username=secrets["reddit_username"],
					 password=secrets["reddit_password"],
					 redirect_uri=secrets["reddit_redirect_uri"],
					 user_agent='GPT Reddit Commenter 1.2b by /u/NermutBundaloy')

#Authorize with Reddit
#reddit.auth.authorize('a5j6KrVbGzvE3EQ_HGwHulGeWaJv5w')

def checkredditinbox():  #Check the reddit inbox for unread messages, and put them into a 'dict'.
	unread_messages = reddit.inbox.unread()
	unread_dict = {'permalink':[], 'body': []} #make a 'dict' - basically a nested list where comments and their permalinks will be stored.
	for message in unread_messages:
	# check if the message is a root-level comment and a reply to your post
		if isinstance(message, praw.models.Comment) and message.is_root:
			# get the permalink to the comment
			permalink = f"https://www.reddit.com{message.submission.permalink}{message.id}/"
			# get the message contents
			message_text = message.body
			unread_dict['permalink'].append(permalink) #Append the permalink to the comment into our dict
			unread_dict['body'].append(message.body) #Append the comment into our dict
			message.mark_read() #Mark the message as read once it enters the comment parser
	return(unread_dict) #Send the dict we just created back to the main scrupt

def checkredditreplies(): #Will comment on this later, if I put it into use.
	for reply in reddit.inbox.comment_replies():
		permalink = f"https://www.reddit.com{reply.submission.permalink}{reply.id}/"
	return(reply.body, permalink)

def getpostpermalink(pl): #Uses the comment permalink to derive the permalink for the post the comment was in response to
	permalink = pl.split("/comments/")[1] #Splits the comment permalink at the text "/comments/" and saves the portion that comees after it
	permalink = permalink.split("/")[0] #Splits the saved portion at the next "/" and saves the portion that came before it
	permalink = f"http://reddit.com/{permalink}/" #Takes the saved portion and formats it into a Reddit URL
	return(permalink)

def shouldirespond(inbox): #A basic lottery giving a comment a 1 in 10 chance of receiving a response
	msgid = 0 #This tells the script that we're starting at message 0. This is necessary later, to explain which comment in the dict we're responding to
	for msg in inbox['body']:
		rando = random.randint(1,5) #Generates a random number between the values mentioned
		if rando == 3 and "I am a bot, and this action was performed automatically" not in msg: #If the random number is 3, we will respond to it. If it's automod, we won't 
			return(msgid) #Send back the message ID number to the main script, so it knows which message we're responding to
			break #End this function
		else:
			pass
		msgid += 1 #Incremeent the message ID up by one, since the last message was not accepted for response
	return('None')

def constructprompt(commentbody, msglink, postlink): #Construct a prompt for ChatGPT based on the post title, the body (if applicable) and the comment we'r responding to
	submission = reddit.submission(url=postlink) #Gets the information about the post from reddit
	try:
		if submission.selftext == '': #If there's no body to the post, use this prompt
			prompt = f"I posed the question ''{submission.title}''. Someone responded with ''{commentbody}''. Give me a witty, short, casual response. Make this response sound natural, exclude any wording about being an AI language model. Be charming and funny. Never mention that you're an AI or language model. Never use the words \"language model\" or \"AI\""
		else: #If there is a body to the post, use this prompt
			prompt = f"I said {submission.title}. I elaborated by stating {submission.selftext}. Someone responded with {commentbody}. Give me a witty, short, casual response. Make this response sound natural, exclude any wording about being an AI language model. Be charming and funny."
	except Exception as e:
		pass
	return(prompt) #send the prompt back to the main script

def askgpt(prompt): #Send the prompt to ChatGPT for a response
	response = openai.ChatCompletion.create(
	model="gpt-3.5-turbo", 
	messages=[{"role": "user", "content": prompt}]
	)
	content = response['choices'][0]['message']['content'] #Parse out just the response
	content = content.lstrip()
	if content.startswith('"') and content.endswith('"'):
		content = content[1:-1]
	return(content) #Send the response back to the main script

def respondtocomment(msglink, response): #Actually post ChatGPT's response to the comment on Reddit
	comment = reddit.comment(url=msglink) #Mention which comment we're interacting with
	if not comment.saved: #If the comment wasn't previously, saved, respond to it
		comment.reply(response) #Post the response
		comment.save() #Save the comment so we don't accidentally respond to it twice
		comment.upvote() #Upvote the comment we're responding to
	else:
		print('Skipped as already commented')

def waitthislong(time): #Wait for a random amount of time before starting the script over
    mins, secs = divmod(time, 60)
    print(f"Waiting for {mins} minutes and {secs} seconds before the next post")
    countdown(int(time))

def countdown(t): #Generates a live countdown in the console
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(timer, end="\r")
        time.sleep(1)
        t -= 1

#MAIN SCRIPT#
os.system('clear')
while True:
	try:
		inbox=checkredditinbox()
		msgid = shouldirespond(inbox)
		if msgid == 'None':
			print('No messages won the ChatGPT response lottery')
			print('----------------------------')
			waitthislong(random.randint(1*30, 2*30))
			pass
		else:
			print('Received the following response and elected to respond to it')
			print('----------------------------')
			print(inbox['body'][msgid])
			permalink = getpostpermalink(inbox['permalink'][msgid])
			prompt = constructprompt(inbox['body'][msgid], inbox['permalink'][msgid], permalink)
			print('-----')
			print('Here is how I constructed my question to ChatGPT')
			print('-----')
			print(prompt)
			gptresponse = askgpt(prompt)
			print('-----')
			print('Here\'s how ChatGPT responded')
			print('-----')
			print(gptresponse)
			print('----------------------------')
			respondtocomment(inbox['permalink'][msgid], gptresponse)
			waitthislong(random.randint(11*60, 22*60))
	except Exception as e:
		print(e)
