import os
import mysql.connector
from mysql.connector import errorcode
from flask import Flask, render_template, request, jsonify
from azure.cognitiveservices.search.websearch import WebSearchAPI
from msrest.authentication import CognitiveServicesCredentials

app = Flask(__name__)

# bing search connection
subscription_key = os.environ['BING_CLIENT']
client = WebSearchAPI(CognitiveServicesCredentials(subscription_key))

# azure database connection
try:
    conn = mysql.connector.connect(user="shaked@shaked-test-db", password=os.environ['DB_PASS'],
                                  host="shaked-test-db.mysql.database.azure.com", port=3306, database="search-history")
    print("Connection established")
except mysql.connector.Error as err:
  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    print("Something is wrong with the user name or password")
  elif err.errno == errorcode.ER_BAD_DB_ERROR:
    print("Database does not exist")
  else:
    print(err)
else:
  cursor = conn.cursor()


def bing_search_instagram_page(val):
    web_data = client.web.search(query=val)
    for web_page in web_data.web_pages.value:
        if web_page.url.startswith("https://www.instagram.com/"):
            cursor.execute("INSERT INTO history (person_name, link) VALUES ('{}', '{}')".format(val, web_page.url))
            conn.commit()
            return web_page.url


def get_result_from_db(to_search):
    cursor.execute("SELECT * FROM history WHERE person_name = '{}'".format(to_search))
    res = cursor.fetchone()
    return res


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/history")
def get_history():
    history = []
    cursor.execute("SELECT * FROM history ORDER BY search_date")
    all_history = cursor.fetchall()
    for res in all_history:
        history.append(res[1])
    return jsonify(history)


@app.route("/search")
def search():
    to_search = request.args.get('value', 0)
    res = get_result_from_db(to_search)
    return res[1] if res else bing_search_instagram_page(to_search)
