import os
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
import feedparser

# Import functions from app.py
# We will define these functions in app.py to match this test setup.
import app

TEST_DB = "test_rss_deck.db"

@pytest.fixture
def clean_db():
    """Fixture to set up a clean temporary database and remove it after tests."""
    app.DB_FILE = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    app.init_db()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_database_initialization(clean_db):
    """Verify that tables are created correctly on initialization."""
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    
    # Check feeds table
    cursor.execute("PRAGMA table_info(feeds)")
    feeds_cols = {col[1] for col in cursor.fetchall()}
    assert "name" in feeds_cols
    assert "url" in feeds_cols
    assert "category" in feeds_cols
    assert "column_index" in feeds_cols

    # Check articles table
    cursor.execute("PRAGMA table_info(articles)")
    articles_cols = {col[1] for col in cursor.fetchall()}
    assert "feed_id" in articles_cols
    assert "guid" in articles_cols
    assert "title" in articles_cols
    assert "pub_date" in articles_cols
    
    conn.close()

def test_add_default_feeds(clean_db):
    """Verify default feeds are inserted on setup."""
    app.add_default_feeds()
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM feeds")
    count = cursor.fetchone()[0]
    assert count > 0
    conn.close()

def test_standardize_date():
    """Verify that dates of various feed formats are standardized into YYYY-MM-DD HH:MM:SS."""
    # Test RFC 822 format
    parsed_struct = feedparser.parse("").datetime = (2026, 6, 15, 10, 30, 0, 0, 0, 0)
    # Mocking standard structure return from feedparser entry
    entry = MagicMock()
    entry.published_parsed = (2026, 6, 15, 10, 30, 0, 0, 166, 0)
    entry.get = lambda x, default=None: entry.published_parsed if x == 'published_parsed' else default
    
    std_date = app.standardize_pub_date(entry)
    assert std_date == "2026-06-15 10:30:00"

    # Test fallback to current date/time if no publication date is present
    entry_no_date = MagicMock()
    entry_no_date.get = lambda x, default=None: default
    std_date_fallback = app.standardize_pub_date(entry_no_date)
    assert len(std_date_fallback) == 19 # YYYY-MM-DD HH:MM:SS length

def test_parse_and_insert_articles(clean_db):
    """Verify feed parsing, duplication guard, and guid fallback to link."""
    # Set up mock feed metadata
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO feeds (name, url, category, column_index) VALUES (?, ?, ?, ?)",
                   ("Mock Feed", "http://mock.feed", "Brasil", 0))
    feed_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Create mock XML feed entries
    xml_data = """<?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0">
      <channel>
        <title>Mock Channel</title>
        <link>http://mock.feed</link>
        <item>
          <title>Noticia Um</title>
          <link>http://mock.feed/noticia1</link>
          <description>Descricao noticia um</description>
          <guid>guid-1</guid>
          <pubDate>Mon, 15 Jun 2026 10:00:00 -0300</pubDate>
        </item>
        <item>
          <title>Noticia Sem Guid</title>
          <link>http://mock.feed/noticia-sem-guid</link>
          <description>Descricao noticia sem guid</description>
          <pubDate>Mon, 15 Jun 2026 11:00:00 -0300</pubDate>
        </item>
      </channel>
    </rss>
    """
    
    # Run fetch and insert using the parsed XML
    parsed_feed = feedparser.parse(xml_data)
    new_count = app.save_parsed_entries(feed_id, parsed_feed.entries)
    
    assert new_count == 2

    # Fetch articles from db
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT guid, title, link, pub_date FROM articles ORDER BY id")
    articles = cursor.fetchall()
    conn.close()

    assert len(articles) == 2
    # Guid-1 checks
    assert articles[0][0] == "guid-1"
    assert articles[0][1] == "Noticia Um"
    # Guid fallback to link checks
    assert articles[1][0] == "http://mock.feed/noticia-sem-guid"
    assert articles[1][1] == "Noticia Sem Guid"

    # Attempt to insert same entries again (duplication guard)
    new_count_dup = app.save_parsed_entries(feed_id, parsed_feed.entries)
    assert new_count_dup == 0

