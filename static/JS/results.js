document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const searchData = document.getElementById('search-data');
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchQuery');
    const clearSearch = document.getElementById('clearSearch');
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const resultsList = document.getElementById('results-list');
    const resultTemplate = document.getElementById('result-item-template');
    const loader = loadMoreBtn?.querySelector('.loader');

    // State variables
    let currentPage = parseInt(searchData?.dataset.currentPage) || 1;
    let totalPages = parseInt(searchData?.dataset.totalPages) || 1;
    const query = searchData?.dataset.query || '';
    let hasMore = currentPage < totalPages;
    let isLoading = false;

    // Initialize application
    function init() {
        if (searchForm) {
            searchForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const searchQuery = searchInput.value.trim();
                if (searchQuery) {
                    window.location.href = `/search?q=${encodeURIComponent(searchQuery)}&page=1`;
                }
            });
        }

        if (clearSearch) clearSearch.addEventListener('click', clearSearchInput);
        
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', function(e) {
                e.preventDefault();
                if (!isLoading) {
                    handleLoadMore();
                }
            });
            updateLoadMoreButton();
        }
        
        // Initialize frequency bars for initial results
        initializeAllFrequencyVisualizations();
    }

    // Load more results handler
    async function handleLoadMore() {
        if (!hasMore || isLoading) return;
        
        isLoading = true;
        toggleLoadMoreButton(true);
        
        try {
            const nextPage = currentPage + 1;
            const response = await fetch(`/load-more?q=${encodeURIComponent(query)}&page=${nextPage}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success' && data.results?.length) {
                appendResults(data.results);
                
                currentPage = nextPage;
                totalPages = data.total_pages || totalPages;
                hasMore = currentPage < totalPages;
                
                updateLoadMoreButton();
                // Initialize frequency bars for newly loaded results
                initializeNewFrequencyVisualizations(data.results.length);
            } else {
                throw new Error(data.message || "No results found");
            }
        } catch (error) {
            console.error('Load more error:', error);
            showError(error.message || "Failed to load more results. Please try again.");
        } finally {
            isLoading = false;
            toggleLoadMoreButton(false);
        }
    }

    // DOM manipulation functions
    function appendResults(results) {
        const fragment = document.createDocumentFragment();
        
        results.forEach(result => {
            const resultElement = createResultElement(result);
            fragment.appendChild(resultElement);
        });
        
        resultsList.appendChild(fragment);
    }

    function createResultElement(result) {
        const clone = resultTemplate.content.cloneNode(true);
        const element = clone.querySelector('.result-item');
        
        // Set basic result info
        const link = element.querySelector('.result-link');
        link.href = result.url;
        link.textContent = result.title || 'No title available';
        
        element.querySelector('.url-text').textContent = result.url;
        element.querySelector('.result-snippet').textContent = result.description || '';
        
        // Add metadata tags
        const urlContainer = element.querySelector('.result-url');
        addMetadataTag(urlContainer, 'domain-tag', result.domain);
        addMetadataTag(urlContainer, 'type-tag', result.type);
        
        // Add keyword visualization if matches exist
        if ((result.text_matches || 0) > 0) {
            setupKeywordVisualization(element, result);
        }
        
        return element;
    }

    function addMetadataTag(container, className, value) {
        if (!value) return;
        
        const tag = document.createElement('span');
        tag.className = className;
        tag.textContent = value;
        container.appendChild(tag);
    }

    // UI state functions
    function toggleLoadMoreButton(loading) {
        if (!loadMoreBtn) return;
        
        loadMoreBtn.disabled = loading;
        
        if (loader) loader.hidden = !loading;
        
        const textSpan = loadMoreBtn.querySelector('span:not(.loader)');
        if (textSpan) {
            textSpan.hidden = loading;
        } else {
            loadMoreBtn.textContent = loading ? 'Loading...' : 'Load More Results';
        }
    }

    function updateLoadMoreButton() {
        if (!loadMoreBtn) return;
        loadMoreBtn.style.display = hasMore ? 'block' : 'none';
    }

    function clearSearchInput() {
        searchInput.value = '';
        searchInput.focus();
    }

    // Utility functions
    function showError(message) {
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        
        const container = loadMoreBtn?.parentNode || resultsList;
        container.insertBefore(errorElement, loadMoreBtn || null);
        
        setTimeout(() => errorElement.remove(), 5000);
    }

    // Keyword visualization functions
    function setupKeywordVisualization(element, result) {
        const matchContainer = element.querySelector('.text-match-container');
        matchContainer.hidden = false;
        
        // Create match count element
        const matchCountDiv = document.createElement('div');
        matchCountDiv.className = 'result-url';
        matchCountDiv.title = 'Text matches';
        
        // Create SVG icon
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '18');
        svg.setAttribute('height', '18');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', '#e24162');
        svg.setAttribute('stroke-width', '2');
        svg.setAttribute('stroke-linecap', 'round');
        svg.setAttribute('stroke-linejoin', 'round');
        
        ['M2 20h20', 'M3 10l3-8 3 8', 'M12 10l3-8 3 8', 'M6 15h12'].forEach(d => {
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', d);
            svg.appendChild(path);
        });
        
        const frequencyBadge = document.createElement('span');
        frequencyBadge.className = 'frequency-badge';
        frequencyBadge.textContent = result.text_matches || 0;
        
        matchCountDiv.append(svg, frequencyBadge);
        
        // Create popup with keyword breakdown
        const popup = document.createElement('div');
        popup.className = 'match-popup';
        
        const header = document.createElement('div');
        header.className = 'match-header';
        
        header.innerHTML = `
            <span>Keyword Breakdown</span>
            <span class="total-count">${result.total_occurrences || 0} total matches</span>
        `;
        
        const frequencyList = document.createElement('div');
        frequencyList.className = 'frequency-list';
        
        // Add keywords to frequency list
        result.keywords?.forEach(keyword => {
            const percentage = result.total_occurrences > 0 ? 
                Math.round((keyword.count / result.total_occurrences * 100) * 10) / 10 : 0;
            
            const item = document.createElement('div');
            item.className = 'frequency-item';
            item.innerHTML = `
                <span class="word">${keyword.keyword}</span>
                <div class="frequency-bar-container">
                    <div class="frequency-bar" style="width: ${percentage}%"></div>
                    <span class="count">${keyword.count} (${keyword.source})</span>
                </div>
            `;
            frequencyList.appendChild(item);
        });
        
        popup.append(header, frequencyList);
        matchContainer.append(matchCountDiv, popup);
    }

    // Initialize frequency bars for all existing results
    function initializeAllFrequencyVisualizations() {
        document.querySelectorAll('.text-match-container').forEach(container => {
            setupPopupHoverEffects(container);
        });
    }

    // Initialize frequency bars only for newly loaded results
    function initializeNewFrequencyVisualizations(numNewResults) {
        const allResults = document.querySelectorAll('.result-item');
        const newResults = Array.from(allResults).slice(-numNewResults);
        
        newResults.forEach(result => {
            const container = result.querySelector('.text-match-container');
            if (container) {
                setupPopupHoverEffects(container);
            }
        });
    }

    // Setup hover effects for a single container
    function setupPopupHoverEffects(container) {
        const icon = container.querySelector('.result-url');
        const popup = container.querySelector('.match-popup');
        
        if (!popup) return;
        
        // Initialize popup state
        popup.style.opacity = '0';
        popup.style.display = 'none';
        
        container.addEventListener('mouseenter', () => {
            // Animate bars
            container.querySelectorAll('.frequency-bar').forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0';
                setTimeout(() => bar.style.width = width, 10);
            });
            
            // Highlight icon
            if (icon) icon.style.transform = 'scale(1.1)';
            
            // Show popup
            popup.style.display = 'block';
            setTimeout(() => popup.style.opacity = '1', 10);
        });
        
        container.addEventListener('mouseleave', () => {
            // Reset icon
            if (icon) icon.style.transform = 'scale(1)';
            
            // Hide popup
            popup.style.opacity = '0';
            setTimeout(() => popup.style.display = 'none', 300);
        });
    }

    // Initialize the application
    init();
});