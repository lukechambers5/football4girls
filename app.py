from flask import Flask, render_template, request, redirect, url_for
from scraper import get_player_info
import requests  # Import requests to handle connection errors

app = Flask(__name__, static_url_path='/static')

@app.route('/', methods=['GET', 'POST'])
def index():
    player_info = None
    if request.method == 'POST':
        player_name = request.form['player_name']
        print(f"Received player name: {player_name}")
        
        try:
            player_info = get_player_info(player_name)
            if player_info is None:
                return render_template('index.html', player_info=None)  # No info found

        except requests.exceptions.ConnectionError:
            return redirect(url_for('error_page', message="Website unexpectedly closed the connection."))
        
        except Exception as e:  # Catch other exceptions    return redirect(url_for('error_page', message=str(e)))
            return redirect(url_for('error_page', message=str(e)))
    return render_template('index.html', player_info=player_info)

@app.route('/error')
def error_page():
    message = request.args.get('message', "An unknown error occurred.")
    return render_template('error.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)


#sudo nano /etc/resolv.conf - DNS SERVER CHANGE

#ipconfig /flushdns - after done working on project