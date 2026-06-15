import os
import time
import sqlite3
import threading
import requests
import feedparser
from datetime import datetime, timezone
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder='static', static_url_path='')

DB_FILE = "rss_deck.db"

DEFAULT_FEEDS = [
    # Brasil Category
    ("G1 - Brasil", "https://g1.globo.com/rss/g1/", "Brasil", 0),
    ("CNN Brasil", "https://www.cnnbrasil.com.br/feed/", "Brasil", 1),
    ("Folha de S.Paulo", "https://news.google.com/rss/search?q=when:24h+site:folha.uol.com.br&hl=pt-BR&gl=BR&ceid=BR:pt-419", "Brasil", 2),
    ("UOL Notícias", "https://news.google.com/rss/search?q=when:24h+site:uol.com.br/noticias&hl=pt-BR&gl=BR&ceid=BR:pt-419", "Brasil", 3),
    ("BBC Brasil", "https://feeds.bbci.co.uk/portuguese/rss.xml", "Brasil", 4),
    # Mundo Category
    ("Reuters World", "https://news.google.com/rss/search?q=when:24h+site:reuters.com&hl=en-US&gl=US&ceid=US:en", "Mundo", 0),
    ("BBC News World", "http://feeds.bbci.co.uk/news/world/rss.xml", "Mundo", 1),
    ("CNN World", "http://rss.cnn.com/rss/edition_world.rss", "Mundo", 2),
    ("NYT International", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "Mundo", 3),
    ("El País", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/america/portada", "Mundo", 4),
    # Economia Category
    ("G1 Economia", "https://g1.globo.com/rss/g1/economia/", "Economia", 0),
    ("InfoMoney", "https://www.infomoney.com.br/feed/", "Economia", 1),
    ("CNBC Business", "https://search.cnbc.com/rs/search/all/view.rss?partnerId=20001&keywords=finance", "Economia", 2),
    # Tecnologia Category
    ("TechCrunch", "https://techcrunch.com/feed/", "Tecnologia", 0),
    ("G1 Tecnologia", "https://g1.globo.com/rss/g1/tecnologia/", "Tecnologia", 1),
    ("Hacker News", "https://news.ycombinator.com/rss", "Tecnologia", 2),
    # Guerras Category
    ("Guerras (Google)", "https://news.google.com/rss/search?q=when:24h+guerra+OR+conflito+OR+combates&hl=pt-BR&gl=BR&ceid=BR:pt-419", "Guerras", 0),
    ("Reuters Conflict (EN)", "https://news.google.com/rss/search?q=when:24h+war+OR+conflict+site:reuters.com&hl=en-US&gl=US&ceid=US:en", "Guerras", 1),
    ("BBC Conflict (EN)", "https://news.google.com/rss/search?q=when:24h+war+OR+conflict+site:bbc.co.uk&hl=en-US&gl=US&ceid=US:en", "Guerras", 2)
]

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite database and tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_order INTEGER DEFAULT 0
        )
    """)
    
    # Create feeds table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            column_index INTEGER NOT NULL
        )
    """)
    
    # Create articles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_id INTEGER NOT NULL,
            guid TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            description TEXT,
            link TEXT NOT NULL,
            pub_date TEXT NOT NULL,
            fetched_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(feed_id) REFERENCES feeds(id) ON DELETE CASCADE
        )
    """)

    # Create tags table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT 'red'
        )
    """)
    
    # Check if tags table has color column for existing databases
    cursor.execute("PRAGMA table_info(tags)")
    cols = [row[1] for row in cursor.fetchall()]
    if "color" not in cols:
        try:
            cursor.execute("ALTER TABLE tags ADD COLUMN color TEXT DEFAULT 'red'")
        except Exception as e:
            print(f"Error migrating tags table: {e}")
            
    # Clean up existing placeholder and empty articles from DB
    placeholders = [
        "notícias - uol", "notícias uol", "uol notícias", "uol", 
        "noticias uol", "noticias - uol", "uol noticias", 
        "uol - notícias", "uol - noticias", "sem título", ""
    ]
    placeholders_placeholders = ",".join(["?"] * len(placeholders))
    try:
        cursor.execute(f"""
            DELETE FROM articles
            WHERE LOWER(TRIM(title)) IN ({placeholders_placeholders})
               OR LOWER(TRIM(description)) IN ({placeholders_placeholders})
               OR TRIM(title) = ''
               OR TRIM(description) = ''
        """, placeholders + placeholders)
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"Purged {deleted} existing empty/placeholder articles from DB on init.")
    except Exception as e:
        print(f"Error purging placeholders on init: {e}")
    
    conn.commit()
    conn.close()

