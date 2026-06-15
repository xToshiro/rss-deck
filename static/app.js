// Category Icon Map for Default Categories
const CATEGORY_ICONS = {
  'Brasil': `<svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>`,
  'Mundo': `<svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>`,
  'Economia': `<svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>`,
  'Tecnologia': `<svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>`,
  'Guerras': `<svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path><path d="M12 12l4 4M12 12l-4 4"></path></svg>`
};
const DEFAULT_ICON = `<svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 11a9 9 0 0 1 9 9"></path><path d="M4 4a16 16 0 0 1 16 16"></path><circle cx="5" cy="19" r="1"></circle></svg>`;

// State Management
let currentCategory = 'Brasil';
let currentTimeTravelDate = null; // YYYY-MM-DD when active, null for real-time
let currentSearchQuery = '';
let feeds = []; // List of all feeds fetched from backend
let categories = []; // List of all categories fetched from backend
let articles = []; // Loaded articles list
let articleIdSet = new Set(); // Store loaded IDs to identify new arrivals
let isFirstLoad = true;
let pollingInterval = null;
let tagsList = []; // Registered highlight keywords

// DOM Selectors
const deckWorkspace = document.getElementById('deck-workspace');
const refreshBtn = document.getElementById('refresh-btn');
const searchInput = document.getElementById('search-input');
const clearSearchBtn = document.getElementById('clear-search-btn');
const datePicker = document.getElementById('date-picker');
const resetTimeBtn = document.getElementById('reset-time-btn');
const liveIndicator = document.getElementById('live-indicator');
const statusText = document.getElementById('status-text');
const notificationSound = document.getElementById('notification-sound');

// Feed Manager Selectors
const manageFeedsBtn = document.getElementById('manage-feeds-btn');
const feedManagerModal = document.getElementById('feed-manager-modal');
const closeModalBtn = document.getElementById('close-modal-btn');
const addCategoryForm = document.getElementById('add-category-form');
const addFeedForm = document.getElementById('add-feed-form');
const feedManagerList = document.getElementById('feed-manager-list');
const newFeedCategorySelect = document.getElementById('new-feed-category');
const tabNavigation = document.getElementById('tab-navigation');

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await loadCategories();
  await loadFeeds();
  await loadTags(); // Load tags from database
  await loadDashboard();
  
  // Real-time polling every 15 seconds
  pollingInterval = setInterval(pollForUpdates, 15000);
});

// Event Listeners Setup
function setupEventListeners() {
  // Manual Refresh
  refreshBtn.addEventListener('click', triggerManualRefresh);

  // Search input
  let searchTimeout;
  searchInput.addEventListener('input', (e) => {
    currentSearchQuery = e.target.value.trim();
    clearSearchBtn.style.display = currentSearchQuery.length > 0 ? 'block' : 'none';
    
    // Debounce search requests to avoid database spam
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      loadDashboard();
    }, 300);
  });

  clearSearchBtn.addEventListener('click', () => {
    searchInput.value = '';
    currentSearchQuery = '';
    clearSearchBtn.style.display = 'none';
    loadDashboard();
  });

  // Date picker (Time Travel)
  datePicker.addEventListener('change', (e) => {
    const selectedDate = e.target.value;
    if (selectedDate) {
      enableTimeTravel(selectedDate);
    } else {
      disableTimeTravel();
    }
  });

  // Reset Time Travel button
  resetTimeBtn.addEventListener('click', () => {
    disableTimeTravel();
  });

  // Tag Manager listeners
  const tagInput = document.getElementById('tag-input');
  const addTagBtn = document.getElementById('add-tag-btn');

  addTagBtn.addEventListener('click', addTag);
  tagInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      addTag();
    }
  });

  // Feed Manager modal listeners
  manageFeedsBtn.addEventListener('click', openFeedManagerModal);
  closeModalBtn.addEventListener('click', closeFeedManagerModal);
  feedManagerModal.addEventListener('click', (e) => {
    if (e.target === feedManagerModal) {
      closeFeedManagerModal();
    }
  });
  addCategoryForm.addEventListener('submit', handleAddCategory);
  addFeedForm.addEventListener('submit', handleAddFeed);
}