def test_article_queries(clean_db):
    """Verify filtering articles by category, date, and keyword searches."""
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    # Insert feeds
    cursor.execute("INSERT INTO feeds (name, url, category, column_index) VALUES ('F1', 'url1', 'Brasil', 0)")
    feed_br = cursor.lastrowid
    cursor.execute("INSERT INTO feeds (name, url, category, column_index) VALUES ('F2', 'url2', 'Mundo', 0)")
    feed_mu = cursor.lastrowid
    
    # Insert articles
    cursor.execute("INSERT INTO articles (feed_id, guid, title, description, link, pub_date) VALUES (?, ?, ?, ?, ?, ?)",
                   (feed_br, "g1", "Copa do Mundo no Brasil", "Futebol e alegria", "link1", "2026-06-15 10:00:00"))
    cursor.execute("INSERT INTO articles (feed_id, guid, title, description, link, pub_date) VALUES (?, ?, ?, ?, ?, ?)",
                   (feed_br, "g2", "Eleicoes nacionais", "Votacao ocorrendo hoje", "link2", "2026-06-15 12:00:00"))
    cursor.execute("INSERT INTO articles (feed_id, guid, title, description, link, pub_date) VALUES (?, ?, ?, ?, ?, ?)",
                   (feed_mu, "g3", "Global warming summit", "Leaders gather in Paris", "link3", "2026-06-16 09:00:00"))
    conn.commit()
    conn.close()

    # Query: Category = Brasil
    br_articles = app.query_articles(category="Brasil")
    assert len(br_articles) == 2
    assert br_articles[0]["title"] == "Eleicoes nacionais"  # Sorted by pub_date desc

    # Query: Category = Mundo
    mu_articles = app.query_articles(category="Mundo")
    assert len(mu_articles) == 1
    assert mu_articles[0]["title"] == "Global warming summit"

    # Query: Date = 2026-06-15
    date_articles = app.query_articles(date="2026-06-15")
    assert len(date_articles) == 2

    # Query: Date = 2026-06-16
    date_articles_2 = app.query_articles(date="2026-06-16")
    assert len(date_articles_2) == 1
    assert date_articles_2[0]["title"] == "Global warming summit"

    # Query: Search = "Copa"
    search_articles = app.query_articles(search="Copa")
    assert len(search_articles) == 1
    assert search_articles[0]["title"] == "Copa do Mundo no Brasil"

    # Query: Search = "Votacao" (description match)
    search_desc = app.query_articles(search="Votacao")
    assert len(search_desc) == 1
    assert search_desc[0]["title"] == "Eleicoes nacionais"

@pytest.fixture
def client(clean_db):
    """Flask test client."""
    app.app.config['TESTING'] = True
    with app.app.test_client() as client:
        yield client

def test_api_feeds(client):
    """Test the GET /api/feeds endpoint."""
    app.add_default_feeds()
    response = client.get('/api/feeds')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) > 0
    assert "name" in data[0]
    assert "url" in data[0]
    assert "category" in data[0]

def test_api_articles(client):
    """Test the GET /api/articles endpoint."""
    response = client.get('/api/articles')
    assert response.status_code == 200
    assert response.get_json() == []

@patch('app.fetch_all_feeds')
def test_api_fetch(mock_fetch, client):
    """Test the POST /api/fetch endpoint."""
    mock_fetch.return_value = 5
    response = client.post('/api/fetch')
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["new_articles_count"] == 5