def add_default_feeds():
    """Inserts default categories and feeds into database only if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check current categories in DB
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = ["Brasil", "Mundo", "Economia", "Tecnologia", "Guerras"]
        for idx, cat in enumerate(default_categories):
            cursor.execute("INSERT OR IGNORE INTO categories (name, display_order) VALUES (?, ?)", (cat, idx))
            
    # Check current feeds in DB
    cursor.execute("SELECT COUNT(*) FROM feeds")
    if cursor.fetchone()[0] == 0:
        print("Initializing feeds table with default feeds...")
        for name, url, category, column_index in DEFAULT_FEEDS:
            cursor.execute("""
                INSERT OR IGNORE INTO feeds (name, url, category, column_index)
                VALUES (?, ?, ?, ?)
            """, (name, url, category, column_index))
    conn.commit()
    conn.close()

def standardize_pub_date(entry):
    """Standardizes feed item publish dates to YYYY-MM-DD HH:MM:SS (UTC)."""
    parsed = entry.get('published_parsed')
    if parsed:
        try:
            # parsed is a time.struct_time
            dt = datetime(*parsed[:6])
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
    # Fallback to current UTC date time
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

def save_parsed_entries(feed_id, entries, feed_url=""):
    """Saves non-duplicate entries to the articles table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    new_count = 0
    
    for entry in entries:
        title = entry.get('title', 'Sem Título')
        link = entry.get('link', '')
        description = entry.get('summary', entry.get('description', ''))
        
        # Clean title and description
        if title:
            title = title.strip()
        if description:
            # Strip HTML tags from description if present for clean UI display
            import re
            description = re.sub(r'<[^>]+>', '', description)
            description = description.replace('&nbsp;', ' ').strip()
            
        # Skip if title or description is missing
        if not title or not description:
            continue
            
        # Global treatment: skip empty/placeholder articles
        title_lower = title.lower().strip()
        desc_lower = description.lower().strip()
        placeholders = {
            "notícias - uol", "notícias uol", "uol notícias", "uol", 
            "noticias uol", "noticias - uol", "uol noticias", 
            "uol - notícias", "uol - noticias", "sem título", ""
        }
        
        if title_lower in placeholders or desc_lower in placeholders:
            continue
                
        guid = entry.get('id', entry.get('guid', link))
        pub_date = standardize_pub_date(entry)
        
        if not guid or not link:
            continue
            
        try:
            cursor.execute("""
                INSERT INTO articles (feed_id, guid, title, description, link, pub_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (feed_id, guid, title, description[:500], link, pub_date))
            new_count += 1
        except sqlite3.IntegrityError:
            # Duplicate entry, ignore
            pass
        except Exception as e:
            print(f"Failed to insert article: {e}")
            
    conn.commit()
    conn.close()
    return new_count

def fetch_feed_entries(url):
    """Downloads RSS Feed content using proper request headers to avoid 403 blocks."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=4)
        response.raise_for_status()
        # Feedparser parses string content directly
        feed = feedparser.parse(response.content)
        return feed.entries
    except Exception as e:
        print(f"Error fetching feed URL {url}: {e}")
        return []

def fetch_all_feeds():
    """Queries all configured feeds, fetches latest articles, and updates database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, url FROM feeds")
    feeds = cursor.fetchall()
    conn.close()
    
    total_new = 0
    for feed in feeds:
        feed_id, name, url = feed['id'], feed['name'], feed['url']
        print(f"Polling feed: {name} ({url})")
        entries = fetch_feed_entries(url)
        if entries:
            new_inserted = save_parsed_entries(feed_id, entries, url)
            total_new += new_inserted
            print(f"Inserted {new_inserted} new articles for {name}")
    return total_new

def query_articles(category=None, date=None, search=None):
    """Queries, filters, and searches cached articles in the SQLite DB per feed to avoid starvation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch relevant feed IDs first
    if category:
        cursor.execute("SELECT id FROM feeds WHERE category = ?", (category,))
    else:
        cursor.execute("SELECT id FROM feeds")
    feed_ids = [row['id'] for row in cursor.fetchall()]
    
    all_articles = []
    # 2. For each feed, get its latest 50 articles
    for fid in feed_ids:
        query = """
            SELECT a.id, a.feed_id, f.name as feed_name, f.category, a.guid, a.title, a.description, a.link, a.pub_date
            FROM articles a
            JOIN feeds f ON a.feed_id = f.id
            WHERE a.feed_id = ?
        """
        params = [fid]
        
        if date:
            query += " AND a.pub_date LIKE ?"
            params.append(f"{date}%")
            
        if search:
            query += " AND (a.title LIKE ? OR a.description LIKE ?)"
            search_param = f"%{search}%"
            params.append(search_param)
            params.append(search_param)
            
        query += " ORDER BY a.pub_date DESC LIMIT 50"
        
        cursor.execute(query, params)
        all_articles.extend([dict(row) for row in cursor.fetchall()])
        
    conn.close()
    
    # Sort the combined articles by pub_date DESC
    all_articles.sort(key=lambda x: x['pub_date'], reverse=True)
    return all_articles

# Background Polling Thread
def start_background_polling():
    def worker():
        # Sleep for a few seconds to let startup complete
        time.sleep(5)
        while True:
            print("Background fetch starting...")
            try:
                fetch_all_feeds()
            except Exception as e:
                print(f"Error in background fetch worker: {e}")
            # Poll every 1 minute (60 seconds) for a highly live, real-time feel
            time.sleep(60)
            
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

# REST API Routes
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/feeds', methods=['GET', 'POST'])
def api_feeds():
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, url, category, column_index FROM feeds ORDER BY category, column_index")
            feeds = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return jsonify(feeds)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    elif request.method == 'POST':
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        url = data.get('url', '').strip()
        category = data.get('category', '').strip()
        
        if not name or not url or not category:
            return jsonify({"error": "Nome, URL e Categoria são obrigatórios"}), 400
            
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if category exists, if not create it
            cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
            if not cursor.fetchone():
                cursor.execute("SELECT COALESCE(MAX(display_order), 0) FROM categories")
                max_order = cursor.fetchone()[0]
                cursor.execute("INSERT INTO categories (name, display_order) VALUES (?, ?)", (category, max_order + 1))
                
            # Get column index
            cursor.execute("SELECT COALESCE(MAX(column_index), -1) FROM feeds WHERE category = ?", (category,))
            max_idx = cursor.fetchone()[0]
            column_index = max_idx + 1
            
            cursor.execute("""
                INSERT INTO feeds (name, url, category, column_index)
                VALUES (?, ?, ?, ?)
            """, (name, url, category, column_index))
            conn.commit()
            feed_id = cursor.lastrowid
            conn.close()
            
            # Crawl immediately
            try:
                entries = fetch_feed_entries(url)
                if entries:
                    save_parsed_entries(feed_id, entries, url)
            except Exception as crawl_err:
                print(f"Error crawling newly added feed: {crawl_err}")
                
            return jsonify({
                "status": "success", 
                "feed": {
                    "id": feed_id,
                    "name": name,
                    "url": url,
                    "category": category,
                    "column_index": column_index
                }
            }), 201
        except sqlite3.IntegrityError:
            return jsonify({"error": "Já existe um feed cadastrado com esta URL"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/feeds/<int:feed_id>', methods=['PUT', 'DELETE'])
def api_feed_detail(feed_id):
    if request.method == 'PUT':
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        url = data.get('url', '').strip()
        category = data.get('category', '').strip()
        
        if not name or not url or not category:
            return jsonify({"error": "Nome, URL e Categoria são obrigatórios"}), 400
            
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get original feed
            cursor.execute("SELECT url, category, column_index FROM feeds WHERE id = ?", (feed_id,))
            old_feed = cursor.fetchone()
            if not old_feed:
                conn.close()
                return jsonify({"error": "Feed não encontrado"}), 404
                
            old_url = old_feed['url']
            old_category = old_feed['category']
            
            # Check if category exists, if not create it
            cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
            if not cursor.fetchone():
                cursor.execute("SELECT COALESCE(MAX(display_order), 0) FROM categories")
                max_order = cursor.fetchone()[0]
                cursor.execute("INSERT INTO categories (name, display_order) VALUES (?, ?)", (category, max_order + 1))
                
            # If category changed, assign new column_index at the end
            if old_category != category:
                cursor.execute("SELECT COALESCE(MAX(column_index), -1) FROM feeds WHERE category = ?", (category,))
                max_idx = cursor.fetchone()[0]
                column_index = max_idx + 1
            else:
                column_index = old_feed['column_index']
                
            url_changed = (old_url != url)
            if url_changed:
                cursor.execute("DELETE FROM articles WHERE feed_id = ?", (feed_id,))
                
            cursor.execute("""
                UPDATE feeds
                SET name = ?, url = ?, category = ?, column_index = ?
                WHERE id = ?
            """, (name, url, category, column_index, feed_id))
            
            conn.commit()
            conn.close()
            
            if url_changed:
                try:
                    entries = fetch_feed_entries(url)
                    if entries:
                        save_parsed_entries(feed_id, entries, url)
                except Exception as e:
                    print(f"Error crawling updated feed: {e}")
                    
            return jsonify({"status": "success"})
        except sqlite3.IntegrityError:
            return jsonify({"error": "Já existe um feed cadastrado com esta URL"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    elif request.method == 'DELETE':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM feeds WHERE id = ?", (feed_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({"error": "Feed não encontrado"}), 404
                
            cursor.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
            conn.commit()
            conn.close()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/feeds/reorder', methods=['POST'])
def api_reorder_feeds():
    data = request.get_json() or {}
    category = data.get('category')
    feed_ids = data.get('feed_ids')
    
    if not category or not isinstance(feed_ids, list):
        return jsonify({"error": "Categoria e lista de IDs de feed são obrigatórios"}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for idx, fid in enumerate(feed_ids):
            cursor.execute("""
                UPDATE feeds
                SET column_index = ?
                WHERE id = ? AND category = ?
            """, (idx, fid, category))
            
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories', methods=['GET', 'POST'])
def api_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'GET':
        try:
            cursor.execute("SELECT id, name, display_order FROM categories ORDER BY display_order, name")
            cats = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return jsonify(cats)
        except Exception as e:
            conn.close()
            return jsonify({"error": str(e)}), 500
            
    elif request.method == 'POST':
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        if not name:
            conn.close()
            return jsonify({"error": "O nome da categoria não pode ser vazio"}), 400
        try:
            cursor.execute("SELECT COALESCE(MAX(display_order), 0) FROM categories")
            max_order = cursor.fetchone()[0]
            cursor.execute("INSERT INTO categories (name, display_order) VALUES (?, ?)", (name, max_order + 1))
            conn.commit()
            cat_id = cursor.lastrowid
            conn.close()
            return jsonify({"status": "success", "category": {"id": cat_id, "name": name}}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"error": "Esta categoria já existe"}), 400
        except Exception as e:
            conn.close()
            return jsonify({"error": str(e)}), 500

@app.route('/api/categories/<int:cat_id>', methods=['DELETE'])
def api_delete_category(cat_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get category name
        cursor.execute("SELECT name FROM categories WHERE id = ?", (cat_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({"error": "Categoria não encontrada"}), 404
        cat_name = row['name']
        
        # Delete category
        cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        
        # Delete feeds inside this category (cascades to articles)
        cursor.execute("DELETE FROM feeds WHERE category = ?", (cat_name,))
        
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/articles')
def api_articles():
    category = request.args.get('category')
    date = request.args.get('date')
    search = request.args.get('search')
    
    # If category is "Global", fetch all categories
    if category == 'Global':
        category = None
        
    try:
        articles = query_articles(category=category, date=date, search=search)
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/fetch', methods=['POST'])
def api_fetch():
    try:
        new_count = fetch_all_feeds()
        return jsonify({"status": "success", "new_articles_count": new_count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tags', methods=['GET', 'POST'])
def api_tags():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'GET':
        try:
            cursor.execute("SELECT id, word, color FROM tags ORDER BY word")
            tags = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return jsonify(tags)
        except Exception as e:
            conn.close()
            return jsonify({"error": str(e)}), 500
            
    elif request.method == 'POST':
        data = request.get_json() or {}
        word = data.get('word', '').strip()
        color = data.get('color', 'red').strip()
        if color not in ['red', 'green', 'blue', 'purple', 'orange']:
            color = 'red'
            
        if not word:
            conn.close()
            return jsonify({"error": "A palavra-chave não pode ser vazia"}), 400
        try:
            cursor.execute("INSERT INTO tags (word, color) VALUES (?, ?)", (word, color))
            conn.commit()
            tag_id = cursor.lastrowid
            conn.close()
            return jsonify({"status": "success", "tag": {"id": tag_id, "word": word, "color": color}}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"error": "Esta palavra-chave já está cadastrada"}), 400
        except Exception as e:
            conn.close()
            return jsonify({"error": str(e)}), 500

@app.route('/api/tags/<int:tag_id>', methods=['DELETE'])
def api_delete_tag(tag_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Application Boot
# Application Boot
if __name__ == '__main__':
    # 1. Single Instance Check
    import urllib.request
    import webbrowser
    import sys
    try:
        req = urllib.request.Request("http://127.0.0.1:5000/", method="GET")
        with urllib.request.urlopen(req, timeout=1) as response:
            if response.status == 200:
                print("RSS Deck já está rodando. Abrindo no navegador...")
                webbrowser.open("http://127.0.0.1:5000/")
                sys.exit(0)
    except Exception:
        pass

    # Initialize DB & Feeds
    init_db()
    add_default_feeds()
    
    # Start polling thread
    start_background_polling()
    
    # Start Flask server in a background thread
    server_thread = threading.Thread(
        target=lambda: app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()
    
    # Wait 2 seconds and open browser automatically on first launch
    def auto_open_browser():
        time.sleep(2)
        try:
            webbrowser.open("http://127.0.0.1:5000/")
        except Exception as e:
            print(f"Failed to open browser automatically: {e}")
            
    threading.Thread(target=auto_open_browser, daemon=True).start()
    
    # System Tray Icon Support
    import pystray
    from PIL import Image, ImageDraw

    def create_tray_icon():
        # Match premium sidebar color (#0f1624)
        image = Image.new('RGB', (64, 64), color=(15, 22, 36))
        dc = ImageDraw.Draw(image)
        # Blue outer ring, orange inner ring, green center dot representing dynamic feeds connection
        dc.ellipse([8, 8, 56, 56], outline=(59, 130, 246), width=5)
        dc.ellipse([20, 20, 44, 44], outline=(245, 158, 11), width=4)
        dc.ellipse([28, 28, 36, 36], fill=(16, 185, 129))
        return image

    def on_clicked(icon, item):
        if str(item) == "Abrir RSS Deck":
            webbrowser.open("http://127.0.0.1:5000/")
        elif str(item) == "Sair":
            icon.stop()
            os._exit(0)

    icon = pystray.Icon(
        "rss_deck",
        create_tray_icon(),
        title="RSS Deck - Feeds em Tempo Real",
        menu=pystray.Menu(
            pystray.MenuItem("Abrir RSS Deck", on_clicked),
            pystray.MenuItem("Sair", on_clicked)
        )
    )
    
    print("RSS Deck starting in Tray mode on http://127.0.0.1:5000/ ...")
    icon.run()
else:
    # Running under pytest or similar
    init_db()
