# 美股每日简报（私人）

这个网页在每个美股交易日收盘后自动更新，汇总最新交易日的美股新闻，分为六个板块：

🌐 宏观 · 💻 科技 · 🛡️ 国防军工 · 🛒 消费 · 🏦 金融 · 🤖 自动驾驶与人形机器人

另外还有市场快照（主要指数、美债收益率、美元、原油、黄金、比特币，以及各板块 ETF）和全市场要点。

## 工作原理

```
GitHub Actions（每周一至周五 22:15 UTC，即北京时间次日 06:15）
  ├─ 计算最新交易日（NYSE 日历，含节假日），新闻窗口 = 前一交易日 16:00 ET → 当日 24:00 ET
  ├─ 抓取 RSS：Google News 分板块检索、CNBC、MarketWatch、Yahoo Finance、Defense News、
  │           Breaking Defense、The Robot Report 等；按关键词归类、去重
  ├─ 抓取收盘行情（Yahoo Finance）
  ├─ Claude（可选）：每个板块筛选 6–12 条重要新闻，生成中文标题、摘要、相关代码、利好/利空判断，以及板块要点和全市场要点
  ├─ 用 AES-256-GCM 加密（密钥由访问密码经 PBKDF2-SHA256 60 万次迭代派生）
  └─ 推送密文到 site-data 分支（保存历史），并部署到 GitHub Pages / Cloudflare Pages
```

网页本身只是一个外壳：浏览器在本地输入密码解密数据，服务器上和仓库里只有密文。没有密码看不到任何新闻内容。页面还设置了 `noindex`，并通过 robots.txt 禁止搜索引擎收录。

## 部署步骤

1. **合并代码到默认分支**：定时任务只在默认分支上运行（把本分支合并到 `main`，或者把它设为默认分支）。
2. **配置 Secrets**（Settings → Secrets and variables → Actions → New repository secret）：
   | 名称 | 必需 | 说明 |
   |---|---|---|
   | `PAGE_PASSWORD` | ✅ | 网页访问密码。密文是公开可下载的，请使用 **12 位以上的随机密码**以防离线暴力破解 |
   | `ANTHROPIC_API_KEY` | 推荐 | 用于生成中文摘要和要点。不配置时只显示英文标题列表 |
3. **开启 GitHub Pages**：Settings → Pages → Source 选 **GitHub Actions**。
   - 私有仓库使用 Pages 需要 GitHub Pro/Team 等付费计划。如果是免费账户，有两个办法：
     - 把仓库设为 public：仓库里只有代码和密文，密码保存在 Secrets 中，不会泄露；或者
     - 改用 Cloudflare Pages（见下文），并把仓库变量 `DISABLE_GITHUB_PAGES` 设为 `true`。
4. **首次运行**：Actions → *Daily US market news* → Run workflow。完成后访问
   `https://<用户名>.github.io/<仓库名>/`（本仓库对应 `https://lucas168717.github.io/News/`）。

之后每个交易日自动更新；周末和 NYSE 休市日不会生成新的一天。页面顶部的下拉框可以查看历史交易日。

### 可选：Cloudflare Pages + Cloudflare Access（真正的登录保护）

如果希望连密文都不对外公开，可以部署到 Cloudflare Pages，再用 Cloudflare Zero Trust → Access 给站点加上邮箱验证码登录（免费套餐即可）：

1. 在 Cloudflare 创建一个 Pages 项目（Direct Upload），名称默认 `us-market-news`，或者用仓库变量 `CLOUDFLARE_PROJECT` 指定。
2. 添加 Secrets：`CLOUDFLARE_API_TOKEN`（需要 Pages 编辑权限）和 `CLOUDFLARE_ACCOUNT_ID`。
3. 在 Zero Trust → Access → Applications 中为该站点域名添加策略，只允许你自己的邮箱访问。

配置了 `CLOUDFLARE_API_TOKEN` 后，工作流会自动部署到 Cloudflare。页面密码加密仍然有效，相当于两层保护。

## 可调整的地方

| 位置 | 内容 |
|---|---|
| `newsbot/config.py` | 板块、RSS 源 / 检索词、归类关键词、行情代码 |
| 仓库变量 `NEWSBOT_MODEL` | 默认 `claude-opus-5-5`，可以换成其他 Claude 模型 |
| `.github/workflows/daily-news.yml` | 运行时间（cron，UTC） |
| `newsbot/trading_calendar.py` | `SPECIAL_CLOSURES`：临时休市日（如国丧日） |

**费用参考**：每天调用 7 次 Claude（6 个板块 + 1 次总结）。按 Opus 5.5 的价格，粗略估计每天几十美分；实际费用取决于当天的新闻量。

**更换密码**：直接修改 `PAGE_PASSWORD` 即可。旧密码加密的历史数据无法再解密，下次运行时会被清空，并从当天重新开始积累。

## 本地运行

```bash
pip install -r requirements.txt
PAGE_PASSWORD='your-password' ANTHROPIC_API_KEY=... python -m newsbot.build --site-dir site
python -m http.server -d site 8000   # 打开 http://localhost:8000
```

`--date YYYY-MM-DD` 用于重新生成指定交易日（RSS 只保留最近几天的新闻，太早的日期抓不到内容），`--force` 用于覆盖已经生成的当天数据。

测试：`pip install pytest && python -m pytest`

> 免责声明：内容由程序自动抓取，摘要由 AI 生成，可能有误，仅供个人参考，不构成投资建议。
