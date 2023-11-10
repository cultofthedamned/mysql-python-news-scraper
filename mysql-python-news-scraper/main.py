import requests
import json
import mysql.connector
from bs4 import BeautifulSoup

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "passwd": "meowmeow",
    "database": "thedoomscrollingdb",
}

THE_GUARDIAN_BASE_URL = "https://www.theguardian.com/world"
THE_GUARDIAN_URL = "https://www.theguardian.com/"
NEWS_KEYWORDS = [
    "crisis", "disaster", "tragedy", "conflict", "violence", "catastrophe", "emergency", "outbreak", "pandemic", 
    "attack", "downturn", "recession", "unemployment", "bankruptcy", "corruption", "scandal", "inflation", "poverty", 
    "famine", "hunger", "homelessness", "eviction", "displacement", "inequality", "oppression", "protest", "unrest", 
    "riots", "brutality", "war", "genocide", "massacre", "terror", "crimes", "cyberattack", "breach", "disaster", "wildfires", 
    "floods", "hurricane", "tornado", "earthquake", "tsunami", "climate", "pollution", "degradation", "extinction", 
    "deforestation", "injustice", "discrimination", "inequity", "hate", "abuse", "harassment", "violence", "shooting", 
    "accident", "relief", "crisis", "refugees", "migrant", "border", "exploitation", "harassment", "cyberbullying", 
    "suicide", "self-harm", "abuse", "addiction", "overdose", "mental", "health", "hospital", "disease", "vaccine", 
    "shortage", "shortage", "crisis", "collapse", "turmoil", "instability", "government", "propaganda", "disinformation", 
    "misinformation", "censorship", "invasion", "concerns", "rights", "tensions", "conflict", "threat", "scandal", 
    "embezzlement", "fraud", "crash", "economic", "instability", "chaos", "bank", "security", "housing", "police", 
    "investigation", "accident", "accident", "malpractice", "neglect", "controversy", "dismissal", "misconduct", 
    "investigation", "controversy", "neglect", "deprivation", "collapse", "famine", "fraud", "contamination", 
    "corruption", "investigation", "inquiry"
]

SQL_QUERY = """INSERT INTO news_posts (title, image, content) VALUES (%s, %s, %s)"""

def connect_to_database():
    try:
        db = mysql.connector.connect(**DB_CONFIG)
        return db, db.cursor()
    except mysql.connector.Error as err:
        print(f"MySQL Connection Error: {err}")
        return None, None

def close_database_connection(connection, cursor):
    try:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Connection closed")
    except Exception as e:
        print(f"Error closing database connection: {e}")

def insert_article_into_database(cursor, article, db):
    try:
        if article is not None:
            cursor.execute("SELECT * FROM news_posts WHERE title = %(title)s", {"title": article["headline"]})
            result = cursor.fetchone()
            if result:
                print("Item already exists in the database.")
            else:
                cursor.execute(SQL_QUERY, (article["headline"], article["img"], json.dumps(article["content"])))
                inserted_id = cursor.lastrowid
                db.commit()
                print(f"New post inserted with ID: {inserted_id}")
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
    except Exception as e:
        print(f"Error: {e}")

def scrape_and_insert_articles(url, cursor, db):
    try:
        response = requests.get(url).text
        data = BeautifulSoup(response, "html.parser")
        
        articles = data.find_all("div", class_="dcr-12ilguo")

        for article_name in articles:
            full_article = {}
            maincontent_p = {}
            paragraph_count = 0
            words_in_name = article_name.text.split()

            for word in words_in_name:
                if word in NEWS_KEYWORDS:
                    link = THE_GUARDIAN_URL + article_name.a["href"]
                    article_data = requests.get(link).text

                    headline = BeautifulSoup(article_data, "html.parser").find(attrs={"data-gu-name": "headline"}).text
                    full_article["headline"] = headline

                    image = BeautifulSoup(article_data, "html.parser").find("img", class_="dcr-evn1e9")["src"]
                    full_article["img"] = image

                    body = BeautifulSoup(article_data, "html.parser").find(attrs={"data-gu-name": "body"})
                    maincontent = body.find_all("p")

                    for paragraph in maincontent:
                        paragraph_count += 1
                        maincontent_p[f"p{paragraph_count}"] = paragraph.text

                    full_article["content"] = maincontent_p

                    insert_article_into_database(cursor, full_article, db)

                else:
                    continue

    except requests.RequestException as e:
        print(f"Request Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    db, cursor = connect_to_database()
    
    if db and cursor:
        scrape_and_insert_articles(THE_GUARDIAN_BASE_URL, cursor, db)

    close_database_connection(db, cursor)

if __name__ == "__main__":
    main()