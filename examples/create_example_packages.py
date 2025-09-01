# examples/create_example_packages.py - Create demo packages
"""
Create example .pkg files for demonstration
"""

import json
import zipfile
import hashlib
import time
from pathlib import Path

def create_webscraper_package():
    """Create webscraper.pkg example"""
    
    webscraper_code = '''
import urllib.request
import urllib.error
import urllib.parse
import json
import re
import time
from html.parser import HTMLParser

class WebScraperHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = []
        self.current_tag = None
        self.current_attrs = {}
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_attrs = dict(attrs)
        
    def handle_data(self, data):
        if self.current_tag and data.strip():
            self.data.append({
                "tag": self.current_tag,
                "content": data.strip(),
                "attrs": self.current_attrs
            })
    
    def get_links(self):
        """Extract all links from parsed data"""
        links = []
        for item in self.data:
            if item["tag"] == "a" and "href" in item["attrs"]:
                links.append({
                    "url": item["attrs"]["href"],
                    "text": item["content"]
                })
        return links
    
    def get_text_by_tag(self, tag_name):
        """Get all text from specific tags"""
        return [item["content"] for item in self.data if item["tag"] == tag_name]

def scrape_url(url, timeout=10, user_agent=None):
    """
    Scrape content from a URL
    
    Args:
        url (str): URL to scrape
        timeout (int): Request timeout in seconds
        user_agent (str): Custom user agent
    
    Returns:
        dict: Scraped content and metadata
    """
    try:
        headers = {
            "User-Agent": user_agent or "PKG-System-WebScraper/1.0 (+https://github.com/pkg-system)"
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as response:
            html = response.read().decode('utf-8', errors='ignore')
            response_time = time.time() - start_time
            
        # Parse HTML
        parser = WebScraperHTMLParser()
        parser.feed(html)
        
        # Extract basic metadata
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "No title found"
        
        meta_desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        description = meta_desc_match.group(1) if meta_desc_match else ""
        
        return {
            "url": url,
            "status": "success",
            "title": title,
            "description": description,
            "content": parser.data[:100],  # Limit to first 100 elements
            "links": parser.get_links()[:50],  # Limit to first 50 links
            "total_elements": len(parser.data),
            "total_links": len(parser.get_links()),
            "size": len(html),
            "response_time": response_time,
            "scraped_at": time.time()
        }
        
    except urllib.error.URLError as e:
        return {
            "url": url,
            "status": "error",
            "error": f"URL Error: {str(e)}",
            "scraped_at": time.time()
        }
    except Exception as e:
        return {
            "url": url,
            "status": "error", 
            "error": f"Unexpected error: {str(e)}",
            "scraped_at": time.time()
        }

def extract_links(url, timeout=10):
    """
    Extract all links from a webpage
    
    Args:
        url (str): URL to extract links from
        timeout (int): Request timeout
    
    Returns:
        dict: List of links and metadata
    """
    try:
        headers = {"User-Agent": "PKG-System-LinkExtractor/1.0"}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        # Extract links with regex (simple approach)
        link_pattern = r'<a[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>([^<]*)</a>'
        matches = re.findall(link_pattern, html, re.IGNORECASE)
        
        links = []
        for url_match, text_match in matches:
            links.append({
                "url": url_match,
                "text": text_match.strip() or url_match,
                "domain": urllib.parse.urlparse(url_match).netloc
            })
        
        # Remove duplicates
        unique_links = []
        seen_urls = set()
        for link in links:
            if link["url"] not in seen_urls:
                unique_links.append(link)
                seen_urls.add(link["url"])
        
        return {
            "source_url": url,
            "status": "success",
            "links": unique_links[:100],  # Limit results
            "total_links": len(unique_links),
            "unique_domains": len(set(link["domain"] for link in unique_links)),
            "extracted_at": time.time()
        }
        
    except Exception as e:
        return {
            "source_url": url,
            "status": "error",
            "error": str(e),
            "extracted_at": time.time()
        }

def get_page_info(url, timeout=10):
    """
    Get basic information about a webpage
    
    Args:
        url (str): URL to analyze
        timeout (int): Request timeout
    
    Returns:
        dict: Page information and metadata
    """
    try:
        headers = {"User-Agent": "PKG-System-PageInfo/1.0"}
        req = urllib.request.Request(url, headers=headers)
        
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as response:
            html = response.read().decode('utf-8', errors='ignore')
            response_time = time.time() - start_time
            content_type = response.headers.get('content-type', 'unknown')
            status_code = response.status
        
        # Extract metadata
        title = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        title = title.group(1).strip() if title else "No title"
        
        # Count elements
        element_counts = {}
        for tag in ['div', 'p', 'a', 'img', 'h1', 'h2', 'h3', 'script', 'style']:
            count = len(re.findall(f'<{tag}[^>]*>', html, re.IGNORECASE))
            if count > 0:
                element_counts[tag] = count
        
        return {
            "url": url,
            "status": "success",
            "title": title,
            "content_type": content_type,
            "status_code": status_code,
            "size": len(html),
            "response_time": response_time,
            "element_counts": element_counts,
            "has_javascript": 'script' in element_counts,
            "has_css": 'style' in element_counts,
            "analyzed_at": time.time()
        }
        
    except Exception as e:
        return {
            "url": url,
            "status": "error",
            "error": str(e),
            "analyzed_at": time.time()
        }

def scrape_multiple(urls, timeout=10, delay=1):
    """
    Scrape multiple URLs with rate limiting
    
    Args:
        urls (list): List of URLs to scrape
        timeout (int): Request timeout per URL
        delay (int): Delay between requests in seconds
    
    Returns:
        dict: Results for all URLs
    """
    results = []
    
    for i, url in enumerate(urls):
        print(f"Scraping {i+1}/{len(urls)}: {url}")
        
        result = scrape_url(url, timeout)
        results.append(result)
        
        # Rate limiting
        if delay > 0 and i < len(urls) - 1:
            time.sleep(delay)
    
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful
    
    return {
        "total_urls": len(urls),
        "successful": successful,
        "failed": failed,
        "success_rate": (successful / len(urls)) * 100,
        "results": results,
        "completed_at": time.time()
    }

# Export public functions
__all__ = [
    "scrape_url", 
    "extract_links", 
    "get_page_info", 
    "scrape_multiple"
]
'''

    # Create manifest
    manifest = {
        "name": "webscraper",
        "version": "1.0.0",
        "provider": "tryboy869",
        "description": "Simple web scraping tools for the PKG System",
        "author": "PKG System Demo",
        "entry_point": "webscraper.py",
        "exports": ["scrape_url", "extract_links", "get_page_info", "scrape_multiple"],
        "dependencies": [],
        "python_version": ">=3.6",
        "created": time.time(),
        "security_hash": hashlib.sha256(webscraper_code.encode()).hexdigest()
    }
    
    # Create .pkg file
    output_dir = Path("examples")
    output_dir.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(output_dir / "webscraper.pkg", 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        zf.writestr("webscraper.py", webscraper_code)
    
    print("✓ Created webscraper.pkg")
    return output_dir / "webscraper.pkg"

def create_data_tools_package():
    """Create data_tools.pkg example"""
    
    data_tools_code = '''
import json
import csv
import io
import time
import hashlib
from collections import Counter, defaultdict
from typing import Any, Dict, List, Union

def analyze_data(data: Any) -> Dict[str, Any]:
    """
    Analyze data structure and provide insights
    
    Args:
        data: Any Python data structure
    
    Returns:
        dict: Analysis results
    """
    if data is None:
        return {"type": "NoneType", "value": None, "analysis": "Empty data"}
    
    analysis = {
        "type": type(data).__name__,
        "analyzed_at": time.time()
    }
    
    if isinstance(data, dict):
        analysis.update({
            "size": len(data),
            "keys": list(data.keys())[:20],  # First 20 keys
            "total_keys": len(data),
            "nested_dicts": sum(1 for v in data.values() if isinstance(v, dict)),
            "nested_lists": sum(1 for v in data.values() if isinstance(v, list)),
            "value_types": dict(Counter(type(v).__name__ for v in data.values())),
            "max_nesting_level": _get_dict_nesting_level(data)
        })
    elif isinstance(data, (list, tuple)):
        analysis.update({
            "length": len(data),
            "item_types": dict(Counter(type(item).__name__ for item in data)),
            "sample": data[:10] if len(data) <= 10 else data[:5] + ["..."] + data[-5:],
            "is_homogeneous": len(set(type(item).__name__ for item in data)) == 1,
            "has_nested_structures": any(isinstance(item, (dict, list, tuple)) for item in data)
        })
    elif isinstance(data, str):
        lines = data.split('\\n')
        words = data.split()
        analysis.update({
            "length": len(data),
            "word_count": len(words),
            "line_count": len(lines),
            "character_distribution": dict(Counter(data.lower())[:10]),  # Top 10 chars
            "starts_with": data[:50] + "..." if len(data) > 50 else data,
            "appears_to_be_json": _is_json_like(data),
            "appears_to_be_csv": ',' in data and '\\n' in data
        })
    elif isinstance(data, (int, float)):
        analysis.update({
            "value": data,
            "is_positive": data > 0,
            "is_zero": data == 0,
            "absolute_value": abs(data)
        })
    else:
        analysis["value"] = str(data)[:100]
    
    return analysis

def _get_dict_nesting_level(d: dict, level: int = 1) -> int:
    """Calculate maximum nesting level in a dictionary"""
    if not isinstance(d, dict):
        return level - 1
    
    max_level = level
    for value in d.values():
        if isinstance(value, dict):
            max_level = max(max_level, _get_dict_nesting_level(value, level + 1))
    
    return max_level

def _is_json_like(text: str) -> bool:
    """Check if string looks like JSON"""
    text = text.strip()
    try:
        json.loads(text)
        return True
    except:
        return (text.startswith('{') and text.endswith('}')) or (text.startswith('[') and text.endswith(']'))

def parse_csv_string(csv_string: str, delimiter: str = ',') -> Dict[str, Any]:
    """
    Parse CSV string into structured data
    
    Args:
        csv_string: CSV data as string
        delimiter: CSV delimiter
    
    Returns:
        dict: Parsed data with metadata
    """
    try:
        # Detect delimiter if not specified
        if delimiter == ',':
            sample = csv_string[:1000]
            if sample.count(';') > sample.count(','):
                delimiter = ';'
            elif sample.count('\\t') > sample.count(','):
                delimiter = '\\t'
        
        reader = csv.DictReader(io.StringIO(csv_string), delimiter=delimiter)
        rows = list(reader)
        
        if not rows:
            return {
                "status": "error",
                "error": "No data rows found",
                "csv_string_preview": csv_string[:200]
            }
        
        # Analyze columns
        columns = list(rows[0].keys())
        column_analysis = {}
        
        for col in columns:
            values = [row[col] for row in rows if row[col]]
            
            # Try to detect data types
            numeric_count = sum(1 for v in values if _is_numeric(v))
            date_count = sum(1 for v in values if _looks_like_date(v))
            
            column_analysis[col] = {
                "total_values": len(values),
                "empty_values": len(rows) - len(values),
                "unique_values": len(set(values)),
                "sample_values": values[:5],
                "likely_numeric": numeric_count > len(values) * 0.8,
                "likely_date": date_count > len(values) * 0.8
            }
        
        return {
            "status": "success",
            "rows": len(rows),
            "columns": columns,
            "column_count": len(columns),
            "data": rows[:10],  # Sample rows
            "column_analysis": column_analysis,
            "delimiter_used": delimiter,
            "parsed_at": time.time()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "csv_preview": csv_string[:200],
            "attempted_delimiter": delimiter
        }

def _is_numeric(value: str) -> bool:
    """Check if string represents a number"""
    try:
        float(value)
        return True
    except ValueError:
        return False

def _looks_like_date(value: str) -> bool:
    """Check if string looks like a date"""
    date_patterns = ['-', '/', '.', ' ']
    return any(pattern in value for pattern in date_patterns) and any(char.isdigit() for char in value)

def filter_data(data: Union[List, Dict], condition_func) -> Union[List, Dict]:
    """
    Filter data based on condition function
    
    Args:
        data: Data to filter
        condition_func: Function that returns True for items to keep
    
    Returns:
        Filtered data
    """
    try:
        if isinstance(data, list):
            return [item for item in data if condition_func(item)]
        elif isinstance(data, dict):
            return {k: v for k, v in data.items() if condition_func(v)}
        else:
            return data
    except Exception as e:
        return {"error": f"Filter failed: {e}", "original_data": str(data)[:100]}

def group_data(data: List[Dict], key_func) -> Dict[str, Any]:
    """
    Group list of dictionaries by key function
    
    Args:
        data: List of dictionaries
        key_func: Function to extract grouping key
    
    Returns:
        dict: Grouped data with metadata
    """
    if not isinstance(data, list):
        return {"error": "Data must be a list", "received_type": type(data).__name__}
    
    try:
        groups = defaultdict(list)
        for item in data:
            key = str(key_func(item))  # Convert to string for JSON compatibility
            groups[key].append(item)
        
        result_groups = dict(groups)
        
        # Add metadata
        group_sizes = {k: len(v) for k, v in result_groups.items()}
        largest_group = max(group_sizes.values()) if group_sizes else 0
        smallest_group = min(group_sizes.values()) if group_sizes else 0
        
        return {
            "groups": result_groups,
            "group_count": len(result_groups),
            "total_items": len(data),
            "group_sizes": group_sizes,
            "largest_group_size": largest_group,
            "smallest_group_size": smallest_group,
            "average_group_size": len(data) / len(result_groups) if result_groups else 0,
            "grouped_at": time.time()
        }
        
    except Exception as e:
        return {
            "error": f"Grouping failed: {e}",
            "data_sample": str(data[:3]) if data else "empty"
        }

def summary_stats(data: List[Union[int, float]]) -> Dict[str, Any]:
    """
    Calculate summary statistics for numeric data
    
    Args:
        data: List of numeric values
    
    Returns:
        dict: Statistical summary
    """
    if not isinstance(data, list):
        return {"error": "Data must be a list", "received_type": type(data).__name__}
    
    # Extract numeric values
    numeric_data = []
    for item in data:
        if isinstance(item, (int, float)):
            numeric_data.append(item)
        elif isinstance(item, str) and _is_numeric(item):
            try:
                numeric_data.append(float(item))
            except ValueError:
                continue
    
    if not numeric_data:
        return {
            "error": "No numeric data found",
            "original_count": len(data),
            "sample": str(data[:5]) if data else "empty"
        }
    
    # Calculate statistics
    sorted_data = sorted(numeric_data)
    n = len(numeric_data)
    
    # Basic stats
    total = sum(numeric_data)
    mean = total / n
    
    # Median
    if n % 2 == 0:
        median = (sorted_data[n//2 - 1] + sorted_data[n//2]) / 2
    else:
        median = sorted_data[n//2]
    
    # Variance and standard deviation
    variance = sum((x - mean) ** 2 for x in numeric_data) / n
    std_dev = variance ** 0.5
    
    # Quartiles
    q1_idx = n // 4
    q3_idx = 3 * n // 4
    q1 = sorted_data[q1_idx] if q1_idx < n else sorted_data[-1]
    q3 = sorted_data[q3_idx] if q3_idx < n else sorted_data[-1]
    
    return {
        "count": n,
        "min": min(numeric_data),
        "max": max(numeric_data),
        "sum": total,
        "mean": mean,
        "median": median,
        "std_dev": std_dev,
        "variance": variance,
        "q1": q1,
        "q3": q3,
        "range": max(numeric_data) - min(numeric_data),
        "skipped_non_numeric": len(data) - n,
        "calculated_at": time.time()
    }

def hash_data(data: Any) -> Dict[str, str]:
    """
    Generate hash signatures for data integrity
    
    Args:
        data: Any data to hash
    
    Returns:
        dict: Hash signatures using different algorithms
    """
    # Convert data to string representation
    if isinstance(data, (dict, list)):
        data_str = json.dumps(data, sort_keys=True)
    else:
        data_str = str(data)
    
    data_bytes = data_str.encode('utf-8')
    
    return {
        "md5": hashlib.md5(data_bytes).hexdigest(),
        "sha1": hashlib.sha1(data_bytes).hexdigest(),
        "sha256": hashlib.sha256(data_bytes).hexdigest(),
        "data_length": len(data_str),
        "hashed_at": time.time()
    }

def validate_data_structure(data: Dict, schema: Dict) -> Dict[str, Any]:
    """
    Validate data against a simple schema
    
    Args:
        data: Data to validate
        schema: Schema definition
    
    Returns:
        dict: Validation results
    """
    if not isinstance(data, dict):
        return {
            "valid": False,
            "error": "Data must be a dictionary",
            "received_type": type(data).__name__
        }
    
    if not isinstance(schema, dict):
        return {
            "valid": False,
            "error": "Schema must be a dictionary",
            "received_type": type(schema).__name__
        }
    
    errors = []
    warnings = []
    
    # Check required fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check field types
    field_types = schema.get("types", {})
    for field, expected_type in field_types.items():
        if field in data:
            actual_type = type(data[field]).__name__
            if actual_type != expected_type:
                errors.append(f"Field '{field}' expected {expected_type}, got {actual_type}")
    
    # Check for unexpected fields
    allowed_fields = set(field_types.keys()) | set(required_fields)
    unexpected = set(data.keys()) - allowed_fields
    if unexpected:
        warnings.append(f"Unexpected fields: {list(unexpected)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "fields_checked": len(data),
        "validated_at": time.time()
    }

# Export all functions
__all__ = [
    "analyze_data",
    "parse_csv_string", 
    "filter_data",
    "group_data",
    "summary_stats",
    "hash_data",
    "validate_data_structure"
]
'''

    # Create manifest
    manifest = {
        "name": "data_tools",
        "version": "1.0.0",
        "provider": "demo",
        "description": "Comprehensive data analysis and processing tools",
        "author": "PKG System Demo",
        "entry_point": "data_tools.py",
        "exports": [
            "analyze_data", "parse_csv_string", "filter_data", 
            "group_data", "summary_stats", "hash_data", "validate_data_structure"
        ],
        "dependencies": [],
        "python_version": ">=3.6",
        "created": time.time(),
        "security_hash": hashlib.sha256(data_tools_code.encode()).hexdigest()
    }
    
    # Create .pkg file
    output_dir = Path("examples")
    output_dir.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(output_dir / "data_tools.pkg", 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        zf.writestr("data_tools.py", data_tools_code)
    
    print("✓ Created data_tools.pkg")
    return output_dir / "data_tools.pkg"

def create_all_example_packages():
    """Create all example packages"""
    print("Creating example PKG packages...")
    
    packages_created = []
    
    # Create packages
    packages_created.append(create_webscraper_package())
    packages_created.append(create_data_tools_package())
    
    print(f"\n✓ Created {len(packages_created)} example packages:")
    for pkg in packages_created:
        print(f"  - {pkg.name}")
    
    return packages_created

if __name__ == "__main__":
    create_all_example_packages()