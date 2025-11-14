**Title:** UK News Telegram Bot.

**Brief overview:** An automated system for delivering curated news articles sourced from leading online publications.

**Main features:**

* PERSONALIZED news delivery by subscription
* Secure MySQL database for news articles, and user data
* Web scrapping of the biggest UK news websites using BeautifulSoup
* Secure user password protection using bcrypt
* Many commands to help users navigate
**Technologies used:** 
* Python - programming language
* MySQL - for databases
* Telegram - messanger for user interaction
* BeautifulSoup - library for web scraping
* requests - library used to send HTTP requests
* telegram - ibrary used to operate telegram bot
* asyncio - library for running asynchronous functions
* mysql - library to operate MySQL database
* bcrypt - library for user password hashing
* 
**Getting started:**

### Prerequisites
Before running the bot, you need to have the following installed:
* Python 3.8+
* MySQL Database instance running locally or remotely.

### Step 1: Clone the Repository
Open your terminal or command prompt and run the following command to download the source code:
[git clone https://github.com/1dessyatov/UK_News_Telegram_Bot.git
cd UK_News_Telegram_Bot]

### Step 2: Set Up the Environment

Create a Virtual Environment:

`python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate`

Install Dependencies:

`pip install -r requirements.txt`

### Step 3: Configure Database and Secrets

Create a file named .env in the project root directory and add your secret credentials. Do not commit this file to Git.

#### .env file content:

TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
DB_HOST="localhost"
DB_USER="root"
DB_PASSWORD="your_database_password"
DB_NAME="news_database"

### Step 4: Initialize the Database Schema

Before running the bot, you must create the necessary tables in your MySQL database.

Access your MySQL environment (e.g., using MySQL Workbench or the command line).

Ensure a database named news_database (or the name specified in .env) exists.

Run the main.py file once. The function create_tables() will automatically set up the tables (users, articles, subjects, etc.) as defined in the code.

### Step 5: Run the Bot

Execute the main script to start the bot:

`python main.py`
The bot is now running and will begin the hourly news scraping task in the background. Open Telegram and start interacting with your bot by sending the /start command!

**Main telegram bot commands:**

/start - Begin interaction with the bot
/login - Log in to your account
/register - Create a new account
/logout - Log out of your account
/info - View your account info
/preferences - Manage your news preferences
/add "subject" - Add a preference
/remove "subject" - Remove a preference
/clearpreferences - Clear the list of your preferences
/cancel - Cancel current operation
