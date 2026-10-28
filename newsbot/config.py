"""News categories, feeds and market symbols."""

from urllib.parse import quote_plus

# Google News search RSS. `when:{days}d` is filled in at fetch time; results are
# filtered again locally by the trading-day window.
GOOGLE_NEWS = "https://news.google.com/rss/search?q={query}+when:{days}d&hl=en-US&gl=US&ceid=US:en"


def google_news(query: str) -> str:
    return GOOGLE_NEWS.replace("{query}", quote_plus(query))


def cnbc(feed_id: int) -> str:
    return f"https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id={feed_id}"


# Each category: feeds that belong to it outright, plus keywords used to route
# items from the general feeds below.
CATEGORIES = [
    {
        "key": "macro",
        "name": "宏观",
        "icon": "🌐",
        "feeds": [
            cnbc(20910258),  # Economy
            google_news('"Federal Reserve" OR FOMC OR Powell OR "rate cut" OR "rate hike"'),
            google_news("CPI OR PCE OR inflation OR \"jobs report\" OR payrolls OR GDP economy"),
            google_news('"Treasury yields" OR "bond market" OR dollar OR tariffs economy'),
            google_news('"stock market today" OR "Dow Jones" OR "S&P 500" OR Nasdaq close'),
        ],
        "keywords": [
            "fed", "federal reserve", "fomc", "powell", "rate cut", "rate hike", "interest rate",
            "inflation", "cpi", "pce", "ppi", "jobs report", "payroll", "unemployment", "jobless",
            "gdp", "recession", "treasury", "yield", "bond", "dollar", "tariff", "trade war",
            "deficit", "debt ceiling", "shutdown", "economy", "economic", "s&p 500", "dow jones",
            "nasdaq", "stock market", "wall street", "stocks close", "oil price", "opec",
        ],
    },
    {
        "key": "tech",
        "name": "科技",
        "icon": "💻",
        "feeds": [
            cnbc(19854910),  # Technology
            google_news("Nvidia OR Apple OR Microsoft OR Alphabet OR Meta OR Amazon stock"),
            google_news('semiconductor OR chip stocks OR AMD OR Broadcom OR TSMC OR "AI stocks"'),
            google_news("OpenAI OR Anthropic OR \"artificial intelligence\" OR \"data center\" stocks"),
        ],
        "keywords": [
            "nvidia", "apple", "microsoft", "alphabet", "google", "meta ", "amazon web services",
            "aws", "semiconductor", "chip", "amd", "intel", "broadcom", "tsmc", "qualcomm", "micron",
            "artificial intelligence", " ai ", "openai", "anthropic", "data center", "cloud",
            "software", "salesforce", "oracle", "palantir", "netflix", "tech stock", "big tech",
            "smartphone", "iphone", "antitrust",
        ],
    },
    {
        "key": "defense",
        "name": "国防军工",
        "icon": "🛡️",
        "feeds": [
            "https://www.defensenews.com/arc/outboundfeeds/rss/",
            "https://breakingdefense.com/feed/",
            google_news('"Lockheed Martin" OR "RTX Corp" OR Raytheon OR "Northrop Grumman" OR "General Dynamics"'),
            google_news('Pentagon contract OR "defense stocks" OR "defense budget" OR "L3Harris" OR Anduril'),
        ],
        "keywords": [
            "defense", "defence", "pentagon", "military", "lockheed", "raytheon", "rtx corp",
            "northrop", "general dynamics", "l3harris", "huntington ingalls", "boeing defense",
            "anduril", "missile", "drone", "army", "navy", "air force", "nato", "munitions",
            "f-35", "hypersonic", "contract award", "dod",
        ],
    },
    {
        "key": "consumer",
        "name": "消费",
        "icon": "🛒",
        "feeds": [
            cnbc(10000116),  # Retail
            google_news('"retail sales" OR "consumer spending" OR "consumer confidence" OR "consumer sentiment"'),
            google_news("Walmart OR Costco OR Target OR \"Home Depot\" OR Nike OR Starbucks OR McDonald's stock"),
            google_news("Coca-Cola OR PepsiCo OR \"Procter & Gamble\" OR Lululemon OR Chipotle earnings"),
        ],
        "keywords": [
            "retail", "consumer", "walmart", "costco", "target", "home depot", "lowe's", "nike",
            "starbucks", "mcdonald", "chipotle", "coca-cola", "pepsi", "procter", "p&g",
            "lululemon", "restaurant", "apparel", "e-commerce", "shopping", "holiday sales",
            "black friday", "spending", "disney", "airline", "travel", "hotel", "luxury",
        ],
    },
    {
        "key": "financials",
        "name": "金融",
        "icon": "🏦",
        "feeds": [
            cnbc(10000664),  # Finance
            google_news('JPMorgan OR "Goldman Sachs" OR "Morgan Stanley" OR "Bank of America" OR Citigroup OR "Wells Fargo"'),
            google_news("bank stocks OR \"regional banks\" OR \"private credit\" OR \"Berkshire Hathaway\" OR BlackRock"),
            google_news("\"Visa Inc\" OR Mastercard OR \"American Express\" OR PayPal OR Coinbase OR \"crypto stocks\""),
        ],
        "keywords": [
            "bank", "jpmorgan", "goldman", "morgan stanley", "citigroup", "citi", "wells fargo",
            "bank of america", "berkshire", "blackrock", "private credit", "private equity",
            "insurance", "insurer", "visa inc", "mastercard", "american express", "paypal",
            "coinbase", "bitcoin", "crypto", "fintech", "lending", "loan", "mortgage", "sec ",
            "capital requirements", "basel", "fdic", "brokerage", "asset manager",
        ],
    },
    {
        "key": "autonomy",
        "name": "自动驾驶与人形机器人",
        "icon": "🤖",
        "feeds": [
            "https://www.therobotreport.com/feed/",
            google_news('robotaxi OR Waymo OR "Tesla FSD" OR Zoox OR "self-driving" OR "autonomous driving"'),
            google_news('"humanoid robot" OR "Tesla Optimus" OR "Figure AI" OR "Boston Dynamics" OR "Agility Robotics"'),
            google_news('Mobileye OR Aurora autonomous trucks OR "Pony.ai" OR WeRide OR Baidu Apollo'),
        ],
        "keywords": [
            "robotaxi", "waymo", "fsd", "full self-driving", "self-driving", "autonomous",
            "driverless", "zoox", "cruise", "mobileye", "aurora innovation", "pony.ai", "weride",
            "apollo go", "lidar", "humanoid", "optimus", "figure ai", "boston dynamics",
            "agility robotics", "unitree", "1x technologies", "apptronik", "robot",
        ],
    },
]

