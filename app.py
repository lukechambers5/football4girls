from flask import Flask, render_template, request
from scraper import get_player_info

app = Flask(__name__, static_url_path='/static')

@app.route('/', methods=['GET', 'POST'])
def index():
    player_info = None
    if request.method == 'POST':
        player_name = request.form['player_name']
        print(f"Received player name: {player_name}")
        player_info = get_player_info(player_name)
    return render_template('index.html', player_info=player_info)

if __name__ == '__main__':
    app.run(debug=True)


#sudo nano /etc/resolv.conf - DNS SERVER CHANGE

#ipconfig /flushdns - after done working on project