from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load data from JSON file
def load_data(acctno):
    try:
        file_path = os.path.join('cache_data', f'analysis_result_{acctno}.json')
        logger.info(f"Attempting to load data from {os.path.abspath(file_path)}")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            logger.info("Data loaded successfully")
            return data
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise

# Helper function to get specific data with error handling
def get_key_data(key_name, acctno):
    try:
        logger.info(f"Retrieving data for key: {key_name}")
        data = load_data(acctno)
        if key_name not in data:
            logger.warning(f'Key "{key_name}" not found in data')
            return {'error': f'Key "{key_name}" not found in data'}, 404
        logger.info(f"Successfully retrieved data for key: {key_name}")
        return data[key_name], 200
    except Exception as e:
        logger.error(f'Error loading data for key "{key_name}": {str(e)}')
        return {'error': f'Error loading data: {str(e)}'}, 500

@app.route('/api/data')
def get_data():
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        logger.info(f"Received request for /api/data with acctno: {acctno}")
        data = load_data(acctno)
        logger.info("Sending response for /api/data")
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error in get_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Focused API endpoints for specific keys
@app.route('/api/transactions')
def get_transactions_data():
    """Get transaction data including counts, amounts, and percentages by category and direction"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        print(f"Received request for /api/transactions with acctno: {acctno}")
        result, status_code = get_key_data('transactions_data', acctno)
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_transactions_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/money-flow')
def get_money_flow_analysis():
    """Get money flow analysis including total inflows, outflows, and net flow"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        print(f"Received request for /api/money-flow with acctno: {acctno}")
        result, status_code = get_key_data('money_flow_analysis', acctno)
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_money_flow_analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/money-usage')
def get_money_usage_summary():
    """Get detailed money usage summary with flow analysis and descriptions"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        print(f"Received request for /api/money-usage with acctno: {acctno}")
        result, status_code = get_key_data('money_usage_summary', acctno)
        result['dict_analysis'] = result['flow_analysis']
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_money_usage_summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/high-cash')
def get_high_cash_summary():
    """Get high cash summary analysis"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        print(f"Received request for /api/high-cash with acctno: {acctno}")
        result, status_code = get_key_data('high_cash_summary', acctno)
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_high_cash_summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_business_pattern_text(text):
    """Process business pattern text with XML parsing and formatting"""
    original_text = text
    logger.info("Starting business pattern text processing")
    
    # First try except: Extract XML-like patterns and process them
    try:
        import re
        
        # Find all XML-like patterns <a>content</a>
        xml_pattern = r'<([^>]+)>(.*?)</\1>'
        matches = re.findall(xml_pattern, text, re.DOTALL | re.IGNORECASE)
        logger.info(f"Found {len(matches)} XML matches: {[match[0] for match in matches]}")

        for i, (key, content) in enumerate(matches):
            logger.debug(f"Match {i+1}: Key='{key}', Content length={len(content)}")
        
        if not matches:
            logger.info("No XML matches found, returning original text")
            return original_text
        
        processed_sections = {}
        
        # Process each match except the last one
        for i, (key, content) in enumerate(matches):
            if i < len(matches) - 1:  # Not the last one
                logger.info(f"Processing non-last key: {key}")
                # Second try except: Process content with dashes and bold formatting
                try:
                    processed_content = content
                    original_length = len(processed_content)
                    
                    # If "-" in text, split by "-" (but keep the structure)
                    if "-" in processed_content:
                        logger.debug(f"Processing dashes in {key}")
                        parts = processed_content.split("-")
                        processed_content = "/n".join(part.strip() for part in parts if part.strip())
                    
                    # Handle **b** patterns (split by ** but maintain format)
                    bold_pattern = r'\*\*([^*]+)\*\*'
                    if re.search(bold_pattern, processed_content):
                        logger.debug(f"Processing bold patterns in {key}")
                        # Keep the **text** format intact
                        processed_content = re.sub(bold_pattern, r'**\1**', processed_content)
                    
                    processed_sections[key] = processed_content
                    logger.info(f"Successfully processed {key} (length: {original_length} -> {len(processed_content)})")
                    
                except Exception as e:
                    logger.error(f"Second try-except failed for key {key}: {e}")
                    processed_sections[key] = content

                    
            else:  # Last key
                logger.info(f"Processing last key: {key}")
                # Last try except: Remove all '/n'
                try:
                    original_length = len(content)
                    processed_content = content.replace('/n', '').replace('\\n', '')
                    processed_sections[key] = processed_content
                    logger.info(f"Successfully processed last key {key} (length: {original_length} -> {len(processed_content)})")
                except Exception as e:
                    logger.error(f"Last try-except failed for key {key}: {e}")
                    processed_sections[key] = content


        
        logger.info("Business pattern text processing completed successfully")
        return processed_sections
        
    except Exception as e:
        logger.error(f"First try-except failed: {e}")
        logger.info("Returning original text due to processing failure")
        return original_text