# General market feeds; their items are routed to categories by keyword.
GENERAL_FEEDS = [
    cnbc(100003114),  # Top News
    cnbc(15839069),   # Investing
    cnbc(15839135),   # Earnings
    "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
    "https://finance.yahoo.com/news/rssindex",
]

# Publisher names for feeds that don't name one per item.
FEED_SOURCES = {
    "search.cnbc.com": "CNBC",
    "feeds.content.dowjones.io": "MarketWatch",
    "finance.yahoo.com": "Yahoo Finance",
    "www.defensenews.com": "Defense News",
    "breakingdefense.com": "Breaking Defense",
    "www.therobotreport.com": "The Robot Report",
}

# Ranking weight by publisher (substring match, lowercase). Unlisted sources get 0.
SOURCE_WEIGHTS = {
    3: ["reuters", "bloomberg", "wall street journal", "wsj", "financial times", "cnbc",
        "associated press", "ap news", "barron", "marketwatch"],
    2: ["yahoo finance", "investor's business daily", "new york times", "washington post", "axios",
        "fortune", "business insider", "forbes", "techcrunch", "the verge", "the information",
        "defense news", "breaking defense", "defense one", "the robot report", "electrek",
        "insideevs", "coindesk", "morningstar", "politico", "the economist", "semafor"],
    1: ["seeking alpha", "investopedia", "benzinga", "investing.com", "motley fool", "zacks",
        "tradingview", "nasdaq", "teslarati", "fox business", "cnn", "abc news", "cbs news", "nbc news"],
}

# Headlines about other markets are demoted unless they also mention the US.
FOREIGN_TERMS = ["australia", "rba", "canad", "india", "sensex", "nifty", "rbi", "nikkei", "japan's",
                 "korea", "kospi", "ftse", "britain", "u.k.", "new zealand", "philippine", "vietnam",
                 "indonesia", "malaysia", "pakistan", "nigeria", "south africa", "brazil", "mexico's"]
US_TERMS = ["u.s.", " us ", "america", "wall street", "s&p", "nasdaq", "dow", "fed", "nyse", "washington",
            "trump", "pentagon"]

# Market snapshot (Yahoo Finance chart API symbols).
MARKET_SYMBOLS = [
    ("^GSPC", "标普500"),
    ("^IXIC", "纳斯达克"),
    ("^DJI", "道琼斯"),
    ("^RUT", "罗素2000"),
    ("^VIX", "VIX"),
    ("^TNX", "10年美债收益率"),
    ("DX-Y.NYB", "美元指数"),
    ("CL=F", "WTI原油"),
    ("GC=F", "黄金"),
    ("BTC-USD", "比特币"),
]

# Sector ETFs shown next to the snapshot, one per category where it makes sense.
SECTOR_SYMBOLS = [
    ("XLK", "科技 XLK"),
    ("SMH", "半导体 SMH"),
    ("ITA", "军工 ITA"),
    ("XLY", "可选消费 XLY"),
    ("XLP", "必选消费 XLP"),
    ("XLF", "金融 XLF"),
    ("TSLA", "特斯拉 TSLA"),
    ("BOTZ", "机器人 BOTZ"),
]

# How many items per category to show when no Claude summary is available,
# and how many candidates to hand to Claude.
MAX_ITEMS_PLAIN = 15
MAX_CANDIDATES = 60
