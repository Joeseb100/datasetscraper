import random
import requests
from typing import Optional, List, Dict

class ProxyManager:
    def __init__(self):
        self.proxies = [
            {"http": "43.153.27.33:13001"},
            {"http": "119.3.113.150:9094"}
        ]
        self._valid_proxies = None

    def get_random_proxy(self) -> Optional[Dict]:
        """Get a random proxy from the list"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    def get_valid_proxy(self) -> Optional[Dict]:
        """Get first working proxy from the list"""
        if not hasattr(self, '_valid_proxies') or self._valid_proxies is None:
            self._valid_proxies = self._test_proxies()
            
        if self._valid_proxies:
            return random.choice(self._valid_proxies)
        return None
        
    def _test_proxies(self) -> List[Dict]:
        """Test all proxies and return working ones using requests instead of browser"""
        working_proxies = []
        test_urls = [
            "https://www.google.com",
            "https://www.bing.com",
            "https://www.microsoft.com"
        ]
        
        for proxy in self.proxies:
            try:
                # Use requests to test proxy - much lighter than launching a browser
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
                })
                
                # Try multiple URLs in case one is blocked
                for test_url in test_urls:
                    try:
                        response = session.get(
                            test_url,
                            proxies={"http": f"http://{proxy['http']}", "https": f"http://{proxy['http']}"},
                            timeout=5
                        )
                        if response.status_code == 200:
                            working_proxies.append(proxy)
                            print(f"Proxy {proxy['http']} is working")
                            break
                    except Exception:
                        continue
            except Exception as e:
                print(f"Error testing proxy {proxy['http']}: {str(e)}")
                continue
                
        return working_proxies

    def get_all_proxies(self) -> List[Dict]:
        """Get all available proxies"""
        return self.proxies
