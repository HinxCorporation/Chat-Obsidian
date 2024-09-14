import json

import requests


class MediaWikiAPI:
    def __init__(self, site_host):
        self.api_url = f"https://{site_host}/api.php"

    def query(self, action, **params):
        params.update({
            "action": action,
            "format": "json",
        })
        response = None
        try:
            response = requests.get(self.api_url, params=params, proxies={"http": None, "https": None})
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            print(f"Response content: {response.text}")
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON: {e}")
            print(f"Response content: {response.text}")
            return None

    def search(self, query, limit=10):
        return self.query("query", list="search", srsearch=query, srlimit=limit)

    def get_page_content(self, title):
        return self.query("parse", page=title, prop="text")

    def get_random_page(self, limit=1):
        return self.query("query", list="random", rnlimit=limit)

    def list_query_titles(self, query):
        return self.query("query", list="search", srsearch=query, srprop="title")


def __demo_query_and_draw_first_result(item):
    # Create an instance of MediaWikiAPI for English Wikipedia
    wiki = MediaWikiAPI("terraria.wiki.gg")

    # Perform a search query
    search_results = wiki.search(item)

    if search_results is None:
        print("Failed to get search results.")
    else:
        # Print the search results
        print(f"Search results for '{item}':")
        for result in search_results.get('query', {}).get('search', []):
            print(f"- {result['title']}")

        # Get the content of the first search result
        if search_results.get('query', {}).get('search'):
            first_result_title = search_results['query']['search'][0]['title']
            page_content = wiki.get_page_content(first_result_title)

            if page_content is not None:
                # Print a snippet of the page content
                print(f"\nSnippet of '{first_result_title}':")
                # write response to result.html file
                with open('result.html', 'w', encoding='utf-8') as f:
                    f.write(page_content['parse']['text']['*'])
                # out print the response to console
                print(page_content['parse']['text']['*'][:1000])
            else:
                print("Failed to get page content.")

    # Get a random page
    random_page = wiki.get_random_page()
    if random_page is not None:
        random_title = random_page.get('query', {}).get('random', [{}])[0].get('title')
        print(f"\nRandom page: {random_title}")
    else:
        print("Failed to get random page.")


def __demo_list_query_titles(item):
    # Create an instance of MediaWikiAPI for English Wikipedia
    wiki = MediaWikiAPI("terraria.wiki.gg")

    # Perform a search query
    search_results = wiki.list_query_titles(item)

    if search_results is None:
        print("Failed to get search results.")
    else:
        # Print the search results
        print(f"Search results for '{item}':")
        for result in search_results.get('query', {}).get('search', []):
            print(f"- {result['title']}")


# Example usage and test runner:
if __name__ == "__main__":
    query_item = 'angler'
    __demo_list_query_titles(query_item)
