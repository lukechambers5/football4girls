from flask import Flask, render_template, request, redirect, url_for
from scraper import get_player_info
from trending_player import create_db, update_player_search, get_most_searched_players, get_all_search_logs
import requests

app = Flask(__name__, static_url_path='/static')

# Ensure database is created on startup
create_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    player_info = None
    most_searched_player = get_most_searched_players() 

    if request.method == 'POST':
        player_name = request.form['player_name']
        update_player_search(player_name)

        try:
            player_info = get_player_info(player_name)
            if player_info is None:
                return render_template('index.html', player_info=None, most_searched_player=most_searched_player)
        except requests.exceptions.ConnectionError:
            return redirect(url_for('error_page', message="Website unexpectedly closed the connection."))
        except Exception as e:
            return redirect(url_for('error_page', message=str(e)))

    return render_template('index.html', player_info=player_info, most_searched_player=most_searched_player)

@app.route('/search_logs', methods=['GET'])
def search_logs():
    logs = get_all_search_logs()  # This function will query the database for the logs
    return render_template('search_logs.html', logs=logs)


@app.route('/error')
def error_page():
    message = request.args.get('message', "An unknown error occurred.")
    return render_template('error.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)



#sudo nano /etc/resolv.conf