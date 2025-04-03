document.addEventListener('DOMContentLoaded', function() {
    // Get search parameters
    const queryInput = document.getElementById('queryInput');
    const currentPageInput = document.getElementById('currentPageInput');
    const loadingText = document.querySelector('.loading-text');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const loadingContent = document.querySelector('.loading-content');
    
    const query = queryInput ? queryInput.value : '';
    const currentPage = currentPageInput ? parseInt(currentPageInput.value) : 1;

    if (!query) {
        window.location.href = '/';
        return;
    }

    // Start the search process
    initiateSearch(query, currentPage);

    async function initiateSearch(query, page) {
        try {
            // Update loading message
            updateLoadingMessage('Starting web scraping...');
            
            // Start backend search task
            const response = await fetch('/run-backend-task', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    query: query,
                    page: page 
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Failed to start search');
            }

            if (data.status === 'success') {
                // Redirect to results page when ready
                window.location.href = data.redirect_url;
            } else {
                throw new Error(data.message || 'Search failed');
            }
        } catch (error) {
            console.error('Search error:', error);
            showError(error.message);
        }
    }

    function updateLoadingMessage(message) {
        if (loadingText) {
            loadingText.textContent = message;
        }
    }

    function showError(errorMessage) {
        // Hide spinner
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
        
        // Show error message
        updateLoadingMessage(`Error: ${errorMessage}`);
        
        // Add retry button
        const retryButton = document.createElement('button');
        retryButton.className = 'retry-button';
        retryButton.textContent = 'Retry Search';
        retryButton.addEventListener('click', () => {
            window.location.href = `/search?q=${encodeURIComponent(query)}&page=${currentPage}`;
        });
        
        if (loadingContent) {
            loadingContent.appendChild(retryButton);
        }
    }

    // Optional: Add progress simulation if search takes too long
    setTimeout(() => {
        updateLoadingMessage('Still working... this might take a moment');
    }, 5000);
});