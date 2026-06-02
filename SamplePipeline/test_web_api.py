#!/usr/bin/env python3
"""
Test script to validate Web API response structure before running Fabric pipeline
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class WebAPITester:
    """Test Web API pagination and date range extraction"""
    
    def __init__(self, api_endpoint: str, api_headers: Optional[Dict] = None):
        self.api_endpoint = api_endpoint
        self.api_headers = api_headers or {"Content-Type": "application/json"}
        self.all_responses = []
        self.min_max_dates = []
        
    def extract_min_max_dates(self, response_data: Dict, date_field_path: str) -> Tuple[str, str]:
        """
        Extract min and max dates from response
        
        Args:
            response_data: API response dictionary
            date_field_path: Dot notation path to date field (e.g., 'data.createdDate' or 'items[0].timestamp')
        
        Returns:
            Tuple of (min_date, max_date)
        """
        dates = []
        
        try:
            # Navigate to data array
            if 'data' in response_data:
                data_array = response_data['data'] if isinstance(response_data['data'], list) else [response_data['data']]
            elif 'items' in response_data:
                data_array = response_data['items'] if isinstance(response_data['items'], list) else [response_data['items']]
            else:
                data_array = response_data if isinstance(response_data, list) else [response_data]
            
            # Extract date field from each item
            for item in data_array:
                if isinstance(item, dict):
                    for key in ['createdDate', 'timestamp', 'date', 'created_at', 'created', 'updatedDate']:
                        if key in item:
                            dates.append(item[key])
                            break
            
            if dates:
                dates.sort()
                return dates[0], dates[-1]
            else:
                return None, None
                
        except Exception as e:
            print(f"Error extracting dates: {e}")
            return None, None
    
    def get_next_page_token(self, response_data: Dict) -> Optional[str]:
        """
        Extract next page token from response
        
        Args:
            response_data: API response dictionary
        
        Returns:
            Next page token or None if no more pages
        """
        token_fields = [
            'nextPageToken', 'next_page_token', 'pageToken', 'page_token',
            'token', 'cursor', 'next_cursor', 'offset',
            ('pagination', 'nextToken'), ('pagination', 'token'),
            ('links', 'next')
        ]
        
        for field in token_fields:
            if isinstance(field, tuple):
                if field[0] in response_data and isinstance(response_data[field[0]], dict):
                    if field[1] in response_data[field[0]]:
                        return response_data[field[0]][field[1]]
            else:
                if field in response_data:
                    return response_data[field]
        
        return None
    
    def test_api_pagination(self, 
                           start_date: datetime,
                           end_date: datetime,
                           max_iterations: int = 5) -> Dict:
        """
        Test API pagination and date extraction
        
        Args:
            start_date: Start date for API query
            end_date: End date for API query
            max_iterations: Max number of API calls to make
        
        Returns:
            Dictionary with test results
        """
        results = {
            'total_records': 0,
            'total_responses': 0,
            'date_ranges': [],
            'errors': [],
            'success': True
        }
        
        current_date = start_date
        page_token = None
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            next_date = min(current_date + timedelta(days=7), end_date)
            
            params = {
                'startDate': current_date.isoformat() + 'Z',
                'endDate': next_date.isoformat() + 'Z'
            }
            
            if page_token:
                params['pageToken'] = page_token
            
            try:
                print(f"\n[Iteration {iteration}] Calling API...")
                print(f"  URL: {self.api_endpoint}")
                print(f"  Params: {json.dumps(params, indent=2)}")
                
                response = requests.get(
                    self.api_endpoint,
                    params=params,
                    headers=self.api_headers,
                    timeout=30
                )
                response.raise_for_status()
                
                response_data = response.json()
                self.all_responses.append(response_data)
                
                # Extract data count
                if 'data' in response_data:
                    record_count = len(response_data.get('data', []))
                elif 'items' in response_data:
                    record_count = len(response_data.get('items', []))
                else:
                    record_count = 1
                
                results['total_records'] += record_count
                results['total_responses'] += 1
                
                print(f"  ✓ Status: {response.status_code}")
                print(f"  ✓ Records received: {record_count}")
                
                # Extract dates
                min_date, max_date = self.extract_min_max_dates(response_data, 'data[*].createdDate')
                if min_date:
                    results['date_ranges'].append({
                        'iteration': iteration,
                        'min_date': min_date,
                        'max_date': max_date,
                        'record_count': record_count
                    })
                    print(f"  ✓ Date range: {min_date} to {max_date}")
                
                # Check for next page
                page_token = self.get_next_page_token(response_data)
                print(f"  ✓ Next page token: {page_token if page_token else 'None (end of data)'}")
                
                if not page_token or record_count == 0:
                    print(f"\n[Iteration {iteration}] No more data available. Stopping.")
                    break
                    
            except requests.RequestException as e:
                error_msg = f"API Error on iteration {iteration}: {str(e)}"
                print(f"  ✗ {error_msg}")
                results['errors'].append(error_msg)
                results['success'] = False
                break
            except json.JSONDecodeError as e:
                error_msg = f"JSON decode error on iteration {iteration}: {str(e)}"
                print(f"  ✗ {error_msg}")
                results['errors'].append(error_msg)
                results['success'] = False
                break
            except Exception as e:
                error_msg = f"Unexpected error on iteration {iteration}: {str(e)}"
                print(f"  ✗ {error_msg}")
                results['errors'].append(error_msg)
                results['success'] = False
                break
        
        return results
    
    def save_test_results(self, results: Dict, filename: str = 'api_test_results.json'):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {filename}")
    
    def validate_for_pipeline(self) -> Dict:
        """Validate responses are compatible with pipeline"""
        validation = {
            'has_data': False,
            'has_dates': False,
            'has_pagination': False,
            'recommendations': []
        }
        
        if not self.all_responses:
            validation['recommendations'].append("No API responses to validate")
            return validation
        
        first_response = self.all_responses[0]
        
        # Check for data
        if 'data' in first_response or 'items' in first_response or isinstance(first_response, list):
            validation['has_data'] = True
        else:
            validation['recommendations'].append("Could not find data array in response")
        
        # Check for dates
        min_date, max_date = self.extract_min_max_dates(first_response, '')
        if min_date:
            validation['has_dates'] = True
        else:
            validation['recommendations'].append("Could not extract dates from response")
        
        # Check for pagination
        if len(self.all_responses) > 1:
            validation['has_pagination'] = True
        else:
            token = self.get_next_page_token(first_response)
            if token:
                validation['has_pagination'] = True
                validation['recommendations'].append(f"Pagination token present: {token}")
            else:
                validation['recommendations'].append("No pagination detected - API may return single page only")
        
        return validation


def main():
    """Example usage"""
    
    # Configuration
    API_ENDPOINT = "https://api.github.com/repos/microsoft/fabric/commits"
    
    # Example: GitHub API
    headers = {
        'Accept': 'application/vnd.github.v3+json'
    }
    
    tester = WebAPITester(API_ENDPOINT, headers)
    
    # Test the API
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    print("=" * 60)
    print("Web API Pagination Test")
    print("=" * 60)
    
    results = tester.test_api_pagination(start_date, end_date, max_iterations=5)
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Total Responses: {results['total_responses']}")
    print(f"Total Records: {results['total_records']}")
    print(f"Date Ranges Found: {len(results['date_ranges'])}")
    print(f"Errors: {len(results['errors'])}")
    print(f"Success: {results['success']}")
    
    if results['errors']:
        print("\nErrors encountered:")
        for error in results['errors']:
            print(f"  - {error}")
    
    # Validate for pipeline
    print("\n" + "=" * 60)
    print("Pipeline Compatibility Check")
    print("=" * 60)
    validation = tester.validate_for_pipeline()
    print(f"Has Data: {validation['has_data']}")
    print(f"Has Dates: {validation['has_dates']}")
    print(f"Has Pagination: {validation['has_pagination']}")
    
    if validation['recommendations']:
        print("\nRecommendations:")
        for rec in validation['recommendations']:
            print(f"  - {rec}")
    
    # Save results
    tester.save_test_results(results)


if __name__ == "__main__":
    main()
