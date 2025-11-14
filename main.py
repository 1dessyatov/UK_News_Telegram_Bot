# Telegram News Bot

#                                               LIBRARY IMPORTS
import os
from dotenv import load_dotenv #Library to import variables from .env file

from bs4 import BeautifulSoup  # Library for web scraping
import requests  # To send HTTP requests

from telegram import Bot, Update  # Telegram bot API imports
from telegram.ext import ContextTypes, Application, CommandHandler  # Telegram bot framework

import asyncio  # To run asynchronous functions
import mysql.connector  # MySQL database connection
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import bcrypt # Password hashing


load_dotenv()
# Initializing the Telegram bot with a token
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)


# Function to establish a connection to the MySQL database
def create_connection():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    return connection



#                                               CREATING DATABASE

#Initializes normalized database schema with foreign key relationships
def create_tables():
    connection = create_connection()
    cursor = connection.cursor()
    try:
        # Subjects table (1st normal form)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL
            )
        ''')
        # Articles table (relates to subjects)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                publicationTime VARCHAR(255),
                link VARCHAR(255) UNIQUE,
                subject_id INT,
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            )
        ''')
        # Users table (secure authentication)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(255) PRIMARY KEY,
                realname VARCHAR(255) NOT NULL,
                password_hash BLOB NOT NULL
            )
        ''')

        # Session management table
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS username_telegramID (
                        telegram_id BIGINT PRIMARY KEY,
                        username VARCHAR(255),
                        FOREIGN KEY (username) REFERENCES users(username)
                    )
                ''')
        # User preferences junction table (many-to-many)
        cursor.execute('''
                            CREATE TABLE IF NOT EXISTS user_preferences (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                username VARCHAR(255),
                                subject_id INT,
                                FOREIGN KEY (username) REFERENCES users(username),
                                FOREIGN KEY (subject_id) REFERENCES subjects(id)
                            )
                        ''')

    except():
        print("Error with creating tables")
    connection.commit()
    cursor.close()
    connection.close()



#                                               CORE DATA MODEL

#Inserting new subject to the database
def insert_subject(subject_name):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT id FROM subjects WHERE name = %s', (subject_name,))
    result = cursor.fetchone()
    if result is None:
        cursor.execute('INSERT INTO subjects (name) VALUES (%s)', (subject_name,))
        connection.commit()
        subject_id = cursor.lastrowid
    else:
        subject_id = result[0]
    cursor.close()
    connection.close()
    return subject_id

# Function to check if an article already exists in the database
def article_exists(link):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT id FROM articles WHERE link = %s', (link,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result is not None

# Function to check if a user already exists in the subscribers list
def user_exists(username):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result is not None

# Function to add a new user to the subscribers list
def insert_user(username,realname,password_hash):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('INSERT INTO users (username, realname, password_hash) VALUES (%s, %s, %s)', (username, realname, password_hash))
    connection.commit()
    cursor.close()
    connection.close()

# Function to add a new user session to the database
def insert_username_telegramid(telegram_id,username):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('INSERT INTO username_telegramID (username, telegram_id) VALUES (%s, %s)',
                   (username, telegram_id))
    connection.commit()
    cursor.close()
    connection.close()


# Function to remove a user session from the database
def remove_user_session(telegram_id):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM username_telegramID WHERE telegram_id = %s', (telegram_id,))
    connection.commit()
    cursor.close()
    connection.close()


# Function to get all usernames from the subscribers list
def get_all_usernames():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT username FROM users')
    usernames = [row[0] for row in cursor.fetchall()]
    cursor.close()
    connection.close()
    return usernames

# Function to get all telegram ids of current sessions
def get_all_telegram_ids():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT telegram_id FROM username_telegramID')
    telegramids = [row[0] for row in cursor.fetchall()]
    print(telegramids)
    cursor.close()
    connection.close()
    return telegramids


# Function to get user's real name
def get_user_realname(username):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT realname FROM users WHERE username = %s', (username,))
    realname = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    return realname

# Function to get user's password
def get_user_password(username):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE username = %s', (username,))
    password_hash = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    return password_hash

# Function to get user's preferences
def get_user_preferences(username):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT name FROM subjects INNER JOIN user_preferences ON subjects.id = user_preferences.subject_id WHERE username = %s', (username,))
    preferred_subjects = [row[0] for row in cursor.fetchall()]
    cursor.close()
    connection.close()
    return preferred_subjects

