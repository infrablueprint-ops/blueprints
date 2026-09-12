import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        remove_overlay_elements=True,
        magic=True,
        word_count_threshold=10,
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://docs.ansible.com/",
            config=config
        )
        if result.success:
            print(f"Extraction successful! Title: {result.metadata.get('title')}")
            print(f"Markdown length: {len(result.markdown)} chars")
            print("Preview:\n", result.markdown[:300])
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
