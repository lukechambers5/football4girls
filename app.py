from flask import Flask, render_template, request, redirect, url_for
from scraper import log_search, get_player_info, get_player_image
import requests  # Import requests to handle connection errors
from collections import Counter  # Ensure the proper import
import csv

app = Flask(__name__, static_url_path='/static')


# Function to get the most searched player
def get_most_searched_player():
    file_path = 'logs/search_log.csv'

    try:
        # Open the CSV file and read it
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row

            # List to hold player names from the CSV file
            player_names = [row[0] for row in reader]

            # Count occurrences of each player name
            player_counts = Counter(player_names)

            # Find the most common player (most searched)
            if player_counts:
                most_searched = player_counts.most_common(1)[
                    0]  # Get the most common player

                # Get the image for the most searched player
                player_image_url = get_player_image(most_searched[0])

                # Return the player's name, search count, and image URL
                return {
                    'name': most_searched[0],
                    'search_count': most_searched[1],
                    'image_url': player_image_url
                }
            else:
                return None  # If no data, return None

    except FileNotFoundError:
        return None  # If the file doesn't exist, return None

def update_csv(player_data):
    header = ['Name']

    try:
        with open('logs/search_log.csv', mode = 'a', newline = '', encoding = 'utf-8') as file:
            writer = csv.writer(file)

            if file.tell() == 0:
                writer.writerow(header)
                writer.writerow(player_data)
    except Exception as e:
        print(f"Error updating CSV: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    player_info = None
    most_searched_player = get_most_searched_player()  

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
    app.run(debug=True, host='0.0.0.0', port=80)

#sudo nano /etc/resolv.conf - DNS SERVER CHANGE

#ipconfig /flushdns - after done working on project