# Function to add a preference to user's list of preferences
def add_user_preference(username,subject_name):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('INSERT INTO user_preferences (username, subject_id) VALUES (%s, (SELECT id FROM subjects WHERE name = %s))', (username, subject_name))
    connection.commit()
    cursor.close()
    connection.close()

# Function to get all available subjects
def get_all_subjects():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT name FROM subjects WHERE name NOT IN ("Unknown", "n/a")')
    subjects = [row[0] for row in cursor.fetchall()]
    cursor.close()
    connection.close()
    return subjects

# Function to check if user has a particular preference
def check_user_preference(username,subject_name):
    user_preferences = get_user_preferences(username)
    if subject_name in user_preferences:
        return True
    else:
        return False

# Function to remove a preference from user's list of preferences
def remove_user_preference(username,subject_name):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM user_preferences WHERE username = %s AND subject_id = (SELECT id FROM subjects WHERE name = %s)', (username, subject_name))
    connection.commit()

# Function to empty user's list of preferences
def clear_user_preferences(username):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM user_preferences WHERE username = %s', (username,))
    connection.commit()
    cursor.close()
    connection.close()

# Function to get user's username from telegram id
def get_username(telegram_id):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT username FROM username_telegramID WHERE telegram_id = %s', (telegram_id,))
    username = cursor.fetchone()[0]
    return username

# Function to add a new article to the articles list
def insert_article(article):
    if article_exists(article.link):
        print(f"Article already exists in the database: {article.title}")
        return False
    connection = create_connection()
    cursor = connection.cursor()
    subject_id = insert_subject(article.subject)
    try:
        cursor.execute('''
            INSERT INTO articles (title, publicationTime, link, subject_id)
            VALUES (%s, %s, %s, %s)
        ''', (article.title, article.publicationTime, article.link, subject_id))
        connection.commit()
        print(f"Inserted article: {article.title}")
        return True
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    cursor.close()
    connection.close()

# Function to check a session is going for telegram id
def check_session(telegram_id):
    telegram_ids = get_all_telegram_ids()
    if telegram_id in telegram_ids:
        return True
    else:
        return False


# Function to remove all articles from the articles list
def clear_articles():
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM articles")
        connection.commit()
        print("All articles deleted successfully.")
    except mysql.connector.Error as err:
        print(f"Error while deleting articles: {err}")
    cursor.close()
    connection.close()

# Function to escape MarkdownV2 symbols
def escape_markdownv2(text):
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)


# Article class to hold article data
class Article:
    def __init__(self, title, subject, publicationTime, link):
        self.title = title
        self.subject = subject
        self.publicationTime = publicationTime
        self.link = link




#                                       WEB SCRAPING SERVICE


# Scrapes BBC using CSS class heuristics with fault tolerance
def get_latest_articles_from_bbc():
    articles = []
    response = requests.get("http://www.bbc.co.uk/news/")
    soup = BeautifulSoup(response.content, 'html.parser')
    try:
        # Getting a list of the latest articles
        articles_list = soup.find_all('ul', {'class': 'ssrcss-y8stko-Grid e12imr580'})
    except Exception as e:
        print(f"Error with receiving metadata from BBC: {e}")
        return articles
    if articles_list:
        li_elements = articles_list[0].find_all('li') #Getting each article to obtain more data
        for li in li_elements:
                try:
                    link = li.find('a', href=True)
                    if link:
                        href = link['href']
                        if href.startswith('/'):
                            title_element = li.find('p')
                            subject_element = li.find('span', {'class': 'ssrcss-1pvwv4b-MetadataSnippet e4wm5bw3'})
                            publication_time_element = li.find('span', {'class': 'visually-hidden ssrcss-1f39n02-VisuallyHidden e16en2lz0'})
                            article_title = title_element.text if title_element else "No Title"
                            article_subject = subject_element.text if subject_element else "Unknown"
                            article_publicationTime = publication_time_element.text if publication_time_element else "No Time"
                            if article_publicationTime.startswith("."): #Handling an input of Live news
                                article_publicationTime = "Live"
                            article_link = f"https://www.bbc.co.uk{href}"
                            if article_title != "No Title":
                                article = Article(article_title, article_subject, article_publicationTime, article_link)
                                articles.append(article)
                                if len(articles) >= 6: # Rate limiting
                                    break
                except Exception as ex:
                    print(f"Error parsing BBC article: {ex}")
    return articles

