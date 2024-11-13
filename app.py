from flask import Flask, render_template, request, redirect, url_for
from scraper import get_player_info
from trending_player import create_db, update_player_search, get_most_searched_players
import requests
import os

app = Flask(__name__, static_url_path='/static')

@app.route('/', methods=['GET', 'POST'])
def index():
    player_info = None
    most_searched_player = get_most_searched_players() 
    create_db()  # Ensures DB exists on each launch

    if request.method == 'POST':
        player_name = request.form['player_name']
    
        update_player_search(player_name)

        try:
            # Get the player information
            player_info = get_player_info(player_name)
            if player_info is None:
                return render_template('index.html', player_info=None, most_searched_player=most_searched_player)
        except requests.exceptions.ConnectionError:
            return redirect(url_for('error_page', message="Website unexpectedly closed the connection."))

        except Exception as e:  # Handle other exceptions
            return redirect(url_for('error_page', message=str(e)))

    return render_template('index.html', player_info=player_info, most_searched_player=most_searched_player)

@app.route('/error')
def error_page():
    message = request.args.get('message', "An unknown error occurred.")
    return render_template('error.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)


#sudo nano /etc/resolv.conf