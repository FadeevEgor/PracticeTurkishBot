# PracticeTurkishBot

This repository, where the backend of telegram [**@PracticeTurkishBot**](https://t.me/PracticeTurkishBot) bot is implemented. 

## Features

The bot has two features.

### 1. Dictionary

If a user sends a message without commands to the bot, the content of the message is transtated from guessed language used to all other supported languages, e.g. from turkish to both English and Russian if message is written in turkish language.

The translation is looked up in several online translation services, most of which are dictionaries, so the best use of the feature is to translate single words/phrases.  

Supported languages:
- Turkish;
- Russian;
- English.

### 2. Translation mistakes logs

It is easy to pair the bot with [**PracticeTurkish**](https://github.com/FadeevEgor/PracticeTurkish) application. After doing so, it is possible to collect all translation mistakes made by you during a session to your telegram user via the bot.

## Host

It uses [Google Cloud Functions Service](https://cloud.google.com/functions) as the host. Each http request triggers **http** function in the main module.