# Scrapes The Guardian using CSS class heuristics with fault tolerance
def get_latest_articles_from_guardian():
    articles = []
    response = requests.get("https://www.theguardian.com/uk")
    soup = BeautifulSoup(response.content, 'html.parser')
    try:
        # Getting a list of the latest articles
        articles_list = soup.find_all('ul', {'class': 'dcr-68r5kg'})
    except Exception as e:
        print(f"Error with receiving metadata from The Guardian: {e}")
        return articles
    if articles_list:
        li_elements = articles_list[0].find_all('li') #Getting each article to obtain more data
        for li in li_elements:
                try:
                    link = li.find('a', href=True)
                    if link:
                        href = link['href']
                        if href.startswith('/'):
                            title_element = link.get('aria-label')
                            subject_element = li.find('div', {'class': 'dcr-1cc5b8d'})
                            time_element = li.find('time')
                            article_title = title_element if title_element else "No Title"
                            article_subject = subject_element.text if subject_element else "Unknown"
                            article_publicationTime = time_element.text if time_element else "No Time"
                            article_link = f"https://www.theguardian.com{href}"
                            article = Article(article_title, article_subject, article_publicationTime, article_link)
                            articles.append(article)
                            if len(articles) >= 6: # Rate limiting
                                break
                except Exception as e:
                    print(f"Error parsing The Guardian article: {e}")
    return articles


#                                       NOTIFICATION ENGINE

# Orchestrates scraping->storage->delivery pipeline
async def print_latest_news():
    articles_bbc = get_latest_articles_from_bbc()
    articles_guardian = get_latest_articles_from_guardian()
    telegram_ids = get_all_telegram_ids()
    if len(articles_bbc) >= 3:
        for article in articles_bbc:
            is_new = insert_article(article) # Checking if the article is not already in database
            if is_new:
                # Escaping MarkdownV2 symbols for each text
                article.title = escape_markdownv2(article.title)
                article.subject = escape_markdownv2(article.subject)
                article.publicationTime = escape_markdownv2(article.publicationTime)
                article.link = escape_markdownv2(article.link)
                # Generating a representation of a new article
                message = (
                    f"*{article.title}*\n"
                    f"_Subject: {article.subject}_\n"
                    f"_Publication time: {article.publicationTime}_\n"
                    f"[Read Article]({article.link})\n"
                    f"BBC"
                )
                for user_id in telegram_ids:
                    username = get_username(user_id)
                    realname = get_user_realname(username)
                    #Checking if the article subject is preferable for each user:
                    if check_user_preference(username, article.subject):
                        if article.title != "No Title" and article.title != "n/a":
                            #Sending a personalized message
                            await bot.send_message(chat_id=user_id, text=f"{realname}, this article may be interesting for you\\.\n" + message, parse_mode="MarkdownV2")

    if len(articles_guardian) >= 3:
        for article in articles_guardian:
            is_new = insert_article(article) # Checking if the article is not already in database
            if is_new:
                # Escaping MarkdownV2 symbols for each text
                article.title = escape_markdownv2(article.title)
                article.subject = escape_markdownv2(article.subject)
                article.publicationTime = escape_markdownv2(article.publicationTime)
                article.link = escape_markdownv2(article.link)
                # Generating a representation of a new article
                message = (
                    f"*{article.title}*\n"
                    f"_Subject: {article.subject}_\n"
                    f"_Publication time: {article.publicationTime}_\n"
                    f"[Read Article]({article.link})\n"
                    f"The Guardian"
                )
                for user_id in telegram_ids:
                    username = get_username(user_id)
                    realname = get_user_realname(username)
                    # Checking if the article subject is preferable for each user:
                    if check_user_preference(username, article.subject):
                        if article.title != "No Title" and article.title != "n/a":
                            await bot.send_message(chat_id=user_id,
                                                   # Sending a personalized message
                                                   text=f"{realname}, this article may be interesting for you.\n" + message, parse_mode="MarkdownV2")





#                                            CONVERSATION HANDLERS

REGISTER_USERNAME, REGISTER_REALNAME, REGISTER_PASSWORD, LOGIN_USERNAME, LOGIN_PASSWORD = range(5)

