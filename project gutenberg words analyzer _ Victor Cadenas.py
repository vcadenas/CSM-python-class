"""
Project Gutenberg Book Analyzer with Database Storage

This program:
1. Takes a URL from the user (Project Gutenberg book)
2. Extracts the book title
3. Finds the top 10 most common words
4. Saves everything to a SQLite database
5. Shows results in a GUI window
"""

from html.parser import HTMLParser
from urllib.request import urlopen
from collections import Counter
import string
import tkinter as tk
import sqlite3

# ------------------------------------
# STOPWORDS - Common words to skip
# ------------------------------------
STOPWORDS = {
    "a","about","above","after","again","against","all","am","an","and","any",
    "are","as","at","be","because","been","before","being","below","between",
    "both","but","by","can","did","do","does","doing","down","during","each",
    "few","for","from","further","had","has","have","having","he","her","here",
    "hers","him","himself","his","how","i","if","in","into","is","it","its",
    "itself","just","me","more","most","my","myself","no","nor","not","of",
    "off","on","once","only","or","other","our","ours","ourselves","out","over",
    "own","same","she","should","so","some","such","than","that","the","their",
    "theirs","them","themselves","then","there","these","they","this","those",
    "through","to","too","under","until","up","very","was","we","were","what",
    "when","where","which","while","who","whom","why","will","with","you",
    "your","yours","yourself","yourselves"
}


# ------------------------------------
# HTML PARSER - Reads the webpage
# ------------------------------------
class SimpleParser(HTMLParser):
    """
    This class reads HTML and collects:
    - The book title from <title> tag
    - All the words from the page
    """

    def __init__(self):
        super().__init__()
        self.words = []           # List to store all words
        self.in_title = False     # To check inside <title> tag
        self.book_title = ""      # The book title

    def handle_starttag(self, tag, attrs):
        """Called when there is an opening tag like <title>"""
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        """Called when there is a closing tag like </title>"""
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        """Called when there is text between tags"""
        text = data.strip()

        # If we are in the title tag, save the title
        if self.in_title: 
            self.book_title += text + " "
            return  # Don't count title words

        # Otherwise, collect words for counting
        for word in text.split():
            word = word.lower().strip()

            # To skip empty words
            if word == "":
                continue

            # To skip words with punctuation
            if any(p in word for p in string.punctuation):
                continue

            # To skip the stopwords
            if word in STOPWORDS:
                continue

            # To skip very short words
            if len(word) <= 2:
                continue

            # To save a valid word
            self.words.append(word)

    def get_top(self, n):
        """Count words and return the top N most common"""
        counter = Counter(self.words)
        return counter.most_common(n)

    def get_title(self):
        """Return the book title"""
        return self.book_title.strip()


# ------------------------------------
# DATABASE FUNCTIONS
# ------------------------------------

def setup_database():
    """
    Create the database and table if they don't exist.
    It will store: book_title, book_url, word, frequency
    """
    conn = sqlite3.connect('gutenbergwords.db')
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS book_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_title TEXT,
            book_url TEXT,
            word TEXT,
            frequency INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()


def save_to_database(book_title, book_url, top_words):
    """
    Save the book title, URL, and top 10 words to the database.
    Parameters:
    - book_title: The title of the book
    - book_url: The URL of the book
    - top_words: List of tuples like [('word', 123), ('another', 45), ...]
    """
    conn = sqlite3.connect('gutenbergwords.db')
    cursor = conn.cursor()
    
    # Insert each word and its frequency
    for word, frequency in top_words:
        cursor.execute('''
            INSERT INTO book_words (book_title, book_url, word, frequency)
            VALUES (?, ?, ?, ?)
        ''', (book_title, book_url, word, frequency))
    
    conn.commit()
    conn.close()


# ------------------------------------
# GUI BUTTON FUNCTION
# ------------------------------------

def analyze_url():
    """
    This function runs when the user clicks 'Submit'.
    It downloads the page, analyzes it, saves to database,
    and shows the results.
    """
    url = url_entry.get().strip()

    # Check if user entered a URL
    if url == "":
        output_box.insert(tk.END, "Please enter a URL.\n")
        return

    # Clear previous results
    output_box.delete(1.0, tk.END)

    try:
        # Step 1: Download the webpage
        response = urlopen(url)
        html_data = response.read().decode("utf-8", errors="ignore")

        # Step 2: Parse the HTML
        parser = SimpleParser()
        parser.feed(html_data)

        # Step 3: Get the title and top words
        title = parser.get_title()
        top_words = parser.get_top(10)

        # Step 4: Save to database
        save_to_database(title, url, top_words)

        # Step 5: Display results
        output_box.insert(tk.END, f"Book Title: {title}\n")
        output_box.insert(tk.END, f"URL: {url}\n\n")
        output_box.insert(tk.END, "Top 10 Words:\n")
        output_box.insert(tk.END, "-" * 40 + "\n")
        
        for rank, (word, count) in enumerate(top_words, 1):
            output_box.insert(tk.END, f"{rank:2d}. {word:15s} : {count:5d}\n")

    except Exception as e:
        output_box.insert(tk.END, f"Error: {e}\n")


# ------------------------------------
# MAIN PROGRAM - CREATE GUI
# ------------------------------------

# Set up the database when program starts
setup_database()

# Create the main window
window = tk.Tk()
window.title("Project Gutenberg Analyzer")

# URL input section
url_label = tk.Label(window, text="Enter Project Gutenberg URL:")
url_label.pack(pady=5)

url_entry = tk.Entry(window, width=60)
url_entry.pack(pady=5)

# Submit button
submit_button = tk.Button(window, text="Analyze & Save", command=analyze_url)
submit_button.pack(pady=10)

# Output text box
output_box = tk.Text(window, width=70, height=20)
output_box.pack(pady=10)

# Run the GUI
window.mainloop()
