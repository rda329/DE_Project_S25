from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from run_search import run_search, get_results
import math
import time
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'de_project'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Using timedelta for better readability

# Configuration constants
RESULTS_PER_ENGINE = 250
NUM_ENGINES = 4
RESULTS_PER_PAGE = 5

@app.before_request
def refresh_session():
    """Refresh session lifetime on each request"""
    session.permanent = True

@app.route('/')
def home():
    session.pop('search_data', None)
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    """Handle search requests and redirect to loading screen"""
    query = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return redirect(url_for('home'))
    
    # Clear previous search data
    session.pop('search_data', None)
    
    # Store basic search info in session
    session['pending_search'] = {
        'query': query,
        'page': page,
        'started_at': time.time()
    }
    
    return render_template('loading_screen.html',
                         query=query,
                         current_page=page)

@app.route('/run-backend-task', methods=['POST'])
def run_backend_task():
    """Endpoint that performs the actual search/scraping"""
    data = request.get_json()
    query = data.get('query')
    page = data.get('page', 1)
    
    if not query or 'pending_search' not in session:
        return jsonify({'status': 'error', 'message': 'Invalid search request'}), 400
    
    try:
        # Run search with RESULTS_PER_ENGINE from each of NUM_ENGINES
        scrape_time, _ = run_search(query, RESULTS_PER_ENGINE)
        
        # Get first page of ranked results
        first_page_results, total_pages, _ = get_results(query, 1)
        
        # Store results in session
        session['search_data'] = {
            'all_results': first_page_results,
            'result_count': len(first_page_results),
            'time_scrape': scrape_time,
            'query': query,
            'total_pages': total_pages,
            'current_page': 1
        }
        
        # Clear pending search
        session.pop('pending_search', None)
        
        return jsonify({
            'status': 'success',
            'redirect_url': url_for('show_results', q=query),
            'scrape_time': scrape_time
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Search failed: {str(e)}"
        }), 500

@app.route('/results')
def show_results():
    query = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return redirect(url_for('home'))
    
    try:
        page_results, total_pages, has_more = get_results(query, page)
        
        return render_template('search-results.html',
                            results=page_results,
                            query=query,
                            result_count=len(page_results) * total_pages,  # Estimate total count
                            time_scrape=session.get('search_data', {}).get('scrape_time', 0),
                            current_page=page,
                            total_pages=total_pages)
    except Exception as e:
        return redirect(url_for('home'))

@app.route('/load-more', methods=['GET'])
def load_more():
    query = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return jsonify({'status': 'error', 'message': 'Missing query parameter'}), 400
    
    try:
        page_results, total_pages, has_more = get_results(query, page)
        
        return jsonify({
            'status': 'success',
            'results': page_results,
            'current_page': page,
            'has_more': has_more,
            'total_pages': total_pages
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Failed to load results: {str(e)}"
        }), 500

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('home'))

@app.errorhandler(500)
def internal_server_error(e):
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)