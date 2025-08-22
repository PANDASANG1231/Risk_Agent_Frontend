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
def load_data():
    try:
        file_path = 'analysis_result.json'
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
def get_key_data(key_name):
    try:
        logger.info(f"Retrieving data for key: {key_name}")
        data = load_data()
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
        logger.info("Received request for /api/data")
        data = load_data()
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
        print("Received request for /api/transactions")
        result, status_code = get_key_data('transactions_data')
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_transactions_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/money-flow')
def get_money_flow_analysis():
    """Get money flow analysis including total inflows, outflows, and net flow"""
    try:
        print("Received request for /api/money-flow")
        result, status_code = get_key_data('money_flow_analysis')
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_money_flow_analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/money-usage')
def get_money_usage_summary():
    """Get detailed money usage summary with flow analysis and descriptions"""
    try:
        print("Received request for /api/money-usage")
        result, status_code = get_key_data('money_usage_summary')
        result['dict_analysis'] = result['flow_analysis']
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_money_usage_summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/high-cash')
def get_high_cash_summary():
    """Get high cash summary analysis"""
    try:
        print("Received request for /api/high-cash")
        result, status_code = get_key_data('high_cash_summary')
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
        logger.info("Received request for /api/business-pattern")
        result, status_code = get_key_data('business_pattern')
        
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
        print("Received request for /api/public-info")
        result, status_code = get_key_data('public_info')
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_public_info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/public-address')
def get_public_address_info():
    """Get public address information and reviews"""
    try:
        print("Received request for /api/public-address")
        result, status_code = get_key_data('public_address_info')
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_public_address_info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/wire-usage')
def get_wire_money_usage():
    """Get wire transfer money usage analysis (bonus endpoint)"""
    try:
        print("Received request for /api/wire-usage")
        result, status_code = get_key_data('wire_money_usage')
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_wire_money_usage: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions_usage_dict')
def get_trans_usage_dict():
    """Get transaction usage dictionary data from JSON, sorted by direction (asc) and amount (desc)"""
    try:
        print("Received request for /api/transactions_usage_dict")
        result, status_code = get_key_data('transactions_usage_dict')
        
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

@app.route('/api/endpoints')
def list_endpoints():
    """List all available API endpoints"""
    endpoints = {
        'available_endpoints': [
            {
                'path': '/api/data',
                'method': 'GET',
                'description': 'Get all data from analysis_result.json'
            },
            {
                'path': '/api/transactions',
                'method': 'GET',
                'description': 'Get transaction data including counts, amounts, and percentages by category and direction'
            },
            {
                'path': '/api/money-flow',
                'method': 'GET',
                'description': 'Get money flow analysis including total inflows, outflows, and net flow'
            },
            {
                'path': '/api/money-usage',
                'method': 'GET',
                'description': 'Get detailed money usage summary with flow analysis and descriptions'
            },
            {
                'path': '/api/high-cash',
                'method': 'GET',
                'description': 'Get high cash summary analysis'
            },
            {
                'path': '/api/business-pattern',
                'method': 'GET',
                'description': 'Get business pattern analysis for industry alignment'
            },
            {
                'path': '/api/public-info',
                'method': 'GET',
                'description': 'Get public information about the company'
            },
            {
                'path': '/api/public-address',
                'method': 'GET',
                'description': 'Get public address information and reviews'
            },
            {
                'path': '/api/wire-usage',
                'method': 'GET',
                'description': 'Get wire transfer money usage analysis (bonus endpoint)'
            },
            {
                'path': '/api/trans_usage_dict',
                'method': 'GET',
                'description': 'Get transaction usage dictionary data from JSON'
            },
            {
                'path': '/api/endpoints',
                'method': 'GET',
                'description': 'List all available API endpoints'
            }
        ],
        'base_url': 'http://localhost:5000',
        'note': 'All endpoints return JSON data. Add ?pretty=true to format JSON output.'
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