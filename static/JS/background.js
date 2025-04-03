// Create the background container when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Create container for background elements
    const backgroundContainer = document.createElement('div');
    backgroundContainer.classList.add('background-elements');
    document.body.appendChild(backgroundContainer);
    
    // Create pulse element
    const pulse = document.createElement('div');
    pulse.classList.add('pulse');
    document.body.appendChild(pulse);
    
    // Define search terms
    const searchTerms = ['Knowledge', 'Discover', 'Research', 'Find', 'Search', 'Explore', 'Learn', 'Investigate'];
    
    // Create floating elements
    const numMagnifiers = 15;
    
    for (let i = 0; i < numMagnifiers; i++) {
      createMagnifier(backgroundContainer);
      createSearchTerm(backgroundContainer, searchTerms);
    }
  });
  
  function createMagnifier(container) {
    const magnifier = document.createElement('div');
    magnifier.classList.add('magnifier');
    
    // Random position
    const xPos = Math.random() * 100;
    const yPos = Math.random() * 100;
    
    // Random size
    const size = 20 + Math.random() * 30;
    
    // Random animation delay
    const delay = Math.random() * 5;
    
    magnifier.style.left = `${xPos}%`;
    magnifier.style.top = `${yPos}%`;
    magnifier.style.width = `${size}px`;
    magnifier.style.height = `${size}px`;
    magnifier.style.animationDelay = `${delay}s`;
    
    container.appendChild(magnifier);
  }
  
  function createSearchTerm(container, terms) {
    const term = document.createElement('div');
    term.classList.add('search-term');
    
    // Random position
    const xPos = Math.random() * 100;
    const yPos = Math.random() * 100;
    
    // Random term
    const randomTerm = terms[Math.floor(Math.random() * terms.length)];
    term.textContent = randomTerm;
    
    // Random animation delay
    const delay = Math.random() * 5;
    
    term.style.left = `${xPos}%`;
    term.style.top = `${yPos}%`;
    term.style.animationDelay = `${delay}s`;
    
    container.appendChild(term);
  }