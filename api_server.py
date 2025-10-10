from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import logging
from datetime import datetime
import re
import pandas as pd

app = Flask(__name__)
CORS(app)
app.json.sort_keys = False  # For Flask 2.2+

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

def replace_hyphens_with_spaces(text):
    """
    Replace hyphens with spaces when the hyphen is surrounded by non-space characters.
    Pattern: a-b becomes a b (where a and b are non-space characters)
    
    Args:
        text (str): Input text to process
        
    Returns:
        str: Text with hyphens replaced by spaces
    """
    if not isinstance(text, str):
        return text
        
    # Use regex to find hyphens surrounded by non-space characters
    # Pattern explanation: (\S) = non-space character, - = hyphen, (\S) = non-space character
    # Replace with: first_group + space + second_group
    processed_text = re.sub(r'(\S)-(\S)', r'\1 \2', text)
    
    logger.debug(f"Hyphen replacement: '{text}' -> '{processed_text}'")
    return processed_text

def remove_markdown_headers(text):
    """
    Remove markdown headers from the beginning of text.
    Pattern: ### Summary of becomes Summary of
    
    Args:
        text (str): Input text to process
        
    Returns:
        str: Text with markdown headers removed
    """
    if not isinstance(text, str):
        return text
        
    # Remove markdown headers like "### " from the beginning
    # Pattern explanation: ^ = start of string, #{1,6} = 1-6 hash symbols, \s+ = one or more spaces
    processed_text = re.sub(r'^#{1,6}\s+', '', text)
    
    logger.debug(f"Markdown header removal: '{text}' -> '{processed_text}'")
    return processed_text

