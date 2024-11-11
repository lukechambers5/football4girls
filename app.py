from flask import Flask, render_template, request, redirect, url_for
from scraper import log_search, get_player_info, get_player_image
import requests  # Import requests to handle connection errors
from collections import Counter  # Ensure the proper import
from trending_player import create_db
import csv
import os

app = Flask(__name__, static_url_path='/static')

@app.route('/', methods=['GET', 'POST'])
def index():
    player_info = None
    create_db()
    if request.method == 'POST':
        player_name = request.form['player_name']
        log_search(player_name)
        try:
            player_info = get_player_info(player_name)
            if player_info is None:
                return render_template('index.html', player_info=None, most_searched_player=most_searched_player)
            player_data = [player_name]
            update_csv(player_data)
        except requests.exceptions.ConnectionError:
            return redirect(
                url_for('error_page',
                        message="Website unexpectedly closed the connection."))

        except Exception as e:  # Catch other exceptions
            return redirect(url_for('error_page', message=str(e)))

    return render_template('index.html',
                           player_info=player_info,
                           most_searched_player=most_searched_player)


@app.route('/error')
def error_page():
    message = request.args.get('message', "An unknown error occurred.")
    return render_template('error.html', message=message)


if __name__ == '__main__':
    app.run(debug=True)


#sudo nano /etc/resolv.conf - DNS SERVER CHANGE

#ipconfig /flushdns - after done working on project