// Switch categories tab
function switchTab(category) {
  if (currentCategory === category) return;
  
  currentCategory = category;
  
  // Toggle visual states
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-category') === category);
  });
  
  // Clean first-load flags to enable nice slide anim on reload
  isFirstLoad = true;
  loadDashboard();
}

// Time travel triggers
function enableTimeTravel(date) {
  currentTimeTravelDate = date;
  
  // Update state UI indicators
  liveIndicator.classList.remove('live');
  liveIndicator.classList.add('time-travel-mode');
  statusText.textContent = `Modo Histórico`;
  
  resetTimeBtn.style.display = 'block';
  loadDashboard();
}

function disableTimeTravel() {
  currentTimeTravelDate = null;
  datePicker.value = '';
  
  // Update state UI indicators
  liveIndicator.classList.remove('time-travel-mode');
  liveIndicator.classList.add('live');
  statusText.textContent = 'Tempo Real';
  
  resetTimeBtn.style.display = 'none';
  loadDashboard();
}

// Load keywords tags from API
async function loadTags() {
  try {
    const response = await fetch('/api/tags');
    if (!response.ok) throw new Error("Erro ao carregar tags");
    tagsList = await response.json();
    renderTagsList();
  } catch (error) {
    console.error("Error loading tags list:", error);
  }
}

// Render keywords tags list in sidebar
function renderTagsList() {
  const container = document.getElementById('tags-list');
  container.innerHTML = '';
  
  if (tagsList.length === 0) {
    container.innerHTML = `<span style="font-size: 0.8rem; color: var(--text-muted);">Nenhuma tag ativa</span>`;
    return;
  }
  
  tagsList.forEach(tag => {
    const chip = document.createElement('span');
    chip.className = 'tag-chip';
    chip.innerHTML = `
      ${escapeHtml(tag.word)}
      <button class="tag-delete-btn" data-id="${tag.id}">&times;</button>
    `;
    
    // Delete event listener
    chip.querySelector('.tag-delete-btn').addEventListener('click', () => {
      deleteTag(tag.id);
    });
    
    container.appendChild(chip);
  });
}

// Add tag keyword to DB
async function addTag() {
  const input = document.getElementById('tag-input');
  const word = input.value.trim();
  if (!word) return;
  
  try {
    const response = await fetch('/api/tags', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ word })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Erro ao adicionar tag");
    
    input.value = '';
    await loadTags();
    await loadDashboard(); // Re-render to highlight keywords
  } catch (error) {
    alert(error.message);
  }
}

