#!/usr/bin/env python3
"""
Web Search Extension for Claude Computer Use API

This extension provides web search capabilities using the DuckDuckGo API,
allowing Claude to perform targeted web searches without full web browsing.
"""

import os
import json
import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Union
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

# Import the extension base class from the parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension_module import Extension

# Configure logging
logger = logging.getLogger('web_search')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler('logs/web_search.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Constants
DUCKDUCKGO_API_URL = "https://api.duckduckgo.com/"
GOOGLE_SEARCH_URL = "https://www.google.com/search"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
TIMEOUT = 15.0  # seconds
CACHE_DIR = os.path.join("data", "web_search_cache")


class WebSearch(Extension):
    """
    Extension for performing web searches
    """
    
    name = "web_search"
    description = "Performs web searches and retrieves information from the internet"
    version = "1.0.0"
    author = "Claude Computer Use API Team"
    
    def __init__(self):
        """Initialize the Web Search extension"""
        super().__init__()
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        
        # Ensure cache directory exists
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        logger.info("Web Search extension initialized")
    
    async def search(self, 
                    query: str, 
                    num_results: int = 5, 
                    use_cache: bool = True) -> Dict[str, Any]:
        """
        Perform a web search using DuckDuckGo
        
        Args:
            query: Search query
            num_results: Number of results to return
            use_cache: Whether to use cached results
            
        Returns:
            Search results
        """
        cache_file = os.path.join(CACHE_DIR, f"{quote_plus(query)}.json")
        
        # Check cache if enabled
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_results = json.load(f)
                    logger.info(f"Using cached results for query: {query}")
                    return {
                        "status": "success",
                        "query": query,
                        "results": cached_results['results'][:num_results],
                        "source": "cache"
                    }
            except Exception as e:
                logger.error(f"Error reading from cache: {str(e)}")
        
        # Perform the search using DuckDuckGo API
        try:
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                't': 'claude-computer-api'
            }
            
            response = await self.client.get(DUCKDUCKGO_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process results
            results = []
            
            # Add Instant Answer if available
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', 'Instant Answer'),
                    'snippet': data.get('Abstract'),
                    'url': data.get('AbstractURL'),
                    'source': 'instant_answer'
                })
            
            # Add related topics
            for topic in data.get('RelatedTopics', [])[:num_results]:
                if 'Topics' in topic:
                    # This is a category
                    continue
                
                title = topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else topic.get('Text', '')
                snippet = topic.get('Text', '')
                
                results.append({
                    'title': title,
                    'snippet': snippet,
                    'url': topic.get('FirstURL'),
                    'source': 'related_topic'
                })
            
            # If we don't have enough results, use Google as a fallback
            if len(results) < num_results:
                google_results = await self._google_search(query, num_results)
                for result in google_results:
                    # Avoid duplicates
                    if not any(r.get('url') == result.get('url') for r in results):
                        results.append(result)
            
            # Limit to requested number of results
            results = results[:num_results]
            
            # Cache the results
            try:
                with open(cache_file, 'w') as f:
                    json.dump({
                        'query': query,
                        'results': results
                    }, f, indent=2)
            except Exception as e:
                logger.error(f"Error writing to cache: {str(e)}")
            
            return {
                "status": "success",
                "query": query,
                "results": results,
                "source": "api"
            }
        
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            
            # Try Google as a fallback
            try:
                logger.info("Trying Google fallback search")
                results = await self._google_search(query, num_results)
                
                return {
                    "status": "partial_success",
                    "query": query,
                    "results": results,
                    "source": "google_fallback",
                    "error": str(e)
                }
            except Exception as e2:
                logger.error(f"Google fallback search error: {str(e2)}")
                return {
                    "status": "error",
                    "query": query,
                    "error": f"Primary search failed: {str(e)}. Fallback failed: {str(e2)}"
                }
    
    async def _google_search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Perform a Google search as a fallback
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results
        """
        headers = {
            'User-Agent': USER_AGENT
        }
        
        params = {
            'q': query,
            'num': num_results + 5  # Request more to account for filtered results
        }
        
        try:
            response = await self.client.get(GOOGLE_SEARCH_URL, params=params, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = []
            
            # Extract search results
            for result in soup.select('div.g')[:num_results + 5]:
                try:
                    title_element = result.select_one('h3')
                    if not title_element:
                        continue
                        
                    title = title_element.get_text()
                    
                    url_element = result.select_one('a')
                    url = url_element.get('href') if url_element else None
                    
                    # Clean URL
                    if url and url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    snippet_element = result.select_one('div.VwiC3b')
                    snippet = snippet_element.get_text() if snippet_element else ""
                    
                    # Skip if missing essential info
                    if not title or not url:
                        continue
                    
                    search_results.append({
                        'title': title,
                        'snippet': snippet,
                        'url': url,
                        'source': 'google'
                    })
                    
                    if len(search_results) >= num_results:
                        break
                
                except Exception as e:
                    logger.error(f"Error parsing Google result: {str(e)}")
            
            return search_results[:num_results]
        
        except Exception as e:
            logger.error(f"Google search error: {str(e)}")
            return []
    
    async def read_url(self, 
                     url: str, 
                     max_length: int = 8000,
                     extract_mode: str = "main_content") -> Dict[str, Any]:
        """
        Read content from a URL
        
        Args:
            url: The URL to read
            max_length: Maximum content length to return
            extract_mode: Content extraction mode (full_page, main_content, or summary)
            
        Returns:
            URL content
        """
        try:
            headers = {
                'User-Agent': USER_AGENT
            }
            
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
                return {
                    "status": "error",
                    "url": url,
                    "error": f"Unsupported content type: {content_type}"
                }
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "svg", "footer", "header", "nav"]):
                script.extract()
            
            title = soup.title.string if soup.title else "Unknown Title"
            
            # Extract content based on mode
            if extract_mode == "full_page":
                text = soup.get_text()
                
            elif extract_mode == "summary":
                # Try to extract a summary (first few paragraphs)
                paragraphs = soup.find_all('p')
                text = "\n\n".join([p.get_text() for p in paragraphs[:5]])
                
            else:  # main_content
                # Try to find main content
                main_content = None
                
                # Look for common main content containers
                for selector in ['main', 'article', '#content', '.content', '.post', '.entry']:
                    content = soup.select(selector)
                    if content:
                        main_content = content[0]
                        break
                
                if main_content:
                    text = main_content.get_text()
                else:
                    # Fallback: use body content
                    text = soup.body.get_text() if soup.body else soup.get_text()
            
            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Truncate if needed
            if len(text) > max_length:
                text = text[:max_length] + "...[truncated]"
            
            return {
                "status": "success",
                "url": url,
                "title": title,
                "content": text,
                "content_length": len(text),
                "extract_mode": extract_mode
            }
        
        except Exception as e:
            logger.error(f"URL read error: {str(e)}")
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
    
    async def clear_cache(self) -> Dict[str, Any]:
        """
        Clear the search cache
        
        Returns:
            Status information
        """
        try:
            cache_files = [f for f in os.listdir(CACHE_DIR) if f.endswith('.json')]
            num_files = len(cache_files)
            
            for file in cache_files:
                os.remove(os.path.join(CACHE_DIR, file))
            
            return {
                "status": "success",
                "message": f"Cleared {num_files} cached search results"
            }
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def execute(self, command: str = "search", **kwargs) -> Dict[str, Any]:
        """
        Execute extension commands
        
        Args:
            command: The command to execute
            **kwargs: Command-specific arguments
            
        Returns:
            Command execution results
        """
        if command == "search":
            return await self.search(
                query=kwargs.get("query", ""),
                num_results=kwargs.get("num_results", 5),
                use_cache=kwargs.get("use_cache", True)
            )
        elif command == "read":
            return await self.read_url(
                url=kwargs.get("url", ""),
                max_length=kwargs.get("max_length", 8000),
                extract_mode=kwargs.get("extract_mode", "main_content")
            )
        elif command == "clear_cache":
            return await self.clear_cache()
        else:
            return {"status": "error", "message": f"Unknown command: {command}"}


# Add this extension to the registry
if __name__ == "__main__":
    # This allows for testing the extension directly
    extension = WebSearch()
    print(f"Initialized {extension.name} v{extension.version}")
    print(f"Commands: search, read, clear_cache")