@app.route('/api/business-pattern')
def get_business_pattern():
    """Get business pattern analysis for industry alignment"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        logger.info(f"Received request for /api/business-pattern with acctno: {acctno}")
        result, status_code = get_key_data('business_pattern', acctno)
        
        if status_code == 200 and 'raw_analysis' in result:
            logger.info("Processing raw_analysis text for business pattern")
            processed_text = process_business_pattern_text(result['raw_analysis'])
            result['dict_analysis'] = processed_text
            logger.info("Business pattern text processing completed")
        
        logger.info("Sending business pattern response")
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error in get_business_pattern: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/public-info')
def get_public_info():
    """Get public information about the company"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        print(f"Received request for /api/public-info with acctno: {acctno}")
        result, status_code = get_key_data('public_info', acctno)
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_public_info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/public-address')
def get_public_address_info():
    """Get public address information and reviews"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        print(f"Received request for /api/public-address with acctno: {acctno}")
        result, status_code = get_key_data('public_address_info', acctno)
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_public_address_info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/wire-usage')
def get_wire_money_usage():
    """Get wire transfer money usage analysis (bonus endpoint)"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        print(f"Received request for /api/wire-usage with acctno: {acctno}")
        result, status_code = get_key_data('wire_money_usage', acctno)
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_wire_money_usage: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions_usage_dict')
def get_trans_usage_dict():
    """Get transaction usage dictionary data from JSON, sorted by direction (asc) and amount (desc)"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        print(f"Received request for /api/transactions_usage_dict with acctno: {acctno}")
        result, status_code = get_key_data('transactions_usage_dict', acctno)
        
        # Sort the data if it's a list
        if isinstance(result, list) and len(result) > 0:
            # Sort by direction (ascending) first, then by amount (descending)
            result = sorted(result, key=lambda x: (
                str(x.get('direction', '')).lower(),  # direction ascending
                -float(x.get('amount', 0))  # amount descending (negative for reverse sort)
            ))
            print(f"Sorted {len(result)} items by direction (asc) and amount (desc)")
        
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_trans_usage_dict: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts')
def list_accounts():
    """List all available account numbers from cache_data folder"""
    try:
        logger.info("Received request for /api/accounts")
        
        if not os.path.exists('cache_data'):
            logger.warning("cache_data folder not found")
            return jsonify({'accounts': [], 'message': 'No cache_data folder found'}), 200
        
        # Get all JSON files in cache_data folder
        json_files = [f for f in os.listdir('cache_data') if f.endswith('.json')]
        
        # Extract account numbers from filenames
        accounts = []
        for filename in json_files:
            if filename.startswith('analysis_result_') and filename.endswith('.json'):
                acctno = filename.replace('analysis_result_', '').replace('.json', '')
                accounts.append(acctno)
        
        # Sort account numbers for consistent output
        accounts.sort()
        
        logger.info(f"Found {len(accounts)} accounts: {accounts}")
        return jsonify({
            'accounts': accounts,
            'total_count': len(accounts),
            'message': f'Found {len(accounts)} account(s) with analysis data'
        })
        
    except Exception as e:
        logger.error(f"Error in list_accounts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/endpoints')
def list_endpoints():
    """List all available API endpoints"""
    endpoints = {
        'available_endpoints': [
            {
                'path': '/api/accounts',
                'method': 'GET',
                'description': 'List all available account numbers from cache_data folder',
                'parameters': []
            },
            {
                'path': '/api/data',
                'method': 'GET',
                'description': 'Get all data from cache_data/analysis_result_{acctno}.json',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/transactions',
                'method': 'GET',
                'description': 'Get transaction data including counts, amounts, and percentages by category and direction',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/money-flow',
                'method': 'GET',
                'description': 'Get money flow analysis including total inflows, outflows, and net flow',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/money-usage',
                'method': 'GET',
                'description': 'Get detailed money usage summary with flow analysis and descriptions',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/high-cash',
                'method': 'GET',
                'description': 'Get high cash summary analysis',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/business-pattern',
                'method': 'GET',
                'description': 'Get business pattern analysis for industry alignment',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/public-info',
                'method': 'GET',
                'description': 'Get public information about the company',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/public-address',
                'method': 'GET',
                'description': 'Get public address information and reviews',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/wire-usage',
                'method': 'GET',
                'description': 'Get wire transfer money usage analysis (bonus endpoint)',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/trans_usage_dict',
                'method': 'GET',
                'description': 'Get transaction usage dictionary data from JSON',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/endpoints',
                'method': 'GET',
                'description': 'List all available API endpoints'
            }
        ],
        'base_url': 'http://localhost:5000',
        'note': 'All endpoints (except /api/endpoints and /api/accounts) require acctno parameter. Example: /api/data?acctno=12345'
    }
    return jsonify(endpoints)

@app.route('/')
def serve_app():
    try:
        logger.info("Received request for index.html")
        with open('index.html', 'r', encoding='utf-8') as file:
            content = file.read()
            logger.info("index.html loaded successfully")
            return content
    except Exception as e:
        logger.error(f"Error serving app: {str(e)}")
        return str(e), 500

# Add request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.url} from {request.remote_addr}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status_code} for {request.method} {request.url}")
    return response

if __name__ == '__main__':
    logger.info("Starting Flask Risk Agent API Server...")
    logger.info("Server configuration: Debug=True, Port=5000")
    logger.info("Log file: api_server.log")
    app.run(debug=True, port=5000)