# A function dealing with /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    if not check_session(telegram_id):
        await update.message.reply_text("Welcome\\! Are you a new user or existing user?\nType */register* or */login*\nIf you need to cancel current operation, type */cancel*",parse_mode="MarkdownV2")
    else:
        await update.message.reply_text("Welcome back\\! You are already logged in\\. Type */info* to get details about your account\\.\nIf you need to cancel current operation, type */cancel*",parse_mode="MarkdownV2")
        return ConversationHandler.END

#A function dealing with /info command
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    if not check_session(telegram_id):
        await update.message.reply_text(
            f"You are not logged in\\. Type */register* or */login* to log in or register\\.\nIf you need to cancel current operation, type */cancel*",parse_mode="MarkdownV2")
        return ConversationHandler.END
    username = get_username(telegram_id)
    realname = get_user_realname(username)
    await update.message.reply_text(f"Your account details are as follows:\nUsername: {username}\nReal name: {realname}\nType */logout* to log out",parse_mode="MarkdownV2")
    return ConversationHandler.END

# Finite state machine for user registration
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    if check_session(telegram_id):
        await update.message.reply_text("You are already logged in\\. Type */info* to get details about your account\\.\nIf you need to cancel current operation, type */cancel*",parse_mode="MarkdownV2")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Enter a username:")
        return REGISTER_USERNAME

# Function handling /login command
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    if check_session(telegram_id):
        print("User already logged in")
        await update.message.reply_text(
            "You are already logged in\\. Type */info* to get details about your account\\.\nIf you need to cancel current operation, type */cancel*",parse_mode="MarkdownV2")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Enter your username:")
        return LOGIN_USERNAME

#Function handling /logout command
async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    if check_session(telegram_id):
        remove_user_session(telegram_id)
        await update.message.reply_text("You have been logged out successfully.")
    else:
        await update.message.reply_text("You are not logged in.")
    return ConversationHandler.END

#Function handling /preferences command
async def preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    if check_session(telegram_id):
        username = get_username(telegram_id)
        user_preferences = get_user_preferences(username)
        pref_text = "\n".join(user_preferences) if user_preferences else "No preferences"
        subj_text = "\n".join(get_all_subjects())
        await update.message.reply_text(
            f"Your current preferences:\n{pref_text}\n\n"
            f"Available subjects:\n{subj_text}\n\n"
            f"Available commands to manage your preferences:")
        await update.message.reply_text(
            "You can add preferences by typing */add* _subject_\n"
            "You can remove preferences by typing */remove* _subject_\n"
            "You can clear your preferences by typing */clearpreferences*\n",parse_mode="MarkdownV2"

        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            f"You are not logged in\\. Type */register* or */login* to log in or register\\.\nIf you need to cancel current operation, type */cancel*",parse_mode="MarkdownV2")
        return ConversationHandler.END

# Function to clear all user's preferences from the database
async def clearpreferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    if check_session(telegram_id):
        username = get_username(telegram_id)
        clear_user_preferences(username)
        await update.message.reply_text("Your preferences have been cleared successfully.")
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            f"You are not logged in\\. Type */register* or */login* to log in or register\\.\nIf you need to cancel current operation, type */cancel*",parse_mode="MarkdownV2")
        return ConversationHandler.END

# Function handling /add command to add user's preference to the database
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    if check_session(telegram_id):
        username = get_username(telegram_id)
        if not context.args:
            await update.message.reply_text("Please specify a subject to add. Example: /add Middle East")
            return

        subject = ' '.join(context.args)
        if subject in get_all_subjects():
            if not check_user_preference(username, subject):
                add_user_preference(username, subject)
                await update.message.reply_text(f"Preference added successfully: {subject}")
                return ConversationHandler.END
            else:
                await update.message.reply_text(f"Subject is already in your list of preferences.")
                return ConversationHandler.END
        else:
            await update.message.reply_text(f"Invalid subject: {subject}")
            return ConversationHandler.END
    else:
        await update.message.reply_text(
            f"You are not logged in\\. Type */register* or */login* to log in or register\\.\nIf you need to cancel current operation, type */cancel*",parse_mode="MarkdownV2")
        return ConversationHandler.END