// Delete tag keyword from DB
async function deleteTag(id) {
  try {
    const response = await fetch(`/api/tags/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error("Erro ao deletar tag");
    
    await loadTags();
    await loadDashboard(); // Re-render to clear highlights
  } catch (error) {
    alert(error.message);
  }
}

// Check title against tag words for pulsing highlight alerts
function highlightTitleTags(title) {
  let highlighted = escapeHtml(title);
  let hasMatch = false;
  
  if (!tagsList || tagsList.length === 0) return { html: highlighted, hasMatch };
  
  // Sort tags by length descending to match larger words first
  const sortedTags = [...tagsList].sort((a, b) => b.word.length - a.word.length);
  
  sortedTags.forEach(tag => {
    const escapedWord = escapeRegExp(tag.word);
    const regex = new RegExp(`(${escapedWord})`, 'gi');
    if (regex.test(highlighted)) {
      highlighted = highlighted.replace(regex, `<span class="pulsing-keyword">$1</span>`);
      hasMatch = true;
    }
  });
  
  return { html: highlighted, hasMatch };
}

// Helper to escape regex special characters
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Fetch configured feeds
async function loadFeeds() {
  try {
    const response = await fetch('/api/feeds');
    if (!response.ok) throw new Error("Erro ao carregar feeds");
    feeds = await response.json();
    document.getElementById('db-info').textContent = `Feeds: ${feeds.length}`;
  } catch (error) {
    console.error("Error loading feeds list:", error);
  }
}

// Core Dashboard Loading
async function loadDashboard() {
  showWorkspaceLoading(true);
  
  try {
    // Build query params
    let url = `/api/articles?category=${currentCategory}`;
    if (currentTimeTravelDate) {
      url += `&date=${currentTimeTravelDate}`;
    }
    if (currentSearchQuery) {
      url += `&search=${encodeURIComponent(currentSearchQuery)}`;
    }
    
    const response = await fetch(url);
    if (!response.ok) throw new Error("Erro ao buscar artigos");
    
    articles = await response.json();
    
    // Identify new entries for notification sound
    let hasNewItems = false;
    if (!isFirstLoad && !currentTimeTravelDate && !currentSearchQuery) {
      articles.forEach(art => {
        if (!articleIdSet.has(art.id)) {
          hasNewItems = true;
          // Temporarily tag as new to show transition highlight
          art.isBrandNew = true;
        }
      });
    }
    
    // Re-fill the loaded IDs cache
    articleIdSet.clear();
    articles.forEach(art => articleIdSet.add(art.id));
    
    if (hasNewItems) {
      playNotificationSound();
    }
    
    renderDeckColumns();
    isFirstLoad = false;
  } catch (error) {
    console.error("Error loading articles dashboard:", error);
    renderErrorState();
  } finally {
    showWorkspaceLoading(false);
  }
}

// Fetch and append without clearing (Poller)
async function pollForUpdates() {
  // Only poll in live mode and without search filter
  if (currentTimeTravelDate || currentSearchQuery) return;
  
  try {
    let url = `/api/articles?category=${currentCategory}`;
    const response = await fetch(url);
    if (!response.ok) return;
    
    const newArticles = await response.json();
    const newArrivals = [];
    
    newArticles.forEach(art => {
      if (!articleIdSet.has(art.id)) {
        art.isBrandNew = true;
        art.isNewArrival = true; // flag to trigger keyframe animation
        articleIdSet.add(art.id);
        newArrivals.push(art);
      }
    });
    
    if (newArrivals.length > 0) {
      // Prepend the new arrivals so they appear at the top
      articles = [...newArrivals, ...articles];
      playNotificationSound();
      
      // Iterate backwards so the newest is prepended last (putting it at the absolute top)
      for (let i = newArrivals.length - 1; i >= 0; i--) {
        prependArticleToColumnDOM(newArrivals[i]);
      }
      
      // Update header counters
      updateItemCounters();
    }
  } catch (error) {
    console.warn("Polling update failed:", error);
  }
}

// Prepend single card element to DOM with slide animation
function prependArticleToColumnDOM(art) {
  const listContainer = document.getElementById(`list-${art.feed_id}`);
  if (!listContainer) return;
  
  // Remove empty state message if it is present
  const placeholder = listContainer.querySelector('.empty-placeholder');
  if (placeholder) {
    placeholder.remove();
  }
  
  const card = document.createElement('article');
  const highlightResult = highlightTitleTags(art.title);
  
  card.className = `article-card new-item new-arrival${highlightResult.hasMatch ? ' pulsing-alert' : ''}`;
  card.addEventListener('click', () => {
    window.open(art.link, '_blank');
  });
  
  card.innerHTML = `
    <div class="article-header">
      <h4 class="article-title">${highlightResult.html}</h4>
      <span class="article-date">${formatRelativeTime(art.pub_date)}</span>
    </div>
    ${art.description ? `<p class="article-body">${escapeHtml(art.description)}</p>` : ''}
    <div class="article-footer">
      <span class="read-more-link">
        Ler tudo
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="5" y1="12" x2="19" y2="12"></line>
          <polyline points="12 5 19 12 12 19"></polyline>
        </svg>
      </span>
    </div>
  `;
  
  // Prepend card as first child
  listContainer.insertBefore(card, listContainer.firstChild);
  
  // Remove animation class after animation completes
  setTimeout(() => {
    card.classList.remove('new-arrival');
  }, 1000);
}

// Refresh article counts inside headers
function updateItemCounters() {
  const activeFeeds = feeds.filter(f => f.category === currentCategory);
  activeFeeds.forEach(feed => {
    const feedArticles = articles.filter(art => art.feed_id === feed.id);
    const colEl = document.getElementById(`col-${feed.id}`);
    if (colEl) {
      const counter = colEl.querySelector('.item-counter');
      if (counter) {
        counter.textContent = feedArticles.length;
      }
    }
  });
}

// Manual Refresh Request
async function triggerManualRefresh() {
  refreshBtn.classList.add('spinning');
  deckWorkspace.classList.add('workspace-refreshing');
  const cols = deckWorkspace.querySelectorAll('.deck-column');
  cols.forEach(c => c.classList.add('column-refreshing'));
  
  try {
    const response = await fetch('/api/fetch', { method: 'POST' });
    if (!response.ok) throw new Error("Erro no fetch backend");
    const result = await response.json();
    
    console.log(`Manual fetch completed. Inserted articles: ${result.new_articles_count}`);
    await loadDashboard();
  } catch (error) {
    console.error("Manual refresh error:", error);
    alert("Falha ao atualizar feeds. Verifique se o backend está ativo.");
  } finally {
    refreshBtn.classList.remove('spinning');
    deckWorkspace.classList.remove('workspace-refreshing');
    cols.forEach(c => c.classList.remove('column-refreshing'));
  }
}

// Play notification sound safely
function playNotificationSound() {
  notificationSound.currentTime = 0;
  notificationSound.play().catch(e => {
    // Autoplay policy might block it. Ignore gracefully.
    console.log("Audio play blocked by browser policy:", e.message);
  });
}

// Format Date string: "YYYY-MM-DD HH:MM:SS" (UTC) into Relative local format
function formatRelativeTime(dateStr) {
  try {
    const parsedDate = new Date(dateStr + " UTC");
    if (isNaN(parsedDate.getTime())) return dateStr;
    
    const diffMs = new Date() - parsedDate;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return "Agora";
    if (diffMins < 60) return `${diffMins}m`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h`;
    
    return parsedDate.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return dateStr;
  }
}

// Render dynamic columns inside Workspace
function renderDeckColumns() {
  // Clear the deck first
  deckWorkspace.innerHTML = '';
  
  // Filter feeds for active category
  const activeFeeds = feeds.filter(f => f.category === currentCategory);
  
  if (activeFeeds.length === 0) {
    deckWorkspace.innerHTML = `
      <div class="empty-placeholder">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <p>Nenhuma coluna configurada para esta aba.</p>
      </div>
    `;
    return;
  }
  
  // Build and render columns
  activeFeeds.forEach((feed, idx) => {
    // Filter articles for this feed id
    const feedArticles = articles.filter(art => art.feed_id === feed.id);
    
    const columnElement = document.createElement('section');
    columnElement.className = 'deck-column';
    columnElement.id = `col-${feed.id}`;
    columnElement.setAttribute('draggable', 'true');
    columnElement.dataset.feedId = feed.id;
    // Stagger slide entry animation
    columnElement.style.animationDelay = `${idx * 0.08}s`;
    
    columnElement.innerHTML = `
      <div class="deck-column-header">
        <div class="column-title-area">
          <span class="column-title">${feed.name}</span>
          <span class="column-meta">${feed.category} Feed</span>
        </div>
        <div class="column-actions">
          <span class="item-counter">${feedArticles.length}</span>
        </div>
      </div>
      <div class="column-articles-list" id="list-${feed.id}">
        <!-- Cards insert here -->
      </div>
    `;
    
    deckWorkspace.appendChild(columnElement);
    
    const articlesListContainer = document.getElementById(`list-${feed.id}`);
    
    if (feedArticles.length === 0) {
      articlesListContainer.innerHTML = `
        <div class="empty-placeholder">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <p>Nenhuma notícia encontrada.</p>
        </div>
      `;
    } else {
      feedArticles.forEach(art => {
        const card = document.createElement('article');
        const highlightResult = highlightTitleTags(art.title);
        
        card.className = `article-card${art.isBrandNew ? ' new-item' : ''}${highlightResult.hasMatch ? ' pulsing-alert' : ''}`;
        
        // Setup simple card click triggers original article in a new tab
        card.addEventListener('click', () => {
          window.open(art.link, '_blank');
        });
        
        card.innerHTML = `
          <div class="article-header">
            <h4 class="article-title">${highlightResult.html}</h4>
            <span class="article-date">${formatRelativeTime(art.pub_date)}</span>
          </div>
          ${art.description ? `<p class="article-body">${escapeHtml(art.description)}</p>` : ''}
          <div class="article-footer">
            <span class="read-more-link">
              Ler tudo
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
              </svg>
            </span>
          </div>
        `;
        articlesListContainer.appendChild(card);
      });
    }
  });

  // Wire HTML5 Drag & Drop handlers
  setupDragAndDrop();
}

// Show/Hide general workspace loading indicator
function showWorkspaceLoading(show) {
  let loader = document.getElementById('loading-overlay');
  if (show) {
    if (!loader) {
      loader = document.createElement('div');
      loader.id = 'loading-overlay';
      loader.className = 'loading-overlay';
      loader.innerHTML = `
        <div class="spinner"></div>
        <p>Carregando colunas do RSS...</p>
      `;
      deckWorkspace.appendChild(loader);
    }
  } else {
    if (loader) loader.remove();
  }
}

// Error state rendering
function renderErrorState() {
  deckWorkspace.innerHTML = `
    <div class="empty-placeholder" style="color: #ef4444;">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <p>Falha ao conectar com a API. Garanta que o servidor está rodando.</p>
    </div>
  `;
}

// Helper to escape HTML tags to avoid XSS issues
function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ==========================================
// NEW FEATURES: CATEGORIES AND FEEDS MANAGER
// ==========================================

// Load categories from API
async function loadCategories() {
  try {
    const response = await fetch('/api/categories');
    if (!response.ok) throw new Error("Erro ao carregar categorias");
    categories = await response.json();
    
    // Render tabs dynamically
    renderCategoryTabs();
    
    // Populate form dropdown select
    populateCategoryDropdown();
  } catch (error) {
    console.error("Error loading categories:", error);
  }
}

// Render tabs dynamically
function renderCategoryTabs() {
  tabNavigation.innerHTML = '';
  if (categories.length === 0) return;
  
  categories.forEach(cat => {
    const name = cat.name;
    const btn = document.createElement('button');
    btn.className = `tab-btn${currentCategory === name ? ' active' : ''}`;
    btn.setAttribute('data-category', name);
    
    const iconSvg = CATEGORY_ICONS[name] || DEFAULT_ICON;
    
    btn.innerHTML = `
      <span class="tab-indicator-dot"></span>
      ${iconSvg}
      ${escapeHtml(name)}
    `;
    
    btn.addEventListener('click', () => {
      switchTab(name);
    });
    
    tabNavigation.appendChild(btn);
  });
}

// Populate select dropdown
function populateCategoryDropdown() {
  newFeedCategorySelect.innerHTML = '<option value="" disabled selected>Selecione uma categoria...</option>';
  categories.forEach(cat => {
    const opt = document.createElement('option');
    opt.value = cat.name;
    opt.textContent = cat.name;
    newFeedCategorySelect.appendChild(opt);
  });
}

// Modal open/close controls
function openFeedManagerModal() {
  feedManagerModal.style.display = 'flex';
  renderFeedManagerList();
}

function closeFeedManagerModal() {
  feedManagerModal.style.display = 'none';
}

// Form Category submit
async function handleAddCategory(e) {
  e.preventDefault();
  const input = document.getElementById('new-category-name');
  const name = input.value.trim();
  if (!name) return;
  
  try {
    const response = await fetch('/api/categories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Erro ao criar categoria");
    
    input.value = '';
    await loadCategories();
  } catch (err) {
    alert(err.message);
  }
}

// Form Feed submit
async function handleAddFeed(e) {
  e.preventDefault();
  const nameInput = document.getElementById('new-feed-name');
  const urlInput = document.getElementById('new-feed-url');
  
  const name = nameInput.value.trim();
  const url = urlInput.value.trim();
  const category = newFeedCategorySelect.value;
  
  if (!name || !url || !category) return;
  
  try {
    const response = await fetch('/api/feeds', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, url, category })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Erro ao adicionar feed");
    
    nameInput.value = '';
    urlInput.value = '';
    newFeedCategorySelect.value = '';
    
    await loadFeeds();
    renderFeedManagerList();
    await loadDashboard();
  } catch (err) {
    alert(err.message);
  }
}

// Render active feeds list grouped by category in Manager Modal
function renderFeedManagerList() {
  feedManagerList.innerHTML = '';
  
  if (feeds.length === 0) {
    feedManagerList.innerHTML = `<p style="font-size:0.85rem; color:var(--text-muted); text-align:center; padding:1.5rem 0;">Nenhum feed ativo.</p>`;
    return;
  }
  
  // Group feeds
  const grouped = {};
  feeds.forEach(f => {
    if (!grouped[f.category]) {
      grouped[f.category] = [];
    }
    grouped[f.category].push(f);
  });
  
  Object.keys(grouped).forEach(catName => {
    const groupDiv = document.createElement('div');
    groupDiv.className = 'category-group';
    
    const header = document.createElement('div');
    header.className = 'category-group-header';
    header.textContent = catName;
    groupDiv.appendChild(header);
    
    grouped[catName].forEach(feed => {
      const row = document.createElement('div');
      row.className = 'feed-manager-row';
      row.id = `mgr-row-${feed.id}`;
      
      row.innerHTML = `
        <div class="feed-info">
          <span class="feed-row-name">${escapeHtml(feed.name)}</span>
          <span class="feed-row-url">${escapeHtml(feed.url)}</span>
        </div>
        <div class="feed-row-actions">
          <button class="edit-row-btn" data-id="${feed.id}">Editar</button>
          <button class="delete-row-btn" data-id="${feed.id}">Excluir</button>
        </div>
      `;
      
      // Hook buttons
      row.querySelector('.delete-row-btn').addEventListener('click', () => handleDeleteFeed(feed.id));
      row.querySelector('.edit-row-btn').addEventListener('click', () => toggleEditFeedRow(feed));
      
      groupDiv.appendChild(row);
    });
    
    feedManagerList.appendChild(groupDiv);
  });
}

// Delete feed handler
async function handleDeleteFeed(id) {
  if (!confirm("Tem certeza que deseja excluir este feed? Todas as notícias vinculadas a ele serão apagadas.")) return;
  
  try {
    const response = await fetch(`/api/feeds/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error("Erro ao excluir feed");
    
    await loadFeeds();
    renderFeedManagerList();
    await loadDashboard();
  } catch (err) {
    alert(err.message);
  }
}

// Inline editing row toggle
function toggleEditFeedRow(feed) {
  const row = document.getElementById(`mgr-row-${feed.id}`);
  if (!row) return;
  
  row.innerHTML = `
    <form class="feed-edit-form" id="edit-form-${feed.id}">
      <div class="form-group">
        <label>Nome do Feed</label>
        <input type="text" id="edit-name-${feed.id}" value="${escapeHtml(feed.name)}" required>
      </div>
      <div class="form-group">
        <label>URL do RSS</label>
        <input type="url" id="edit-url-${feed.id}" value="${escapeHtml(feed.url)}" required>
      </div>
      <div class="form-group">
        <label>Categoria</label>
        <select id="edit-category-${feed.id}" required>
          <!-- Categories filled -->
        </select>
      </div>
      <div style="display:flex; gap:0.5rem; margin-top:0.25rem;">
        <button type="submit" class="save-row-btn">Salvar</button>
        <button type="button" class="cancel-row-btn" id="edit-cancel-${feed.id}">Cancelar</button>
      </div>
    </form>
  `;
  
  // Fill category select
  const select = document.getElementById(`edit-category-${feed.id}`);
  categories.forEach(cat => {
    const opt = document.createElement('option');
    opt.value = cat.name;
    opt.textContent = cat.name;
    if (cat.name === feed.category) opt.selected = true;
    select.appendChild(opt);
  });
  
  // Hook cancel
  document.getElementById(`edit-cancel-${feed.id}`).addEventListener('click', () => {
    renderFeedManagerList();
  });
  
  // Hook submit/save
  document.getElementById(`edit-form-${feed.id}`).addEventListener('submit', async (e) => {
    e.preventDefault();
    const newName = document.getElementById(`edit-name-${feed.id}`).value.trim();
    const newUrl = document.getElementById(`edit-url-${feed.id}`).value.trim();
    const newCat = select.value;
    
    if (!newName || !newUrl || !newCat) return;
    
    try {
      const response = await fetch(`/api/feeds/${feed.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName, url: newUrl, category: newCat })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Erro ao salvar feed");
      
      const categoryTabChanged = (feed.category !== newCat);
      
      await loadCategories();
      await loadFeeds();
      
      if (categoryTabChanged && currentCategory === feed.category) {
        currentCategory = newCat;
      }
      
      renderFeedManagerList();
      await loadDashboard();
    } catch (err) {
      alert(err.message);
    }
  });
}

