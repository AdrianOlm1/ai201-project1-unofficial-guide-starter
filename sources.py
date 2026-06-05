"""Single source of truth for the 10 documents in the UCSC Unofficial Guide corpus.

Each entry maps a filename (saved under documents/) to the URL it came from.
ingest.py reads this list to download and clean each page.
"""

SOURCES = [
    {
        "filename": "01_cohp_eleven_things.txt",
        "url": "https://cityonahillpress.com/2014/07/21/eleven-things-to-know-going-into-your-first-year/",
        "title": "City on a Hill Press — Eleven Things to Know Going Into Your First Year",
    },
    {
        "filename": "02_cohp_housing_guide.txt",
        "url": "https://cityonahillpress.com/2026/03/01/a-guide-to-ucsc-housing/",
        "title": "City on a Hill Press — A Guide to UCSC Housing",
    },
    {
        "filename": "03_cohp_residential_colleges.txt",
        "url": "https://cityonahillpress.com/2022/09/18/a-perfect-ten-ucscs-residential-colleges/",
        "title": "City on a Hill Press — A Perfect Ten: UCSC's Residential Colleges",
    },
    {
        "filename": "04_cohp_bus_guide_2023.txt",
        "url": "https://cityonahillpress.com/2023/09/27/a-guide-to-taking-the-bus-for-the-transit-savvy/",
        "title": "City on a Hill Press — A Guide to Taking the Bus for the Transit-Savvy",
    },
    {
        "filename": "05_cohp_bus_guide_2008.txt",
        "url": "https://cityonahillpress.com/2008/10/23/a-simple-guide-to-buses-on-campus/",
        "title": "City on a Hill Press — A Simple Guide to Buses on Campus (2008)",
    },
    {
        "filename": "06_collegevine_colleges_ranked.txt",
        "url": "https://www.collegevine.com/faq/31271/ucsc-colleges-ranked",
        "title": "CollegeVine — UCSC colleges ranked?",
    },
    {
        # Replaced the original Quora source: Quora hard-blocks all scrapers
        # (HTTP 403 login wall) so it could not be ingested. This CollegeVine
        # FAQ covers the same student-perspective angle (dorm/residential life)
        # and is publicly accessible.
        "filename": "07_collegevine_dorm_life.txt",
        "url": "https://www.collegevine.com/faq/124138/what-s-campus-life-like-in-uc-santa-cruz-dorms",
        "title": "CollegeVine — What's Campus Life Like in UC Santa Cruz Dorms?",
    },
    {
        "filename": "08_niche_reviews.txt",
        "url": "https://www.niche.com/colleges/university-of-california-santa-cruz/reviews/",
        "title": "Niche — UC Santa Cruz Reviews",
    },
    {
        "filename": "09_niche_campus_life.txt",
        "url": "https://www.niche.com/colleges/university-of-california-santa-cruz/campus-life/",
        "title": "Niche — UC Santa Cruz Campus Life",
    },
    {
        "filename": "10_goodtimes_best_places_to_eat.txt",
        "url": "https://www.goodtimes.sc/best-places-to-eat-ucsc-university-of-california-santa-cruz-dining/",
        "title": "GoodTimes Santa Cruz — The Best Places to Eat on the UCSC Campus",
    },
]
