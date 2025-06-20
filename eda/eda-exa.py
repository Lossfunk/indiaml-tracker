from exa_py import AsyncExa
# [{'institute_name': 'Hong Kong Baptist University', 'location': 'Hong Kong', 'website': None, 'type': 'academic', 'country': 'HK'}, {'institute_name': 'RIKEN', 'location': None, 'website': None, 'type': None, 'country': None}]

async def main():
    exa = AsyncExa(api_key="06624558-05d2-4d14-ae96-182afc7fc5cd")

    # Example query to fetch all papers
    response = await exa.answer(
        """
This is a either a research institute, government agency, or a corporate entity.

For the given institute or department, fetch as much information as possible, such as:
- ROR ID
- OpenAlex ID
- Wikipedia link
- Wikidata ID
- Country (2 letter ISO code)
- Latitude and Longitude
- Canonical name
- Homepage URL
- Type (academic, corporate, government)
- Department (if available)
- Lab (if available)
- Location (if available)
- Additional metadata (if available)
""",
model="exa-pro"
    )

    # Print the results
    print(response)






if __name__ == "__main__":
    import asyncio
    asyncio.run(main())