def apply_text_processing(data):
    """
    Apply text processing (including hyphen replacement and markdown header removal) to string values in data structure.
    Recursively processes dictionaries, lists, and strings.
    
    Text processing steps:
    1. Replace hyphens with spaces (a-b → a b)
    2. Remove markdown headers from beginning (### Summary of → Summary of)
    
    Args:
        data: Input data (can be dict, list, str, or other types)
        
    Returns:
        Processed data with same structure
    """
    if isinstance(data, dict):
        return {key: apply_text_processing(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [apply_text_processing(item) for item in data]
    elif isinstance(data, str):
        # Apply text processing functions in sequence
        processed_text = replace_hyphens_with_spaces(data)
        processed_text = remove_markdown_headers(processed_text)
        processed_text = processed_text.strip()
        return processed_text
    else:
        return data

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
        
        if status_code == 200:
            # Apply general text processing (hyphen replacement) to all string values
            logger.info("Applying text processing (hyphen replacement) to business pattern data")
            result = apply_text_processing(result)
            
            if 'raw_analysis' in result:
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
        
        # Apply text processing (hyphen replacement, markdown header removal, and strip) to result
        if status_code == 200:
            logger.info("Applying text processing (hyphen replacement, markdown header removal, and strip) to public info data")
            result = apply_text_processing(result)
            
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
        
        # Apply text processing (hyphen replacement, markdown header removal, and strip) to result
        if status_code == 200:
            logger.info("Applying text processing (hyphen replacement, markdown header removal, and strip) to public address data")
            result = apply_text_processing(result)
            
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_public_address_info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/customer-info')
def get_customer_info():
    """Get customer information and details"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        print(f"Received request for /api/customer-info with acctno: {acctno}")
        result, status_code = get_key_data('customer_info', acctno)
        
        # Apply text processing (hyphen replacement) to result
        if status_code == 200:
            logger.info("Applying text processing (hyphen replacement) to customer info data")
            result = apply_text_processing(result)
            
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_customer_info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/graph')
def get_graph_data():
    """Get network graph data for visualization from analysis result"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
        
        logger.info(f"Received request for /api/graph with acctno: {acctno}")
        
        # Load the analysis data for the specified account
        data = load_data(acctno)
        if not data:
            return jsonify({'error': f'No data found for account {acctno}'}), 404
        
        # Extract the linkage data
        if 'linkage' not in data:
            logger.warning(f"No linkage data found for account {acctno}")
            return jsonify({'error': 'No linkage data available for this account'}), 404
        
        linkage_data = data['linkage']
        logger.info("Linkage data extracted successfully from analysis result")
        
        return jsonify(linkage_data)
        
    except Exception as e:
        logger.error(f"Error in get_graph_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tree')
def get_tree_data():
    """Get tree data for visualization from analysis result"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
        
        logger.info(f"Received request for /api/tree with acctno: {acctno}")
        
        # Load the analysis data for the specified account
        data = load_data(acctno)
        if not data:
            return jsonify({'error': f'No data found for account {acctno}'}), 404
        
        # Extract the linkage data (same source as graph data)
        if 'linkage' not in data:
            logger.warning(f"No linkage data found for account {acctno}")
            return jsonify({'error': 'No linkage data available for this account'}), 404
        
        linkage_data = data['linkage_tree']
        logger.info("Tree data extracted successfully from analysis result")
        
        return jsonify(linkage_data)
        
    except Exception as e:
        logger.error(f"Error in get_tree_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/subgraph')
def get_subgraph_data():
    """Get subgraph data for a specific node at a given degree"""
    try:
        acctno = request.args.get('acctno')
        center_node = request.args.get('center_node', str(acctno).zfill(16))
        degree = request.args.get('degree', '1')  # Default to 1st degree
        
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
        
        if not center_node:
            return jsonify({'error': 'center_node parameter is required'}), 400
            
        try:
            degree = int(degree)
            if degree < 1:
                degree = 1
        except ValueError:
            degree = 1
        
        logger.info(f"Received request for /api/subgraph with acctno: {acctno}, center_node: {center_node}, degree: {degree}")
        
        # Load the full graph data
        data = load_data(acctno)
        if not data:
            return jsonify({'error': f'No data found for account {acctno}'}), 404
        
        if 'linkage' not in data:
            logger.warning(f"No linkage data found for account {acctno}")
            return jsonify({'error': 'No linkage data available for this account'}), 404
        
        linkage_data = data['linkage']
        
        # Extract nodes and links from the full graph
        full_nodes = linkage_data.get('nodes', [])
        full_links = linkage_data.get('links', [])
        
        if not full_nodes or not full_links:
            return jsonify({'error': 'Invalid graph data structure'}), 400
        
        # Find the center node
        center_node_obj = None
        for node in full_nodes:
            if node.get('id') == center_node:
                center_node_obj = node
                break
        
        if not center_node_obj:
            return jsonify({'error': f'Center node {center_node} not found in graph'}), 404
        
        # Calculate subgraph using BFS to specified degree
        subgraph_nodes = {}
        subgraph_links = []
        visited_nodes = set()
        
        # Build adjacency list for efficient traversal
        adjacency = {}
        for link in full_links:
            source_id = link.get('source')
            target_id = link.get('target')
            
            if source_id not in adjacency:
                adjacency[source_id] = []
            if target_id not in adjacency:
                adjacency[target_id] = []
                
            adjacency[source_id].append((target_id, link))
            adjacency[target_id].append((source_id, link))
        
        # BFS to find all nodes within the specified degree
        from collections import deque
        queue = deque([(center_node, 0)])  # (node_id, current_degree)
        visited_nodes.add(center_node)
        
        # Add center node
        subgraph_nodes[center_node] = center_node_obj
        
        while queue:
            current_node, current_degree = queue.popleft()
            
            if current_degree < degree:
                # Explore neighbors
                for neighbor_id, link in adjacency.get(current_node, []):
                    if neighbor_id not in visited_nodes:
                        visited_nodes.add(neighbor_id)
                        queue.append((neighbor_id, current_degree + 1))
                        
                        # Add neighbor node
                        neighbor_node = next((n for n in full_nodes if n.get('id') == neighbor_id), None)
                        if neighbor_node:
                            subgraph_nodes[neighbor_id] = neighbor_node
                    
                    # Add link if both nodes are in subgraph
                    if neighbor_id in subgraph_nodes and link not in subgraph_links:
                        subgraph_links.append(link)
        
        # Convert nodes dict to list
        subgraph_nodes_list = list(subgraph_nodes.values())
        
        # Create the subgraph response
        subgraph_data = {
            'nodes': subgraph_nodes_list,
            'links': subgraph_links,
            'center_node': center_node,
            'degree': degree,
            'total_nodes': len(subgraph_nodes_list),
            'total_links': len(subgraph_links),
            'original_graph_size': {
                'nodes': len(full_nodes),
                'links': len(full_links)
            }
        }
        
        logger.info(f"Subgraph generated: {len(subgraph_nodes_list)} nodes, {len(subgraph_links)} links at degree {degree}")
        
        return jsonify(subgraph_data)
        
    except Exception as e:
        logger.error(f"Error in get_subgraph_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions_usage_detail_dict')
def get_trans_usage_detail_dict():
    """Get transaction usage detail data from transactions_display"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        print(f"Received request for /api/transactions_usage_detail_dict with acctno: {acctno}")
        
        # Get transactions_display data
        transactions_display_result, status_code = get_key_data('transactions_display', acctno)
        if status_code != 200:
            return jsonify({'error': 'Failed to fetch transactions_display data'}), status_code
        
        # Initialize result list
        result = []
        
        # Add transactions_display data
        if isinstance(transactions_display_result, list):
            result.extend(transactions_display_result)
            print(f"Added {len(transactions_display_result)} items from transactions_display")
        
        # Apply text processing (hyphen replacement) to result
        logger.info("Applying text processing (hyphen replacement) to transaction detail data")
        result = apply_text_processing(result)
        
        # Sort the data by direction (ascending) first, then by trans_am (descending)
        if len(result) > 0:
            result = sorted(result, key=lambda x: (
                str(x.get('direction', '')).lower(),  # direction ascending
                -float(x.get('trans_am', 0))  # trans_am descending (negative for reverse sort)
            ))
            print(f"Sorted {len(result)} items by direction (asc) and trans_am (desc)")
            
            # Format trans_am as currency and trans_am_pct as percentage for each item
            for item in result:
                if 'trans_am' in item and item['trans_am'] is not None:
                    try:
                        # Convert to float, round, and format as currency
                        trans_am_value = float(item['trans_am'])
                        rounded_value = round(trans_am_value)
                        # Format as currency with commas
                        formatted_currency = f"${rounded_value:,}"
                        item['trans_am'] = formatted_currency
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not format trans_am value '{item['trans_am']}': {e}")
                        # Keep original value if formatting fails
                        pass
                
                # Format trans_am_pct as percentage with rounded number
                if 'trans_am_pct' in item and item['trans_am_pct'] is not None:
                    try:
                        # Convert to float, multiply by 100, round to whole number, and format as percentage
                        pct_value = float(item['trans_am_pct']) * 100
                        rounded_pct = round(pct_value, 0)
                        # Format as percentage string
                        formatted_percentage = f"{rounded_pct}%"
                        item['trans_am_pct'] = formatted_percentage
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not format trans_am_pct value '{item['trans_am_pct']}': {e}")
                        # Keep original value if formatting fails
                        pass
            
            logger.info("Formatted trans_am values as currency and trans_am_pct values as percentages")

        print(f"Total items: {len(result)} (transactions_display)")
        print(f"Returning {len(result)} transaction detail items")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error in get_trans_usage_detail_dict: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions_usage_dict')
def get_trans_usage_dict():
    """Get transaction usage dictionary data from JSON, sorted by direction (asc) and trans_am (desc), with trans_am formatted as currency"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        print(f"Received request for /api/transactions_usage_dict with acctno: {acctno}")
        result, status_code = get_key_data('transactions_usage_dict', acctno)
        
        if status_code == 200:
            # Apply text processing (hyphen replacement) to result
            logger.info("Applying text processing (hyphen replacement) to transaction usage dict data")
            result = apply_text_processing(result)
            
            # Sort the data if it's a list
            if isinstance(result, list) and len(result) > 0:
                # Sort by direction (ascending) first, then by trans_am (descending)
                result = sorted(result, key=lambda x: (
                    str(x.get('direction', '')).lower(),  # direction ascending
                    -float(x.get('trans_am', 0))  # trans_am descending (negative for reverse sort)
                ))
                print(f"Sorted {len(result)} items by direction (asc) and trans_am (desc)")
                
                # Reorder columns to: category, direction, usage_category, trans_am
                desired_column_order = ['category', 'direction', 'usage_category', 'trans_am']
                
                # Reorder each dictionary to match desired column order
                reordered_result = []
                for item in result:
                    if isinstance(item, dict):
                        # Create new ordered dictionary
                        reordered_item = {}
                        
                        # Add columns in desired order if they exist
                        for column in desired_column_order:
                            if column in item:
                                reordered_item[column] = item[column]
                        
                        # Add any remaining columns not in the desired order
                        for key, value in item.items():
                            if key not in desired_column_order:
                                reordered_item[key] = value
                        
                        reordered_result.append(reordered_item)
                    else:
                        reordered_result.append(item)
                
                result = reordered_result
                print(f"Reordered columns to: {desired_column_order}")
                
                # Format trans_am as currency and trans_am_pct as percentage for each item
                for item in result:
                    if 'trans_am' in item and item['trans_am'] is not None:
                        try:
                            # Convert to float, round, and format as currency
                            trans_am_value = float(item['trans_am'])
                            rounded_value = round(trans_am_value)
                            # Format as currency with commas
                            formatted_currency = f"${rounded_value:,}"
                            item['trans_am'] = formatted_currency
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Could not format trans_am value '{item['trans_am']}': {e}")
                            # Keep original value if formatting fails
                            pass
                    
                    # Format trans_am_pct as percentage with rounded number
                    if 'trans_am_pct' in item and item['trans_am_pct'] is not None:
                        try:
                            # Convert to float, round to 2 decimal places, and format as percentage
                            pct_value = float(item['trans_am_pct']) * 100
                            rounded_pct = round(pct_value, 0)
                            # Format as percentage string
                            formatted_percentage = f"{rounded_pct}%"
                            item['trans_am_pct'] = formatted_percentage
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Could not format trans_am_pct value '{item['trans_am_pct']}': {e}")
                            # Keep original value if formatting fails
                            pass
                
                logger.info("Formatted trans_am values as currency and trans_am_pct values as percentages")
        
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_trans_usage_dict: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_account_numbers(data, key_name):
    """Process account numbers in data to ensure they are 16 digits with zero-padding"""
    try:
        if isinstance(data, list) and len(data) > 0:
            # Look for common account number field names
            account_fields = ['Account Number', 'account_number', 'accountNumber', 'acctno', 'acct_no']
            
            for item in data:
                if isinstance(item, dict):
                    for field in account_fields:
                        if field in item and item[field]:
                            # Convert to string and zero-pad to 16 digits
                            acct_str = str(item[field]).strip()
                            if acct_str.isdigit():
                                item[field] = acct_str.zfill(16)
                                logger.info(f"Zero-padded account number in {key_name}: {acct_str} -> {item[field]}")
                            break
            
            logger.info(f"Successfully processed account numbers in {key_name}")
        return data
    except Exception as e:
        logger.error(f"Error processing account numbers in {key_name}: {str(e)}")
        return data

@app.route('/api/utr-info')
def get_utr_info():
    """Get UTR (Currency Transaction Report) information using pandas for simplified data processing"""
    try:
        acctno = request.args.get('acctno')
        if not acctno:
            return jsonify({'error': 'acctno parameter is required'}), 400
            
        logger.info(f"Received request for /api/utr-info with acctno: {acctno}")

        # Get customer info and validate
        customer_info, customer_status = get_key_data('customer_info', acctno)
        if customer_status != 200:
            return jsonify({'error': 'Failed to retrieve customer information'}), customer_status
            
        target_acct = customer_info.get('frmtd_acct_no', "")
        if not target_acct:
            return jsonify({'error': 'Customer account number not found'}), 404
            
        target_acct = str(target_acct).zfill(16)

        # Get UTR info and validate
        result, status_code = get_key_data('utr_info', acctno)
        if status_code != 200:
            return jsonify({'error': 'Failed to retrieve UTR information'}), status_code
            
        if not result:
            result = [{'Account Number': target_acct, 'UTR Count': '0', 'Target Account': "Y"}]
            return jsonify(result), 200

        # Convert result to pandas DataFrame for easier manipulation
        df = pd.DataFrame(result if isinstance(result, list) else [result])
        
        # Validate DataFrame structure
        required_columns = ['Account Number', 'UTR Count']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'Invalid UTR data structure'}), 500
            
        # Add Target Account column
        utr_col = 'Target Account'
        df[utr_col] = "N"
        
        # Process account numbers
        acct_col = 'Account Number'
        df[acct_col] = df[acct_col].astype(str).str.strip()
        df[acct_col] = df[acct_col].apply(lambda x: x.zfill(16))
        logger.info(f"Zero-padded account numbers in utr_info")
                            
        # Check if target account exists
        target_found = df[acct_col] == target_acct

        if target_found.any():
            # Modify UTR count for target account
            df.loc[target_found, utr_col] = "Y"
            logger.info(f"Modified UTR count for target account {target_acct}")
        else:
            # Add new row for target account if not found
            logger.info(f"Target account {target_acct} not found, adding new row")
            new_row = pd.DataFrame([{
                acct_col: target_acct,
                'UTR Count': '0',
                utr_col: "Y"
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            logger.info(f"Added new row for target account {target_acct}")
                
        # Convert back to list of dictionaries
        result = df.to_dict('records')

        logger.info(f"Successfully processed UTR info for target account {target_acct}")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in get_utr_info: {str(e)}")
        return jsonify({'error': 'Internal server error processing UTR information'}), 500

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
        
        # Sort account numbers based on the last part after splitting by underscore
        accounts.sort(key=lambda x: x.split("_")[-1])
        
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
                'path': '/api/customer-info',
                'method': 'GET',
                'description': 'Get customer information and details',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/graph',
                'method': 'GET',
                'description': 'Get network graph data for visualization',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/tree',
                'method': 'GET',
                'description': 'Get tree data for visualization',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/transactions_usage_dict',
                'method': 'GET',
                'description': 'Get transaction usage dictionary data from JSON, sorted by direction (asc) and trans_am (desc)',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/transactions_usage_detail_dict',
                'method': 'GET',
                'description': 'Get transaction usage detail data from transactions_display',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/utr-info',
                'method': 'GET',
                'description': 'Get UTR (Currency Transaction Report) information',
                'parameters': ['acctno (required)']
            },
            {
                'path': '/api/ctr-info',
                'method': 'GET',
                'description': 'Get CTR (Currency Transaction Report) information',
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