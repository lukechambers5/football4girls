import re
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Function to get the Wikipedia page content
def get_page_content(player_name):
    url = f"https://en.wikipedia.org/wiki/{player_name.replace(' ', '_')}"
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    try:
        response = session.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses
        return response.text  # Return HTML content as text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

# Function to search for a player using Wikipedia's API
def search_player(player_name):
    search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={player_name}&limit=1&namespace=0&format=json"
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()
        if data[1]:  # Check if there are results
            return data[1][0]  # Return the first match
        else:
            print("Player not found in Wikipedia.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the search: {e}")
        return None

# Function to extract the personal life section
def extract_personal_life_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    personal_life_header = (
        soup.find('span', id='Personal_life') or 
        soup.find('h2', string=re.compile("Personal life", re.IGNORECASE)) or 
        soup.find('span', id='Early_life') or 
        soup.find('h2', string=re.compile("Early life", re.IGNORECASE))
    )
    if not personal_life_header:
        print("Personal life header not found in the HTML content.")
        return None

    personal_life_content = ""
    content = personal_life_header.find_all_next()

    for element in content:
        if element.name == 'h2':  # Stop at the next main section
            break
        if element.name in ['p', 'ul', 'ol', 'div', 'table', 'dl']:
            personal_life_content += element.get_text(separator="\n", strip=True) + "\n"

    if not personal_life_content.strip():
        print("No personal life information found after the header.")
        return None

    return personal_life_content


def get_player_info(player_name):
    matched_name = search_player(player_name)

    if not matched_name:
        return None

    html_content = get_page_content(matched_name)

    if not html_content:
        return None

    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{matched_name.replace(' ', '_')}"
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    try:
        response = session.get(summary_url)
        response.raise_for_status()
        data = response.json()

        title = data.get('title')
        extract = data.get('extract')
        image_url = data.get('thumbnail', {}).get('source', None)
        summary_url = data.get('content_urls', {}).get('desktop', {}).get('page', None)

        # Extract all images
        player_images = extract_images(html_content)

        personal_life_content = extract_personal_life_info(html_content)
        cleaned_text = remove_bracket_numbers(personal_life_content)

        # Get dating info and used sentences
        dating_info, used_sentences = dating_stuff(cleaned_text)
        family_info = family_stuff(cleaned_text, used_sentences)

        position_explanation = determine_position(extract, title)
        
        

        # Check if the player is retired based on summary
        if check_retirement(extract):
            title += " (Retired)"
        else:
            title += " (Active)"  # Assuming they are active if not retired

        return {
            'title': title,
            'extract': position_explanation,
            'image_url': image_url,
            'summary_url': summary_url,
            'dating_life': dating_info,
            'family_life': family_info,
            'player_images': player_images  # Include all player images
        }

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None



# Function to remove bracketed numbers (like citations)
def remove_bracket_numbers(text):
    if not isinstance(text, str):
        return text  # Return the input as-is if it's not a string
    cleaned_text = re.sub(r'\[\s*\d+\s*\]', '', text)
    return cleaned_text.strip()


def dating_stuff(cleaned_text):
    if not cleaned_text:  # Check if cleaned_text is None or empty
        return "No dating information found.", set()  # Return an empty set for used sentences

    dating = ''
    dating_keywords = ["dating", "dated", "girlfriend", "boyfriend", "wife", "husband", "married", "marriage",
                       "relationship", "broken up", "couple", "engaged", "divorce", "divorced"]
    
    subheaders_to_skip = ["relationships and marriages", "personal life"]
    sentences = cleaned_text.split('.')
    used_sentences = set()  # Keep track of sentences used in the dating section

    for sentence in sentences:
        sentence = sentence.strip()
        
        # Remove unwanted characters
        sentence = re.sub(r'["\(\)]', '', sentence) 
        print(f"Processed sentence: {sentence.lower()}")
        
        # Check if sentence starts with any subheader to skip (instead of exact match)
        if sentence.lower().strip() == "relationships and marriages":
            continue
        
        # Only add the sentence if it contains a dating keyword and isn't already used
        if sentence and sentence not in used_sentences:
            for keyword in dating_keywords:
                if keyword in sentence.lower():
                    dating += sentence + ".\n\n"
                    used_sentences.add(sentence)  # Mark this sentence as used
                    break

    return dating if dating else "Most likely single. Check wikipedia for more info...", used_sentences



