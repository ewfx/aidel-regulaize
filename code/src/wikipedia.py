import asyncio
from crawl4ai import AsyncWebCrawler


async def fetch_company_info(url="https://en.wikipedia.org/wiki/Apple_Inc"):
    async with AsyncWebCrawler() as crawler:
        # Run the async crawler
        result = await crawler.arun(url=url)

        if not result or not result.content:
            return "Failed to retrieve content"

        # Extract entities from the page content
        entities = result.extract_entities()

        # Extract company-specific details using regex
        company_info = {
            "Company Name": entities.get("ORG", []),  # Extract organization names
            "Headquarters": result.regex_search(r'Headquarters[:\s]+([^\n]+)'),
            "CEO": result.regex_search(r'CEO[:\s]+([^\n]+)'),
            "Industry": result.regex_search(r'Industry[:\s]+([^\n]+)'),
            "Founded": result.regex_search(r'Founded[:\s]+([^\n]+)')
        }

        return company_info


async def main():
    url = "https://en.wikipedia.org/wiki/Microsoft"  # Change for different companies
    company_details = await fetch_company_info(url)
    print(company_details)


if __name__ == "__main__":
    asyncio.run(main())
