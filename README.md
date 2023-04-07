# PracticeTurkishBot

This repository, where the backend of telegram [**@PracticeTurkishBot**](https://t.me/PracticeTurkishBot) bot is implemented. 

## Features

The bot has several features.

### 1. Dictionary

If a user sends a message without commands to the bot, the content of the message is transtated from guessed language used to all other supported languages, e.g. from turkish to both English and Russian if message is written in turkish language.

The translation is looked up in several online translation services, most of which are dictionaries, so the best use of the feature is to translate single words/phrases.  

Supported languages:
- Turkish;
- Russian;
- English.

### 2. Morphology

If the recived text is a single word in turkish, and the word doesn't match its lemma, than the bot will perform morphology analysis.


#### Example with the word "gittim"
```
gitmek
>git   |Verb
+   ti |PastTense
+     m|1stPrsnSingular
=gittim|Verb
```
### 4. Translation mistakes logs

It is easy to pair the bot with [**PracticeTurkish**](https://github.com/FadeevEgor/PracticeTurkish) application. After doing so, it is possible to collect all translation mistakes made by you during a session to your telegram user via the bot.

### 3. Word of the day 

Each day it sends word of the day to all subscribed users.

### 4. Your translation mistakes hub

The bot can work as an extension for [PracticeTurkish](https://github.com/FadeevEgor/PracticeTurkish) CLI-application. With a proper configuration, It will send your translation mistakes to you via the bot.

## Hosting

The bot functionality is splitted between several [Google Cloud Functions](https://cloud.google.com/functions) and [AWS lambdas](https://aws.amazon.com/lambda/):
1. [PracticeTurkishBotFunction](./PracticeTurkishBotFunction) acts as the webhook for the bot: the function accepts HTTP POST request an ([update](https://core.telegram.org/bots/api#update)) for every interaction with the bot. Its responsibility is to parse every update and send back appropriate response. To do so, it employs other cloud functions in most cases.
2. [UsersTableFunction](./PracticeTurkishBotFunction) acts as a HTTP data API endpoint for a database with users data. It's responsible for performing all actions with regard to users data, such as adding new users, token verification, word of the day subscribtions, etc.
3. [TranslationFunction](./TranslationFunction) acts as a translation service: recieves text and responds with its translation.
4. [MorphologyFunction](./MorphologyFunction) acts as a morphology analysis service: recieves a turkish word and responds with its morphology analysis.
5. [RedirectFunction](./RedirectFunction) redirects a text from an incoming HTTP post request to a telegram user specified in the request, if given the correct user token.
6. [WordOfTheDayLambda](./WordOfTheDayLambda) sends turkish word of the day to every subscribed user. Invoked daily by [AWS EventBridge scheduler](https://aws.amazon.com/eventbridge/scheduler/).

First five listed services are google cloud functions, triggered by HTTP requests. The last one service is a AWS Lambda invoked by scheduler.