def test_api_tags(client):
    """Test GET, POST, and DELETE /api/tags endpoints."""
    # 1. Fetch tags (should be empty initially)
    response = client.get('/api/tags')
    assert response.status_code == 200
    assert response.get_json() == []

    # 2. Add a new tag keyword
    response = client.post('/api/tags', json={"word": "Trump"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "success"
    assert data["tag"]["word"] == "Trump"
    tag_id = data["tag"]["id"]

    # 3. Add duplicate tag keyword (should fail)
    response = client.post('/api/tags', json={"word": "Trump"})
    assert response.status_code == 400
    assert "error" in response.get_json()

    # 4. Fetch tags again
    response = client.get('/api/tags')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["word"] == "Trump"

    # 5. Delete tag keyword
    response = client.delete(f'/api/tags/{tag_id}')
    assert response.status_code == 200
    assert response.get_json()["status"] == "success"

    # 6. Fetch tags again (should be empty)
    response = client.get('/api/tags')
    assert response.status_code == 200
    assert response.get_json() == []

def test_api_categories(client):
    """Test categories API endpoints (GET and POST)."""
    # 1. Fetch categories (should have default seeded categories if add_default_feeds is run, but clean_db starts with empty tables. Wait, clean_db calls init_db which does not run add_default_feeds. So it should be empty).
    response = client.get('/api/categories')
    assert response.status_code == 200
    assert response.get_json() == []

    # 2. Add new category
    response = client.post('/api/categories', json={"name": "Ciência"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "success"
    assert data["category"]["name"] == "Ciência"

    # 3. Add duplicate category (should fail)
    response = client.post('/api/categories', json={"name": "Ciência"})
    assert response.status_code == 400
    assert "error" in response.get_json()

    # 4. Fetch list again
    response = client.get('/api/categories')
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "Ciência"

def test_feed_crud(client):
    """Test feeds POST, PUT, DELETE endpoints."""
    # Seed categories first
    client.post('/api/categories', json={"name": "Tecnologia"})
    
    # 1. Add new feed
    response = client.post('/api/feeds', json={
        "name": "Gizmodo",
        "url": "https://gizmodo.uol.com.br/feed/",
        "category": "Tecnologia"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "success"
    assert data["feed"]["name"] == "Gizmodo"
    feed_id = data["feed"]["id"]

    # 2. Update feed (PUT)
    response = client.put(f'/api/feeds/{feed_id}', json={
        "name": "Gizmodo Brasil",
        "url": "https://gizmodo.uol.com.br/feed/",
        "category": "Tecnologia"
    })
    assert response.status_code == 200
    
    # Fetch feeds and verify name
    response = client.get('/api/feeds')
    feeds = response.get_json()
    assert feeds[0]["name"] == "Gizmodo Brasil"

    # 3. Delete feed (DELETE)
    response = client.delete(f'/api/feeds/{feed_id}')
    assert response.status_code == 200
    
    # Fetch feeds and verify it's gone
    response = client.get('/api/feeds')
    assert len(response.get_json()) == 0

def test_feeds_reorder(client):
    """Test feeds reordering endpoint."""
    conn = app.get_db_connection()
    cursor = conn.cursor()
    # Insert test feeds in "Brasil"
    cursor.execute("INSERT INTO feeds (name, url, category, column_index) VALUES ('F1', 'url1', 'Brasil', 0)")
    f1_id = cursor.lastrowid
    cursor.execute("INSERT INTO feeds (name, url, category, column_index) VALUES ('F2', 'url2', 'Brasil', 1)")
    f2_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Call reorder: F2 to position 0, F1 to position 1
    response = client.post('/api/feeds/reorder', json={
        "category": "Brasil",
        "feed_ids": [f2_id, f1_id]
    })
    assert response.status_code == 200

    # Verify indices in DB
    conn = app.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, column_index FROM feeds ORDER BY column_index")
    rows = cursor.fetchall()
    conn.close()

    assert rows[0]['id'] == f2_id
    assert rows[0]['column_index'] == 0
    assert rows[1]['id'] == f1_id
    assert rows[1]['column_index'] == 1

def test_uol_filter(clean_db):
    """Verify that empty/placeholder UOL articles are filtered out."""
    conn = app.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO feeds (name, url, category, column_index) VALUES ('UOL', 'https://uol.com.br/feed', 'Brasil', 0)")
    feed_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # 1. Feed items list
    entries = [
        # This one should be filtered out because title is "Notícias - UOL" and description is "Notícias UOL"
        {
            "title": "Notícias - UOL",
            "link": "https://noticias.uol.com.br/1",
            "summary": "Notícias UOL",
            "id": "uol-1"
        },
        # This one should be kept because it has a valid title and summary
        {
            "title": "Nova Descoberta Científica",
            "link": "https://noticias.uol.com.br/2",
            "summary": "Pesquisadores encontraram novos fósseis...",
            "id": "uol-2"
        },
        # This one should be filtered out because it has no summary/description
        {
            "title": "Apenas Título",
            "link": "https://noticias.uol.com.br/3",
            "id": "uol-3"
        }
    ]

    new_count = app.save_parsed_entries(feed_id, entries, "https://uol.com.br/feed")
    assert new_count == 1  # Only uol-2 should be inserted

    # Verify in DB
    conn = app.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT guid FROM articles WHERE feed_id = ?", (feed_id,))
    inserted = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert inserted == ["uol-2"]

