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

# Coverage list for the daily stock guidance: per category, (ticker, name, key drivers).
# The drivers are what the analysis checks each new event against.
COVERAGE = {
    "macro": [
        ("SPY", "标普500 ETF", "盈利预期、实际利率、风险偏好"),
        ("QQQ", "纳指100 ETF", "长端利率、AI资本开支叙事、大型科技盈利"),
        ("IWM", "罗素2000 ETF", "降息路径、信用利差、国内经济"),
        ("TLT", "20年+美债 ETF", "通胀、美联储路径、财政赤字与发债"),
        ("GLD", "黄金 ETF", "实际利率、美元、地缘避险、央行购金"),
        ("UUP", "美元指数 ETF", "美欧日利差、避险需求、关税"),
    ],
    "tech": [
        ("NVDA", "英伟达", "数据中心GPU需求、云厂商资本开支、出口管制、新架构量产节奏"),
        ("MSFT", "微软", "Azure增速、AI资本开支回报、Copilot变现、OpenAI关系"),
        ("AAPL", "苹果", "iPhone换机周期、服务收入、中国需求、关税与供应链"),
        ("GOOGL", "Alphabet", "搜索份额与AI冲击、云业务增速、反垄断裁决、TPU"),
        ("AMZN", "亚马逊", "AWS增速与产能、零售利润率、资本开支"),
        ("META", "Meta", "广告价格与展示量、AI资本开支、Reality Labs亏损"),
        ("AVGO", "博通", "定制AI芯片（XPU）订单、网络芯片、VMware"),
        ("TSM", "台积电", "先进制程与CoWoS产能、AI订单、地缘与关税"),
        ("AMD", "AMD", "MI系列GPU放量、服务器CPU份额"),
        ("ORCL", "甲骨文", "OCI云订单（RPO）、AI数据中心融资与资本开支"),
    ],
    "defense": [
        ("LMT", "洛克希德·马丁", "F-35交付与维护、导弹产能（PAC-3/GMLRS/JASSM）、机密项目成本超支"),
        ("RTX", "雷神技术", "Raytheon导弹与防空需求、Pratt发动机（GTF）问题、商用售后"),
        ("NOC", "诺斯罗普·格鲁曼", "B-21进度与利润率、Sentinel洲际导弹、航天业务"),
        ("GD", "通用动力", "潜艇（Columbia/Virginia）产能、湾流公务机交付、弹药"),
        ("BA", "波音", "737/787交付与FAA产能上限、防务固定价合同亏损、现金流"),
        ("LHX", "L3哈里斯", "导弹固体火箭发动机（Aerojet）、太空传感器、通信"),
        ("HII", "亨廷顿英格尔斯", "造船劳动力与产能、海军预算、利润率修复"),
        ("LDOS", "Leidos", "政府IT与服务合同、DOGE式支出审查"),
        ("PLTR", "Palantir", "国防软件合同、美国商业客户增长、估值"),
        ("AVAV", "AeroVironment", "无人机与巡飞弹订单、乌克兰需求、BlueHalo整合"),
        ("KTOS", "Kratos", "无人靶机/协同作战飞机、高超音速测试"),
        ("RKLB", "Rocket Lab", "Neutron火箭进度、国防航天合同（SDA）"),
    ],
    "consumer": [
        ("WMT", "沃尔玛", "同店销售、高收入客群份额、电商与广告利润"),
        ("COST", "好市多", "会员续费率、同店销售、会费调整"),
        ("HD", "家得宝", "房地产成交与利率、大件维修需求"),
        ("MCD", "麦当劳", "低收入客群客流、促销与定价"),
        ("KO", "可口可乐", "定价能力、销量、汇率"),
        ("PG", "宝洁", "提价与销量、原材料成本、汇率"),
        ("NKE", "耐克", "转型进度、库存与折扣、中国需求、关税"),
        ("SBUX", "星巴克", "美国同店客流、转型计划、中国竞争"),
        ("TGT", "塔吉特", "可选消费需求、库存、竞争份额"),
        ("TJX", "TJX", "折扣零售份额、库存采购机会"),
    ],
    "financials": [
        ("JPM", "摩根大通", "净利息收入（NII）指引、投行与交易收入、信用成本"),
        ("BAC", "美国银行", "NII对利率敏感度、存款成本"),
        ("GS", "高盛", "并购与IPO活跃度、交易收入、资产管理"),
        ("MS", "摩根士丹利", "财富管理资金流、投行"),
        ("WFC", "富国银行", "资产上限解除后的扩张、费用控制"),
        ("C", "花旗", "重组进度、ROTCE目标"),
        ("BRK-B", "伯克希尔", "保险浮存金、现金部署、回购"),
        ("BLK", "贝莱德", "资金流入、私募信贷与基础设施"),
        ("V", "Visa", "跨境支付量、消费支出、监管（刷卡费）"),
        ("MA", "万事达", "支付量增速、跨境旅行"),
        ("SCHW", "嘉信理财", "客户资产流入、现金分流"),
        ("COIN", "Coinbase", "加密货币价格与交易量、监管立法"),
    ],
    "autonomy": [
        ("TSLA", "特斯拉", "FSD/Robotaxi进展与监管、Optimus量产时间表、汽车交付与毛利"),
        ("GOOGL", "Alphabet（Waymo）", "Waymo城市扩张、付费单量、安全事件"),
        ("NVDA", "英伟达", "DRIVE Thor与机器人平台（Isaac/GR00T）合作"),
        ("UBER", "Uber", "与自动驾驶公司合作还是被颠覆、出行需求"),
        ("MBLY", "Mobileye", "ADAS订单、Robotaxi合作、英特尔减持"),
        ("AUR", "Aurora", "无人驾驶卡车商业化里程与客户"),
        ("PONY", "小马智行", "Robotaxi车队规模、海外扩张"),
        ("WRD", "文远知行", "Robotaxi与Robobus海外合作"),
        ("TER", "泰瑞达", "协作机器人（Universal Robots）需求"),
        ("SYM", "Symbotic", "仓储机器人订单（沃尔玛）、交付节奏"),
    ],
}