# Updated family_stuff function
def family_stuff(cleaned_text, used_sentences):
    if not cleaned_text:  # Check if cleaned_text is None or empty
        return "No family information found."

    family = ''
    family_keywords = ["son", "daughter", "brother", "sister", "grandfather", "grandmother",
                       "children", "family", "father", "mother"]

    sentences = cleaned_text.split('.')
    for sentence in sentences:
        sentence = sentence.strip()
        
        # Remove leading quotation marks and any other unwanted characters
        sentence = re.sub(r'^[“”"\'\(\s]+', '', sentence)

        if sentence in used_sentences:  # Skip the sentence if it was already used in the dating section
            continue
        
        for keyword in family_keywords:
            if keyword in sentence.lower():
                family += sentence + ". " + "\n\n"
                break  # Add only the first matching sentence for each keyword

    return family if family else "No family information found."

def check_retirement(summary):
    # Keywords indicating retirement
    retirement_keywords = ["retired", "former", "last played", "played until", "ex-"]
    
    # Check if any retirement keywords are present in the summary
    for keyword in retirement_keywords:
        if keyword in summary.lower():
            return True
    
    # If no retirement keyword is found, assume the player is not retired
    return False

def extract_images(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    images = []

    # Minimum dimensions for valid images
    MIN_IMAGE_WIDTH = 50
    MIN_IMAGE_HEIGHT = 50

    def is_valid_image(img_tag):
        # Check if the image has valid dimensions, skip small icons/logos
        if img_tag.has_attr('width') and img_tag.has_attr('height'):
            try:
                width = int(img_tag['width'])
                height = int(img_tag['height'])
                if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
                    return False
            except ValueError:
                return False  # In case width/height are not numbers

        # Filter out images likely to be logos, icons, or placeholders
        img_url = img_tag['src']
        alt_text = img_tag.get('alt', '').lower()
        if any(ext in img_url.lower() for ext in ['logo', 'icon', 'sprite', 'placeholder', 'default']):
            return False
        if any(keyword in alt_text for keyword in ['placeholder', 'default', 'image not available']):
            return False
        
        # Filter out SVG images and small GIFs
        if img_url.endswith('.svg') or img_url.endswith('.gif'):
            return False

        # Ensure alt text isn't empty or vague
        if not alt_text or alt_text in ['image', 'photo', 'thumbnail']:
            return False
        
        return True

    # Find the main image from the infobox
    infobox = soup.find('table', class_='infobox')
    if infobox:
        main_image_tag = infobox.find('img')
        if main_image_tag and is_valid_image(main_image_tag):
            main_image_url = f"https:{main_image_tag['src']}"
            images.append(main_image_url)

    # Find all images before the "References" section
    references_header = soup.find('span', id='References')
    if references_header:
        for element in references_header.find_all_previous():
            if len(images) >= 10:  # Limit to the first 10 images
                break
            if element.name == 'h2':
                break  # Stop if we reach a new section
            if element.name == 'img' and is_valid_image(element):
                img_url = f"https:{element['src']}"
                if img_url not in images:
                    images.append(img_url)

    # If fewer than 10 images were found, search for more on the page
    if len(images) < 10:
        all_images = soup.find_all('img')
        for img_tag in all_images:
            if is_valid_image(img_tag):
                img_url = f"https:{img_tag['src']}"
                if img_url not in images:
                    images.append(img_url)
            if len(images) >= 10:  # Stop when we have 10 images
                break

    return images[:10]  

def position(name):
    html_content = get_page_content(name)

    # Check if the HTML content was successfully retrieved
    if not html_content:
        print(f"Failed to retrieve HTML content for {name}.")
        return None

    soup = BeautifulSoup(html_content, 'html.parser')

    # Try to find the infobox specifically with class 'infobox vcard' or any infobox
    infobox = soup.find('table', class_='infobox')

    if infobox:
        print("Infobox found.")
        
        # Try to find the 'Position' row in the infobox
        position_row = infobox.find('th', string=lambda text: text and "Position" in text)
        if position_row:
            print("Position row found:", position_row.get_text(strip=True))
            
            # Get the next 'td' element with the position information
            position_value = position_row.find_next('td')
            if position_value:
                position_text = position_value.get_text(separator=" ", strip=True)
                print("Position value found:", position_text)
                return position_text
            else:
                print("No 'td' element found after 'Position'.")
        else:
            print("Position row not found in infobox.")
    else:
        print(f"Infobox not found for {name}. Printing the first table on the page for inspection:")
        
        # If infobox is not found, print the first table for debugging
        first_table = soup.find('table')
        if first_table:
            print(first_table.prettify()[:2000])  # Print the first 2000 characters for easier inspection
        else:
            print("No table found on the page.")
    
    return "Position not found"

def determine_position(summary, name):
    if("football" in summary):
        return football_position(name)
    elif("basketball" in summary):
        return basketball_position(name)
    elif("hockey" in summary):
        return hockey_position(name)
    elif("soccer" in summary):
        return soccer_position(name)
    else:
        return "Sport not included yet"
    
# Football position logic
def football_position(name):
    position_val = position(name).lower()
    
    # Offense positions
    if "quarterback" in position_val:
        return f'{name} plays the Quarterback position! This means he is the signal caller. He runs the offense and either throws the ball or hands it off to the running back.'
    elif "running back" in position_val:
        return f'{name} plays the Running Back position! This means he receives handoffs from the quarterback to rush the ball.'
    elif "fullback" in position_val:
        return f'{name} plays the Fullback position! This means he is a beefier running back. They are both fast and very strong and do a lot of blocking.'
    elif "wide receiver" in position_val:
        return f'{name} plays the Wide Receiver position! This means he catches the ball thrown by the quarterback.'
    elif "tight end" in position_val:
        return f'{name} plays the Tight End position! This means he is a receiver that is also used to block for the running back.'
    elif "offensive lineman" in position_val:
        return f'{name} plays the Offensive Line position! This means he blocks for the quarterback and running back.'
    
    # Defense positions
    elif "safety" in position_val:
        return f'{name} plays the Safety position! This means he is the last line of defense and is responsible for stopping long plays.'
    elif "cornerback" in position_val:
        return f'{name} plays the Cornerback position! This means he defends the wide receivers and sometimes tries to tackle the quarterback.'
    elif "linebacker" in position_val:
        return f'{name} plays the Linebacker position! This means he is both strong and fast and will sometimes rush the quarterback or tackle the ball carrier.'
    elif "defensive line" in position_val or "defensive end" in position_val:
        return f'{name} plays the Defensive Line position! This means he is the first line of defense and is responsible for stopping the running back from running through the middle.'
    
    # Otherwise
    else:
        return f"{name} is retired and is currently a {position_val}!"

# Basketball position logic
def basketball_position(name):
    position_val = position(name).lower()
    
    if "center" in position_val:
        return f'{name} plays the Center position! This means they are usually the tallest player on the court and are responsible for blocking shots, rebounding, and scoring close to the basket.'
    elif "power forward" in position_val:
        return f'{name} plays the Power Forward position! They do a lot of the same things as a center, getting rebounds and guarding taller players on defense. They are frequently good outside shooters as well.'
    elif "small forward" in position_val:
        return f'{name} plays the Small Forward position! They can play close or far and float around where they are needed throughout the game, guarding who needs to be guarded, and finding gaps in the defense.'
    elif "point guard" in position_val:
        return f'{name} plays the Point Guard position! Their skills are passing and dribbling, frequently known as the playmakers. On defense, they normally try to get steals and force the opponents to make mistakes.'
    elif "shooting guard" in position_val:
        return f'{name} plays the Shooting Guard position! They are the best shooters on the court, frequently shooting far out shots that others cannot. On defense, they try to get steals and block passes.'
    else:
        return f"{name} is retired and is currently a {position_val}!"

# Hockey position logic
def hockey_position(name):
    position_val = position(name).lower()
    
    if "goalie" or "goaltender" in position_val:
        return f'{name} plays the Goalie position! He is the player who protects the goal. His main job is to stop the puck from going into the net.'
    elif "defenseman" in position_val:
        return f'{name} plays the Defenseman position! There are usually two on the ice. They help the goalie by blocking shots and keeping opposing players away from the goal. They also assist in moving the puck up the ice.'
    elif "forward" in position_val:
        return f'{name} plays the Forward position! He focuses on scoring goals and assisting his teammates, controlling the puck and setting up plays. He plays both offense and defense.'
    else:
        return f"{name} is retired and is currently a {position_val}!"

# Soccer position logic
def soccer_position(name):
    position_val = position(name).lower()
    
    if "goalkeeper" in position_val:
        return f'{name} plays the Goalkeeper position! He is the player who protects the goal. His main job is to stop the ball from going into the net.'
    elif "defender" in position_val:
        return f'{name} plays the Defender position! He helps protect the goal by blocking attacks from opposing players and often supports the midfield.'
    elif "midfielder" in position_val:
        return f'{name} plays the Midfielder position! He controls the play, linking defense and attack, and helps both in defending and creating scoring opportunities.'
    elif "forward" in position_val or "striker" in position_val:
        return f'{name} plays the Forward position! He focuses on scoring goals and creating chances for the team, often leading the attack.'
    else:
        return f"{name} is retired and is currently a {position_val}!"