# Function handling /remove command to remove user's preference from the database
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    if check_session(telegram_id):
        username = get_username(telegram_id)
        if not context.args:
            await update.message.reply_text("Please specify a subject to remove. Example: /remove Middle East")
            return
        subject = ' '.join(context.args)
        if subject in get_all_subjects():
            if check_user_preference(username, subject):
                remove_user_preference(username, subject)
                await update.message.reply_text(f"Preference removed successfully: {subject}")
                return ConversationHandler.END
            else:
                await update.message.reply_text(f"Subject is not in your list of preferences to remove it.")
                return ConversationHandler.END
        else:
            await update.message.reply_text(f"Invalid subject: {subject}")
            return ConversationHandler.END
    else:
        await update.message.reply_text(
            f"You are not logged in\\. Type */register* or */login* to log in or register\\.\nIf you need to cancel current operation, type */cancel*",parse_mode="MarkdownV2")
        return ConversationHandler.END



# Function for username handling
async def register_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_usernames()
    username = update.message.text
    if username in users:
        await update.message.reply_text("Username already exists. Try a different one.")
        return REGISTER_USERNAME
    context.user_data["username"] = username
    await update.message.reply_text("Enter your real name:")
    return REGISTER_REALNAME

# Function to get user's real name
async def register_realname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["realname"] = update.message.text
    await update.message.reply_text("Choose a password:")
    return REGISTER_PASSWORD

# Function for secure password handling with bcrypt
async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.encode("utf-8")
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    username = context.user_data["username"]
    telegram_id = update.message.from_user.id
    insert_user(username, context.user_data["realname"], hashed)
    insert_username_telegramid(telegram_id, username)
    await update.message.reply_text(f"Thanks for registering, {context.user_data['realname']}\\!\nTo get news articles from the leading websites, set your preferences by typing */preferences*",parse_mode="MarkdownV2")
    return ConversationHandler.END

# Function handling username login
async def login_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_usernames()
    username = update.message.text
    if username not in users:
        await update.message.reply_text("Username not found. Try again:")
        return LOGIN_USERNAME
    context.user_data["username"] = username
    await update.message.reply_text("Enter your password:")
    return LOGIN_PASSWORD

# Function handling password login
async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    password = update.message.text.encode("utf-8")
    username = context.user_data["username"]
    stored = get_user_password(username)
    realname = get_user_realname(username)

    if bcrypt.checkpw(password, stored):
        await update.message.reply_text(f"Welcome back, {realname}!")
        insert_username_telegramid(telegram_id, username)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Incorrect password. Try again:")
        return LOGIN_PASSWORD

# Function handling /cancel command to cancel user's current operations
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("All current operations are cancelled.")
    return ConversationHandler.END

# Function to deal with unknown commands
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Unknown command\\.\n"
        "Type */help* for a list of available commands\\.",parse_mode="MarkdownV2"
    )

# Function to deal with unknown messages to bot
async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I only understand specific commands\\.\nType */help* to see what I can do\\.",parse_mode="MarkdownV2"
    )

# Function handling /commands to send a list of available commands
async def commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Here are the available commands:\n\n"
        "*/start* \\- Begin interaction with the bot\n"
        "*/login* \\- Log in to your account\n"
        "*/register* \\- Create a new account\n"
        "*/logout* \\- Log out of your account\n"
        "*/info* \\- View your account info\n"
        "*/preferences* \\- Manage your news preferences\n"
        "*/add* _subject_ \\- Add a preference\n"
        "*/remove* _subject_ \\- Remove a preference\n"
        "*/clearpreferences* \\- Clear the list of your preferences\n"
        "*/cancel* \\- Cancel current operation\n",
        parse_mode="MarkdownV2"
    )

# Function to systematically check websites for new articles and notify users each hour
async def check_news():
    while True:
        await print_latest_news()
        await asyncio.sleep(3600)
#                                                   MAIN APPLICATION

# Function to handle user commands and run the app
def main():
    create_tables()

    app = ApplicationBuilder().token(bot.token).build()

    # REGISTER handler
    register_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register)],
        states={
            REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_username)],
            REGISTER_REALNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_realname)],
            REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # LOGIN handler
    login_handler = ConversationHandler(
        entry_points=[CommandHandler("login", login)],
        states={
            LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_username)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Other Bot commands handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(CommandHandler("preferences", preferences))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("clearpreferences", clearpreferences))
    app.add_handler(CommandHandler("help", commands))
    app.add_handler(CommandHandler("cancel", cancel))

    # Adding register and loging handlers
    app.add_handler(register_handler)
    app.add_handler(login_handler)

    # Adding handlers for unknown commands and messages
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))


    # Background task
    loop = asyncio.get_event_loop()
    loop.create_task(check_news())

    app.run_polling()

if __name__ == "__main__":
    main()