// ==========================================
// DRAG AND DROP COLUMN REORDERING
// ==========================================

function setupDragAndDrop() {
  const columns = document.querySelectorAll('.deck-column');
  
  columns.forEach(col => {
    col.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/plain', col.dataset.feedId);
      col.classList.add('dragging');
    });
    
    col.addEventListener('dragend', () => {
      col.classList.remove('dragging');
      deckWorkspace.classList.remove('drag-over');
    });
  });
  
  deckWorkspace.addEventListener('dragover', (e) => {
    e.preventDefault();
    deckWorkspace.classList.add('drag-over');
    
    const draggingCol = document.querySelector('.deck-column.dragging');
    if (!draggingCol) return;
    
    const afterElement = getDragAfterElement(deckWorkspace, e.clientX);
    if (afterElement == null) {
      deckWorkspace.appendChild(draggingCol);
    } else {
      deckWorkspace.insertBefore(draggingCol, afterElement);
    }
  });
  
  deckWorkspace.addEventListener('drop', async (e) => {
    e.preventDefault();
    deckWorkspace.classList.remove('drag-over');
    
    // Find visual column elements order in DOM
    const currentCols = [...deckWorkspace.querySelectorAll('.deck-column')];
    const newOrderIds = currentCols.map(col => parseInt(col.dataset.feedId));
    
    try {
      const response = await fetch('/api/feeds/reorder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: currentCategory,
          feed_ids: newOrderIds
        })
      });
      if (!response.ok) throw new Error("Erro ao salvar ordem no servidor");
      
      // Update local feeds list to reflect new order
      const otherCategoryFeeds = feeds.filter(f => f.category !== currentCategory);
      const sortedActiveFeeds = newOrderIds.map(fid => feeds.find(f => f.id === fid));
      feeds = [...sortedActiveFeeds, ...otherCategoryFeeds];
      
      // Refresh Counters/DOM bindings without full wipe if necessary, but reordering visual is already set by Drag
    } catch (err) {
      console.warn("Could not save column order:", err);
      // Rollback visual elements
      await loadFeeds();
      renderDeckColumns();
    }
  });
}

// Find closest elements for insert target
function getDragAfterElement(container, x) {
  const draggableElements = [...container.querySelectorAll('.deck-column:not(.dragging)')];
  
  return draggableElements.reduce((closest, child) => {
    const box = child.getBoundingClientRect();
    const offset = x - box.left - box.width / 2;
    if (offset < 0 && offset > closest.offset) {
      return { offset: offset, element: child };
    } else {
      return closest;
    }
  }, { offset: Number.NEGATIVE_INFINITY }).element;
}
