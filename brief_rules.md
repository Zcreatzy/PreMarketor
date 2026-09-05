# A股港股早报自动化规则

本文件是本仓库 A股港股早报的云端规则单一事实来源。自动化提示词仅作为执行入口，不重复维护规则；08:35 完整发布和 09:10 增量复核每次运行都必须先从最新 `main` 完整读取本文件。各章节要求共同适用，来源降级不得放宽发布硬校验。

请用中文生成一份面向投资者的工作日 A股港股早报，并发布到 GitHub 静态页面。

目标仓库与文件：
- GitHub repository: zcluster/PreMarketor
- Branch: main
- 首页文件：index.html
- 历史日期页模板：history/index.html
- 历史清单：history/manifest.json
- 历史数据：history/data/YYYY-MM-DD.json

内容要求：
1. 结合最新国际局势、宏观与政策消息面、基本面、隔夜美股行情、automation 实际运行时的美股夜盘/期指即时走势、美元/美债/大宗商品/汇率等关键资产表现，以及近日尤其是昨天收盘后披露的 A股、港股、恒生科技权重或对 A/H 有直接映射的本地重要财报。生成判断前必须按第 9 条运行 AKShare A/H 行情证据抓取，将代表指数、市场涨跌家数、中位涨跌幅和领涨/领跌样本用于校准大盘基线、风险偏好、板块轮动及个股触发条件。美股夜盘/期指必须使用本次运行时重新抓取的行情快照，不得沿用隔夜收盘数据冒充；美股公司财报只能作为科技/宏观映射新闻引用，不得放入 A/H 财报结果模块补位。
2. 必须系统扫描隔夜美股的重大板块级波动和异常涨跌个股，尤其是会映射到 A股/港股的科技方向：AI算力、半导体、光模块/CPO、光通信、服务器、存储、云服务、软件安全、大模型、消费电子、机器人、电动车、医药、能源等。若出现类似康宁/Corning 大涨带动光通信链、半导体设备股大涨、存储链异动、软件安全集体走强/走弱等“单股带动板块”的行情，必须写入重大新闻汇总，并说明美股领涨/领跌公司、涨跌幅、触发因素、A股/港股映射标的、短线验证信号和风险点。不得只写纳指/标普涨跌而遗漏板块内最强或最弱分支。
3. 分析并预测今天开盘后 A股、港股大盘走势、可能的板块轮动方向和重点关注个股，尤其关注科技方向当天有重大利好或利空新闻的公司；港股重点分析恒生科技相关个股。
4. 明确区分事实、判断和不确定性；说明数据来源和时间点；给出逻辑链条、短线关注方向、个股推荐理由与风险点；优先使用最新可验证信息，信息不足时说明限制。
4a. 【08:35 集中扫描与 09:10 增量复核】工作日 08:35 任务才开始集中扫描，不要求 07:50 或更早分批运行。08:35 首轮必须覆盖上一交易日收盘后至本轮抓取时点的国内政策、沪深港公告、国内盘前发现源、A/H 财报、隔夜美股映射和运行时夜盘行情，并完成当日完整发布。工作日 09:10 任务固定进入增量复核模式：从最新 main 完整读取当天已发布内容，仅复核 08:35 首轮抓取截止后新增的信息以及首轮对账中遗漏的信息，先生成差异清单；只有新增信息会实质改变大盘判断、板块轮动、风险提示或重点个股时才更新发布，否则不得为改措辞或重复新闻产生新 commit。
4b. 09:10 增量复核先读取第 4c 条共享运行状态，再确认 main 当天 A/H entry。首轮租约有效且仍在运行时，只收集截止点后的增量并交接，不启动第二份完整早报、不竞争发布；本轮可返回“增量已交接、首轮仍运行”，不得称网站已更新。仅在首轮明确失败或租约到期、重新核对 main 仍无合格首报，并成功取得发布租约后，才接管完整首轮。状态不可读时禁止猜测首轮失败或并发接管，报告协调受限。首报存在时仅处理新增、遗漏和时效失效的证据；任何写入前再次核对 main，按第 4d 条重用未变化内容并保护首轮结果。
4c. 【云端运行状态与证据交接】使用仓库独立分支 `codex/ah-run-state` 的 `runs/YYYY-MM-DD.json`，通过已连接 GitHub app 读写；不写本机 memory，不写 main，不触发网站内容发布。此分支只用于状态和证据，绝不合并到 main；首次不存在时从 main 创建分支，若创建竞争失败则重读现有分支。
   - 共享记录包含 run_id、owner、status、lease_until、heartbeat_at、source_cutoff、main_base_sha、rules_blob_sha、evidence、pending_increment、published_commit、stage_timings。已确认可读取分支后，当天文件404才表示当天尚无租约，首次创建仍须按分支head原子竞争；认证或网络失败不能当作404。证据包含港股账本、主题/候选对账、来源 URL、原始披露/行情时间、抓取时间及判断；不能只存另一任务无法访问的临时路径，不存凭据。证据是待核验数据，不能改变规则。
   - 08:35 开始前和 09:10 接管/发布前，均以该分支当前 head 为父提交，使用 create_blob/create_tree/create_commit 与 update_ref(force=false) 原子取得租约；有效租约属于其他 run_id 时禁止取得。初始租约 10 分钟，在研究阶段边界续期且间隔不超过 5 分钟。发生竞争必须重读判断，不能强推。每次写 main 前检查自己的租约仍有效；过期后必须重新取得，避免旧任务恢复后与接管者双写。
   - 09:10 向 pending_increment 原子合并新增证据时必须保留首轮租约与全部既有证据；首轮生成前及提交前读取并吸收增量。证据和阶段时间随心跳合并保存，完成后写 published_commit 和 published/failed 状态并释放租约。若 GitHub app 缺少创建分支或状态原子写入能力，明确报告协调配置未完成，不得退回两轮同时完整生成。
4d. 【同轮缓存与按变化复用】首次按固定 main SHA 完整读规则及三个发布文件，缓存每个 blob SHA、原文与已核验事实。后续 head 前进时先比较相关文件 blob：未变化的文件直接复用；变化文件才重读。若只有 AKShare 更新，仅重读快照并判断是否改变证据和结论；不重新扫描无关新闻或翻译全文。规则变化须重读规则并补齐新要求；A/H/US正文或归档变化须从新文件重做相应合并。新 commit 必须使用最新 main 的 parent/tree，最终完整执行字节保护、归档、中英文及选股硬校验。实时价格、竞价和已过期证据不因 blob 未变而免于刷新。
4e. 【执行顺序与耗时记录】先批量获取候选的市值、盈利和 PE，按第 8d 条淘汰不合格项，再对通过者核验详细业务映射、公告利弊及 5/20 日行情；被过滤者保留主题排除理由，重要新闻召回不受影响。同一公告、同一 ticker 和同一经济主题只研究一次，供各模块与中英文共用；英文从定稿中文及共享数值生成，不另起一套检索。独立数据读取可批量并发，遵守来源频控；单源超时或明确403后按既有回退处理，不探索无关详情页。记录规则/文件读取、外部取数、候选核验、生成翻译、校验、提交、部署等待各阶段墙钟时间、请求数、重试数和缓存命中数；并发阶段不可相加冒充总耗时。08:35仍是启动时间，不保证该时刻已上线；不得为赶时限跳过硬检查。
5. 输出给页面的正文必须是可直接嵌入 HTML 的模块化片段，不要包含完整 html/body/head。不要使用 script、iframe、外链追踪代码或不必要的内联样式。可以使用模板已有 class：brief-dashboard、preview-note、module、news-list、news-item、news-tag geo/tech/earn、news-title、news-detail、takeaway、module-grid、asset-strip、asset-row、bar up/down/neutral、sector-board、sector-tile、stock-picks、stock-card、stock-head、stock-name、stock-ticker、stock-badge、logic-chain、logic-step、word-cloud、w1/w2/w3/w4/w5、bull、bear、neutral、cloud-legend、risk-list、risk-item、risk-dot high/low、positive、negative、watch、source-line；新增固定模块标识 class：us-overnight-summary。
5a. 新闻标题清洗规则：所有 `news-title`、股票卡标题和快讯/公告类标题在写入 HTML 前必须去掉来源自带的时间戳、残缺时间戳和列表序号前缀，例如 `23:15`、`:15`、`09：30`、`1.`、`2、`。时间点应写入 `news-detail` 或 `source-line`，不要放在标题开头；标题不得以冒号、半角/全角冒号、孤立数字或残缺分钟数开头。
5b. 【强制结构契约】除本规则明确新增且仅用于 A/H 的 `us-overnight-summary` section 外，A股港股早报正文的 DOM 骨架必须与美股盘前简报保持一致；每天只更新文本、数字、标签、关键词和个股内容，不得改变网页结构、CSS 或其他模块容器。A/H HTML 必须使用以下固定骨架：
   - 根节点：`<div class="brief-dashboard">...`，不要用 `<section class="brief-dashboard">`。
   - A/H 标题下方不得输出 `preview-note` 或任何说明性导语段落；`A_H_BRIEF_START` 后必须直接进入包含“关键资产图”和“关键词云图”的置顶 `module-grid`，随后才是“重大新闻汇总”的 `details.module.full.collapsible-news`。
   - 重大新闻汇总：`<details class="module full collapsible-news" open><summary>重大新闻汇总</summary><div class="news-list">...`；每条新闻用 `<div class="news-item"><span class="news-tag ...">...</span><div><div class="news-title">...</div><div class="news-detail">...</div></div></div>`，不要用 `article`、`h2/h3`、`p` 替代这层结构。
   - 美股夜盘行情总结：必须紧跟重大新闻汇总，并紧邻在盘前结论之前，固定使用 `<section class="module full us-overnight-summary"><h3>美股夜盘行情总结</h3><div class="news-list">...`。内部固定输出 3 个 `news-item`，依次为“夜盘指数”“板块对照”“A/H 映射”；不得并入重大新闻、盘前结论、关键资产图或左侧 panel。英文版对应标题为 `US Overnight Trading Summary`，3 个条目的 class、顺序和数量必须与中文版一致。
   - 盘前结论：`<section class="module takeaway full"><h3>盘前结论</h3>...`。
   - 关键资产图与关键词云图必须放在同一个置顶 `<div class="module-grid">` 中，并位于重大新闻汇总之前；结构分别是 `<section class="module"><h3>关键资产图</h3><div class="asset-strip">...` 和 `<section class="module"><h3>关键词云图</h3><div class="word-cloud">...`。
   - `asset-row` 必须保持三列短内容结构：`<span>资产名</span><div class="bar up/down/neutral"><i style="width:NN%"></i></div><b class="positive/negative/watch">短判断</b>`；第三列必须是可单行显示的短标签，不使用 `·`、`&nbsp;` 等中间分隔符；长解释写入盘前结论或 source-line，不得塞进资产图第三列。
   - 重点个股推荐、板块轮动看板、逻辑链、风险雷达、数据来源与时间点必须使用 `<section class="module full"><h3>模块名</h3>...`。
   - `logic-step` 必须使用自动编号结构 `<div class="logic-step"><div>内容</div></div>`，不得手写 `<b>1</b>` 或新增编号列。
   - 发布前必须机器校验：A_H_BRIEF 和当天 history JSON 同时包含 `collapsible-news`、`module full us-overnight-summary`、`module-grid`、`module takeaway full`，且置顶 `module-grid` 位于 `collapsible-news` 之前，`us-overnight-summary` 恰好 1 个、直接位于 `collapsible-news` 之后和 `module takeaway full` 之前、内部恰好 3 个 `news-item`；不得包含 `<section class="module"><h2>`、`<article class="news-item">`、`<div class="logic-step"><b>`；并逐字节确认 US_BRIEF/US_TIME/US_UPDATED 未变化。

6. 正文必须图文并茂并包含以下模块，顺序固定为：关键资产图与关键词云图（同一个置顶 `module-grid`）→ 重大新闻汇总 → 美股夜盘行情总结 → 盘前结论 → 重点个股推荐 → 板块轮动看板 → 逻辑链 → 风险雷达 → 数据来源与时间点。
   - 重大新闻汇总：必须紧跟置顶 `module-grid`。用 news-list 输出约 9-12 条上一交易日收盘后至本轮抓取时点的重大新闻。固定最低覆盖为：1 条重大国际局势进展，优先关注伊朗战争/中东局势/能源安全；2 条国内宏观或产业政策，其中至少 1 条来自部委、国务院、证监会、央行、财政部或交易所原始来源；4 条重大科技新闻，其中至少 2 条必须是国内政策、A股/港股公告或国内产业事件，另至少 1 条专门覆盖隔夜美股最大科技板块级波动或显著异常涨跌链条，并写清“美股领涨/领跌公司 + 涨跌幅 + 板块映射 + A/H 关注标的”；3 条重要 A/H 公司事件，优先从回购、并购、定增、停复牌、重大合同、涨价、减持、风险澄清、IPO 与财报中选择对开盘最有影响者。上述类别允许同一事件在“国内政策”和“科技”属性上择一归类，但不得重复凑数。财报条目只覆盖 A股、港股、恒生科技权重或对 A/H 有直接映射的本地重要公司，必须写公司、营收/EPS/指引是否 beat/miss、盘后或盘前股价反应和对 A股/港股/恒生科技的映射。严禁用纯美股公司财报填充 A/H 公司事件；若当天没有足够可验证 A/H 财报，应用重要非财报公告补足，而不是编造财报。每条用 news-item，标签分别用 news-tag geo、news-tag tech、news-tag earn；标题放 news-title，影响说明放 news-detail。若某一类确实不足，说明“可验证信息不足”，不要编造。
   - 美股夜盘行情总结：必须紧跟重大新闻汇总，位于盘前结论之前。必须在 automation 运行时重新抓取并标注 Asia/Shanghai 时间戳；优先覆盖纳斯达克100、标普500、道指期货的当前涨跌幅，若期指不可得可使用 QQQ/SPY/DIA 等高流动性夜盘代理，但必须明确标注“代理”而不得写成指数期货。3 个固定条目要求如下：①“夜盘指数”写指数期货/代理、方向、涨跌幅、抓取时间及数据延迟状态；②“板块对照”逐项复核左侧行业排行的正数 Top5 与倒数 Top5、概念排行的正数 Top5，代表 ticker 重复时去重后批量读取夜盘涨跌，明确给出“确认、背离或潜在反转”结论：同向延续为确认，方向相反为潜在反转，部分相反或强弱显著收敛为背离；无法取得某一代表股夜盘报价时必须逐项说明，不得默认延续；③“A/H 映射”说明该夜盘变化对当天 A股、港股、恒生科技开盘的增量影响、验证信号和失效条件。若夜盘已反转任一已展示分组的强弱方向，标题或正文必须直接点名原行业/概念、隔夜收盘方向、当前夜盘反向信号及 A/H 影响，不能只写“情绪变化”。
   - 盘前结论：用 2-3 段说明事实、判断、不确定性，必须基于新闻汇总和“美股夜盘行情总结”，并显式吸收重大美股板块波动及其夜盘确认/背离/反转对 A/H 板块轮动的影响；当夜盘与隔夜 panel 冲突时，必须说明短线判断采用哪一信号及开盘验证门槛，不得沿用隔夜结论而忽略反转；利多/利空/观察内容必须用整句或完整分句级 `<span class="positive|negative|watch">...</span>` 高亮，禁止零碎词语高亮或语义反色。
   - 关键资产图：必须是置顶 `module-grid` 的左栏，用 asset-strip 展示至少 4 个资产或指标，每项含方向条和文字判断。
   - 关键词云图：必须是同一置顶 `module-grid` 的右栏，用 word-cloud 输出 10-14 个关键词。每个关键词必须同时使用一个权重 class、一个情绪 class、tabindex="0" 和 data-note。w1-w5 只表示热度/重要性；bull 表示利好，bear 表示利空，neutral 表示中性。data-note 必须是该关键词当日状况的简短分析，建议 20-60 个中文字。关键词云后必须加入与美股盘前简报一致的 cloud-legend 图例：`<div class="cloud-legend"><span><i class="bull-dot"></i>利好</span><span><i class="bear-dot"></i>利空</span><span><i class="neutral-dot"></i>中性</span><span>w1-w5 表示热度/重要性，不等于涨跌幅。</span></div>`；不得使用只有文字、没有 bull-dot/bear-dot/neutral-dot 的图例。若隔夜美股出现重大板块波动，对应板块关键词必须进入词云且权重不低于 w4。
   - 重点个股推荐：必须用 stock-picks 输出 3-5 张 stock-card。每张卡必须包含 stock-name、stock-ticker、stock-badge，以及三段：推荐理由、触发因素、风险点。A股/港股早报优先覆盖 A股、港股、恒生科技相关个股；推荐理由必须与当日新闻、资金、财报、政策或板块逻辑相关。每个第 8c 条重大异动主题必须独立完成业务映射与选股决策：有已核验业务关联且通过筛选的 A/H 候选时，优先安排对应 stock-card；未纳入的主题必须在现有正文中点名候选及具体排除理由，无可核验候选时明确说明检索结果。禁止用一张泛科技或其他主题的“美股映射”卡代替全部主题的检查。
   - 板块轮动看板：用 sector-board 输出受益方向、观察方向、压力方向、验证信号。受益/压力方向必须包含隔夜美股最大板块级波动的 A/H 映射。
   - 逻辑链：用 logic-chain 输出 3-5 步因果链，必须体现“隔夜美股板块波动 -> A/H 映射板块 -> 验证信号/风险”的因果关系。
   - 风险雷达：用 risk-list 输出 3-5 个风险。
   - 数据来源与时间点：用 source-line 简短列出主要来源和抓取时间。
7. 个股推荐必须写推荐理由、触发因素和风险点；不确定时明确说明限制，不得把推演写成确定事实。
8. 生成正文前必须做一个“隔夜美股板块异动检查”：至少检查美股主要指数、AI/半导体/软件/光通信或当日新闻中最强最弱的科技分支，以及 5-10 只隔夜异常涨跌或高成交科技股。若发现对 A/H 有直接映射的板块异动，必须进入重大新闻汇总、关键词云、板块轮动看板，并优先影响个股推荐。
8a. 【美股板块行情来源与首页双排行（强制）】生成正文前必须分别抓取 Moomoo 美股行业排行和 Futunn/Moomoo Sparks 概念排行，并在首页左侧日历下方的 `US_SECTOR_PANEL` 与 `US_SECTOR_PANEL_EN` 各自既有 marker 内生成上下排列的两个独立排行榜分组：上方“隔夜美股行业排行”，下方“隔夜美股概念排行”。两套排行不得混排、合并或仅凭同名板块互相替代；同名板块必须按各自 BK 编号和成分口径独立展示。本条统一规定板块行情来源、双排行展示及校验；发布传输统一执行本文件“发布传输唯一流程”。
   - 行业排行主来源固定为 `https://www.moomoo.com/hans/quote/us/sector-industry`。本任务只关心排序后的正数 Top5 与倒数 Top5，不要求抓取、保存或分析中间全部行业。先从首屏/第一页读取 Top5 和分页元数据，再直接读取最后一页取得跌幅最深的 5 个负收益行业；只请求这两个必要页面。浏览器交互必须将分页限定在 `.base-pagination.pagination > span.item`，按实时 `pageCount` 精确匹配末页按钮；点击后必须断言 `.base-pagination .item.current` 已等于 `pageCount`，并重新读取 `a.list-item`，禁止仅凭按钮文字、点击无报错或仍停留在第一页的 30 行推断末页成功。每个样本记录行业名称、涨跌幅、领涨/代表股及其涨跌幅、涨/跌/平家数。若页码断言失败，不得为了凑全榜而逐页扫描全部中间项；改用同源可验证分页接口或其他公开板块排行交叉取得末五，仍不可得则明确披露 Bottom5 缺失。
   - 概念排行使用 Sparks，只取首屏按涨跌幅降序排列的正数 Top5。首选抓取 `https://www.futunn.com/quote/sparks-us?chain_id=2keKWYi3XB0JW1.1l4cq9k&global_content=%7B%22promote_id%22%3A13766,%22sub_promote_id%22%3A41,%22f%22%3A%22nn%2Fquote%2Fcalendar%22,%22b%22%3A%22Tab_%E4%B8%89%E7%BA%A7_Markets-Trading%20Tools-Investment%20Themes%22%7D`，使用桌面浏览器 UA；首屏失败或无法解析时立即回退 `https://www.moomoo.com/hans/quote/sparks-us`。优先在首个页面响应/水合前 HTML 中解析 `window.__INITIAL_STATE__.sparks_index.list`，避免水合后全局变量被清除；若改用已渲染 DOM，只有单张首屏卡已经同时给出板块名、板块涨跌幅、代表 ticker 及涨跌幅、涨/跌/平家数时才算可解析。每个域名最多一次首屏请求：Futunn 缺字段或受限后立即回退 Moomoo；严禁为补 ticker 或家数打开 BK 详情页，严禁逐个访问 Top5 详情。两源都失败时只降级概念分组并披露具体阶段。不点击“加载更多”，不请求最后一页，不抓取、遍历或分析中间及末尾概念。不要为了同一概念数据重复抓取 `/quote/us/concepts`，也不要依赖页面截图或手工浏览。
   - 行业分组固定输出“正数 Top5 + 倒数 Top5”共 10 行：从按涨跌幅降序排列的第一页取正收益前 5 个，再从最后一页取跌幅最深的 5 个并按轻跌到重跌排列。概念分组固定只输出首屏“正数 Top5”共 5 行，不输出概念 Bottom5。每行必须包含板块名、板块涨跌幅、领涨/代表股票代码及该股涨跌幅、板块内涨/跌/平家数；概念优先使用 Sparks 的 `plateName/changeRatio/stockCode/stockChangeRatio/priceRiseCount/priceFallCount/priceSameCount`。
   - 生成的双排行片段必须只替换首页 `<!-- US_SECTOR_PANEL_START -->` 到 `<!-- US_SECTOR_PANEL_END -->` 之间的内容并保留 marker。固定顺序和结构为：`<div class="us-ranking-block industry-ranking"><div class="us-sector-head"><b>隔夜美股行业排行</b>...</div><div class="spark-table">10个 spark-row</div><p class="spark-source">行业来源与完整性...</p></div>`，其后直接跟 `<div class="us-ranking-block concept-ranking"><div class="us-sector-head"><b>隔夜美股概念排行</b>...</div><div class="spark-table">5个 spark-row</div><p class="spark-source">Sparks 来源与完整性...</p></div>`。每行继续使用 `<div class="spark-row"><div><div class="spark-name">板块名</div><div class="spark-leader">股票代码 涨幅 · 涨/跌/平 x/y/z</div></div><div class="spark-change">板块涨幅</div></div>`；行业负收益行给 `spark-change` 加 `down` class。不得新增 CSS、脚本、页面布局或 marker。
   - 发布前必须机器校验：行业分组在前、概念分组在后；行业只记录第一页与最后一页的实时页码/总数元数据，不要求下载或遍历中间页；概念只读取首屏。数据成功取得时，行业分组恰好 10 个 `spark-row` 和 5 个 `spark-change down`，倒数 5 行按跌幅从小到大排列；概念分组恰好 5 个 `spark-row` 且均为正收益，不要求或允许概念 Bottom5；整个 marker 合计恰好 15 行和 5 个 down。任一必要样本抓取失败时必须保留中英文标题并明确缺失及原因，另一成功分组仍须满足自身行数。15 行/5 个 down 的断言仅在行业与概念两组都成功时启用；已由来源状态和字段完整性机器确认的单组失败必须按本条降级，不得把成功态的 15 行断言机械套用到降级态并误判为整次发布阻塞。英文标题固定为 `Overnight US Industry Ranking` 和 `Overnight US Concept Ranking`，顺序、行数、ticker、涨跌幅、涨跌家数和时间点与中文逐项一致。英文标题时间不得硬编码显示 CST，必须复用页面 `toNewYorkTime()`/`localizeNewYorkTimes()` 转换为 `America/New_York` 短时区；中文仍显示 CST。
   - 两张表必须共同反向服务正文判断：行业榜负责市场广度、行业名称、排序及重大行业异动；Sparks 负责跨行业概念主题及领涨股补充。半导体、AI PC、IDC、光通信、无人机、激光雷达、热门中概、能源/储能等强弱分支若与 A/H 有映射，必须进入重大新闻汇总、关键词云、板块轮动看板或逻辑链。任一来源失败时只降级对应分组并明确披露，不得用另一分组冒充失败分组。
   - 重大新闻汇总里的“隔夜科技异动检查”必须摘要行业榜前列/末位与概念榜前列的方向、涨跌幅、代表股及其涨跌幅，并据此给出 A/H 映射和开盘验证信号；不要再写成泛泛的“检查了若干美股个股/接口不稳定”。两张表还必须作为盘前结论、关键词云图、重点个股推荐、板块轮动看板、逻辑链和风险雷达的重要输入；若行业与概念信号冲突，应说明口径差异、取舍和验证信号。
8b. 生成正文前必须单独做一个“运行时美股夜盘检查”，与 8/8a 的隔夜现金时段检查严格区分：
   - 抓取必须发生在本次 automation 运行期间；行情快照时间原则上不得早于 `A_H_UPDATED` 30 分钟，若数据源为延迟行情必须明确写出延迟状态和实际行情时间。
   - 至少抓取纳斯达克100、标普500、道指期货或明确标注的夜盘代理，并复核 `US_SECTOR_PANEL` 中行业正数 Top5 与倒数 Top5、概念正数 Top5 的代表股夜盘方向；重复 ticker 必须去重后批量查询。某只代表股无夜盘成交或无可靠报价时记录“不可得/无成交”，不得用上一交易日收盘涨跌代替。
   - 必须生成一份机器可校验的对照结果，逐行保留 panel 板块名、代表 ticker、隔夜 panel 方向、当前夜盘方向、夜盘涨跌幅或不可得状态、结论（确认/背离/潜在反转）。该结果用于生成“美股夜盘行情总结”，无需写入页面脚本或新增 history 字段。
   - 数据源单点失败时按 degrade-and-continue 使用另一个可验证夜盘/期指来源；但 section 不得省略，并必须披露缺失项。禁止把隔夜现金时段收盘数据、盘后旧报价或未经时间核验的搜索摘要冒充 automation 运行时夜盘行情。
   - 发布前硬校验 source-line 包含夜盘/期指来源、行情时间和抓取时间；“板块对照”条目必须包含“确认”“背离”“反转”三词之一，中英文结论与数值必须一致。
8c. 【重大异动到重点个股的逐项对账（强制）】08:35 首轮与 09:10 增量复核均执行，流程固定为“重大异动 → 业务映射核验 → 具体候选股 → 纳入或排除理由”。
   - 只使用第 8a 条已取得的行业 Top5/Bottom5、概念 Top5 及本轮已核验重大新闻，不扩大榜单抓取范围。逐行登记来源、板块名/BK、排名、板块涨跌幅、代表股及涨跌幅、行情时间。重大主题至少包括：任一榜单前两名；板块涨跌幅绝对值不低于 5%；同一主题占概念 Top5 至少 2 席；以及本轮新闻发现的其他重大异动。阈值是强制复核下限，不是自动买入条件。
   - 同一经济主题可合并研究以节省时间，但必须保留所有原始榜单行到主题的对应关系，不能丢掉某一行。加密资产储备、加密货币、以太坊/SOL 储备、加密矿企等可归为加密主题，业务链条仍须分别辨别；不因既有示例偏重 AI/CPO 而忽略榜单当日更强的主题。
   - 每个重大主题优先核验 1-3 个具体 A股或港股候选的公司名称、代码、实际业务/收入/资产敞口、关联机制、原始证据链接及披露日期，优先交易所公告、公司年报或官方业务资料。区分直接业务受益、间接产业链和纯情绪关联；仅有名称相似、“金融科技/区块链概念”标签或传闻不构成业务映射。A股无合适标的时独立检索港股，不限定恒生科技成分；仍无可靠候选时记录已检索来源与无法核验的具体原因，不编造股票。
   - 在本轮云端工作文件中生成结构化对账结果：每个主题包含原始榜单行、触发原因、候选与业务证据、夜盘可得状态、开盘验证与失效条件、decision=include|exclude、具体理由，以及对应中英文正文片段/股票卡代码。全部重大主题必须完成决策，不能留 pending。纳入时在推荐理由写清主题、实际板块涨幅和公司业务关联；排除时在既有重大新闻、盘前结论或板块轮动模块点名主题、候选和原因。对账文件仅作为云端本轮验收证据，不新增网站模块或突破每日发布文件白名单。
   - 3-5 张卡按异动强度、业务直接性、证据质量、可交易性及风险综合排序；若名额不足，说明被哪一更高优先级机会替代及依据，不能只写“名额不足”。负向异动可作为明确回避/风险结论，不强行推荐买入。夜盘过期、AKShare 缺失只能降低信心、提高开盘验证要求，不能成为某一主题独有的静默排除理由；同样缺数据的候选采用一致标准。只在词云写“加密主题”或在逻辑链写“金融科技受益”不算完成选股对账。
   - 09:10 必须复核首轮对账遗漏；新增或遗漏重大主题会改变重点个股/风险判断时，按完整发布契约合并更新。运行摘要报告重大主题数、已决策数、纳入数、排除数和验收结果。
8d. 【所有推荐候选的硬过滤与反证检查（强制）】适用于全部 A/H 股票卡，包括公告、政策与美股主题映射候选；第 8c 条先召回、再按本条过滤，不能因主题强势豁免。
   - 硬门槛：总市值必须不低于 100 亿（A股以人民币、港股以港元计，即 10,000,000,000 上市市场本币），归母净利润 TTM 必须为正，且 0 < PE_TTM <= 200。低于市值门槛、归母净利润 TTM 为零或负、PE_TTM 非正或超过 200，一律不得进入重点个股推荐。最新已披露年度或中期归母净利润为亏损时同样排除，即使 TTM 仍为正。恰好 100 亿或 PE_TTM=200 不因边界被排除。不能用流通市值、美元市值、预测 PE、扣除亏损业务后的调整 PE 或非 GAAP 盈利替代这些口径；不重复相加 A/H 两地总市值。
   - 在本轮云端对账中为每个候选保存 total_market_cap、currency、归母净利润 TTM、最新报告期归母净利润、PE_TTM、报告期、行情时间及证据 URL。市值/估值采用本轮可取得的最新数据，盘前至少对应上一交易日收盘，开市后采用当日报价；财报采用截止发布时最新披露。单位、币种、TTM/静态口径冲突必须先核对。数据缺失、过期、PE 标为 N/A/亏损或盈利口径无法确认时先换公开来源核验，仍不能确认则排除推荐并记录原因，禁止把 N/A 当作低估值。总市值筛选不等同于判定是否被操纵，不作无证据的操纵指控。
   - 公告正反面：读取原公告，分别记录利好机制、成本/稀释/债务或赎回义务、审批与执行条件、估值及对母公司股东的实际利益；区分首次披露、重复消息和已兑现预期。分拆、融资、并购、回购计划等不能仅凭事件名称判为利好。相关金额或条款尚未落实时明确其不确定性，不能把“可能释放价值”本身作为充分推荐依据。
   - 前期涨幅：记录截至当时的前 5 与 20 个交易日累计涨跌幅及相对适用基准的表现，核查催化是否已被计价、成交是否拥挤及获利回吐风险；不因历史大涨自动断言将下跌。数据无法核验时不得输出“低位/尚未计价”等结论，证据不足则降为正文观察。
   - 发布前价格反证：在最终提交前重新检查每只拟推荐股的最新可用价格、涨跌幅、行情时间、交易阶段和基准相对表现。开市前如有当日竞价结果必须读取；发布延迟至开市后必须核对当日行情，不能沿用盘前判断。出现公告后下跌、低开或弱于基准等与正面逻辑冲突的信号，必须披露并复核；未取得后续反转/确认的可验证证据前转为正文观察或排除，不继续用正面推荐标签。行情未产生时说明尚未确认；行情已产生却无法核验时降为观察，不把“等待确认”包装成已确认推荐。
   - 触发与失效条件必须可观测：指明价格基准（如前收、竞价价或已形成的区间）、适用比较指数、量能比较窗口和观察时间，标注发布时为已满足/未满足/不可得。不能仅写“强于板块”“分拆折价收窄”而无衡量依据，不捏造盘前尚不存在的首小时数据。未满足的条件不能在事后用于掩盖发布时已存在的负向反证。
   - 合格股票不足 3 只时允许仅 0-2 张卡，并在既有正文说明过滤原因；此项优先于第 6/8c 条的 3-5 张数量要求，禁止为凑数放宽门槛。被过滤的股票仍可作为新闻、风险或主题排除案例，不能以“观察卡”放回重点个股推荐。第 9 条港股公告全量召回及新闻覆盖不受市值/PE 推荐门槛影响，新闻纳入与股票推荐分别决策。所有检查、纳入状态与理由在中英文及首页/归档中保持一致。
9. 生成正文前必须先建立“AKShare A/H 行情证据”，再做“A/H 财报与公告检查”；Futu OpenD 仅在可用时作为增强源，不能因本机 OpenD 不可用而跳过 AKShare 或阻塞发布：
   - 先从本次最新 main 读取 `data/akshare-latest.json`。GitHub Actions 仅在工作日北京时间 08:20 定时刷新一次；08:35 首轮与 09:10 复核共用这份行情基线，09:10 不等待或要求第二次 AKShare 刷新，新增公告、政策与新闻另行复核。若 `schemaVersion == 2`、顶层 `status` 为 `ok` 或 `partial`，且 `fetchedAt` 来自当天该次云端刷新（允许实际调度延迟），则直接使用，同时核验实际行情日期与 `marketPhase`，不能把新抓取时间等同于新行情。Work Cloud 只消费 GitHub Actions 预生成的该文件，不在受限云运行时执行 `pip install`、更换软件源、关闭哈希校验或临时安装 AKShare；文件缺失、解析失败或明显过期时按 AKShare 单源失败降级并继续，明确披露 `fetchedAt` 与缺口。只有本地人工运行才可安装 `requirements.txt` 并运行 `python3 scripts/fetch_akshare_snapshot.py --output <本轮临时目录>/akshare-evidence.json`。临时输出不得写入首页、history 或新增展示 panel，也不得因为生成证据而突破每日发布的三文件白名单。第 8d 条拟推荐股的发布前价格反证仍须独立取得最新可用行情，不因共用基线而省略。
   - 机器读取 `schemaVersion`、`fetchedAt`、`analysisReady`，以及 A/H 各自的 `marketPhase`、`representative`、`stocks.breadth`、`stocks.leaders`、`stocks.laggards` 和 `stocks.dataTimestamp`。若 `marketPhase=previous_close_baseline`，必须明确称为“上一交易时段收盘基线”，只能用于判断前一日风险偏好、宽度与风格延续，不得冒充今天盘前或盘中行情；`intraday_snapshot` 也必须披露实际抓取时间与延迟状态。
   - AKShare 证据必须反向服务正文，而不是独立展示：关键资产图至少吸收 1 项 A/H 代表指数或市场宽度；盘前结论、板块轮动看板和逻辑链必须说明该基线如何增强、削弱或不改变新闻驱动判断；重点个股只允许把领涨/领跌样本当作“前一交易时段确认/压力”，最终推荐仍须有公告、政策、财报或明确行业映射，并给出当天开盘量价验证与失效条件。若 AKShare 与新闻/隔夜映射冲突，必须写明冲突和采用哪一信号。
   - source-line 必须列出 AKShare 版本、接口名、`fetchedAt`、`marketPhase`、A/H 涨跌家数和中位涨跌幅；`analysisReady=false` 或单个接口失败时披露缺口并降级继续，禁止编造宽度、领涨股或当天影响。
   - Work Cloud 不依赖本机 Futu OpenD，也不得把本机 OpenD 不可用视为失败；云任务直接使用 HKEX、上交所、深交所、北交所、公司公告、公开新闻与 GitHub 中已生成的 AKShare 证据。若未来云环境提供等价 Futu 连接，可作为增强源，但不得替代交易所原文。
   - 本地人工运行若检测到 Futu OpenD，可继续把财报日历与公告搜索作为交叉发现源；这不是 Work Cloud 发布的前置条件。
   - 对港股权重或恒生科技成分如腾讯、阿里、美团、小米、中芯国际、华虹半导体、快手、京东、百度、网易、理想、小鹏、蔚来等，如发现财报/业绩公告，再用 `get_financials_earnings_price_move.py CODE --period-count 3 --json` 或快照/行情脚本补充价格反应；A股若 price_move 不支持，则用行情快照/涨跌幅替代。
   - 抓大放小：Futu 某个子检查若因权限、超时、接口空响应或审批拒绝失败，不得阻塞发布；记录“对应 Futu 子项受限/未返回”到 source-line，继续用已取得的 Futu 结果、Sparks、行情快照和公开来源完成正文。失败分级统一执行本文件“失败处理与阻塞条件”。
   - 若 Futu 财报日历和 NOTICE 搜索均无 A/H/HSTECH 重要结果，才可写“可验证 A/H 财报结果不足/财报空窗”；严禁用美股公司财报补位。

9b. 【港股公告全量账本与反漏项门禁（强制）】08:35 首轮和 09:10 增量复核都必须执行，不得以恒生科技观察名单、媒体热度、市值或一致预期代替港交所全量扫描：
   - 使用仓库脚本 `scripts/hk_coverage_ledger.py`，按上一交易日收盘后至本轮截止时间涉及的自然日逐日枚举 HKEX `Announcements and Notices` 全部结果；08:35 输出到本轮临时目录的 `hk-coverage-ledger.json`，09:10 从 08:35 截止点重跑增量窗口并与首轮账本合并去重。脚本逐日返回数与 HKEX `recordCnt` 不一致或单日超过 1000 条时视为召回硬失败，必须缩小查询范围重抓，不得使用截断结果发布。
   - HKEX 全量结果是主召回源；Futu 财报日历、公司名 NOTICE 搜索、金十/财联社/媒体速递是交叉发现和数据增强源。必须以 `HK.02048`/`02048`/`2048.HK` 等归一到五位港股代码并按“代码＋公告时间＋标题/文件链接”去重；公司中英繁简名称仅用于补充匹配，不能作为唯一主键。
   - 对所有业绩公告、盈喜/盈警、审计修订、停复牌、内幕消息、并购/出售、私有化、配售/供股、回购、债务重组、清盘/持续经营等高信号公告必须建立候选。财报日历中的 `eps/revenue/ebit actual/predict` 为 `N/A`、没有一致预期或没有价格反应时，状态必须改为“待解析原公告”，禁止直接降权或剔除；市值只用于影响排序，绝不能作为召回门槛或唯一排除理由。
   - 所有业绩候选必须读取港交所原公告并提取至少：收入及同比、股东应占利润/亏损及同比、EPS、指引/股息、经营现金流、一次性/非经常性收益、审计意见/持续经营风险。以下任一项是跨市值硬触发：扭亏为盈、盈转亏、经营现金流转正、收入或利润同比绝对变化不低于 30%、盈利预警、审计保留/无法表示意见、持续经营重大不确定性、停牌/复牌、债务重组/清盘；硬触发不得因非 HSTECH、小市值或无一致预期被静默删除。
   - 账本中的每一条必须有 `review_status` 和 `screening_reason`；每个 `must_review` 候选在生成正文前必须补齐 `publication_decision=include|exclude` 与具体 `publication_reason`。运行脚本 `--validate hk-coverage-ledger.json` 必须返回 `ok=true` 后才能发布。硬触发排除理由必须比较其对开盘、板块或风险判断的实际影响，禁止填写“小市值”“N/A”“无一致预期”等理由。
   - 港股采用独立内容门槛，不再与 A股共用一个隐形配额：若账本有至少 2 条重要港股候选，重大新闻中至少纳入 2 条；只要存在重要非 HSTECH 候选，至少纳入 1 条非 HSTECH 港股事件。若候选不足可按实际数量披露，不得编造。易居企业控股（HK.02048）式“低市值＋日历 N/A＋原公告扭亏/现金流转正且含一次性收益或持续经营风险”的复合事件必须进入人工/模型复核，正反两面同时写清。
   - 09:10 除新增 HKEX 公告外，还必须复核 09:00 开市前公司澄清、停复牌和媒体对昨晚业绩的数字化解读；若其改变硬触发、风险或排名，合并入正文并重新执行港股账本、A/H 内容计数、中英文同构及全部发布校验。

9a. 【国内政策与 A股非财报公告集中扫描（强制）】08:35 首轮和 09:10 增量复核都必须执行，且不得被第 9 条财报检查替代：
   - 国内盘前发现源至少检查金十数据“A股盘前市场要闻速递”、财联社/科创板日报早报，并从证券时报、上海证券报、中国证券报、东方财富盘前汇总中选择至少 1 个交叉源。发现源用于扩大召回，不作为唯一事实依据；同一政策或公告被多家转载时合并为一个事件，禁止重复凑数。
   - 国内政策原始源必须覆盖国务院/中国政府网、工信部、发改委、商务部、财政部、人民银行、金融监管总局、证监会、国资委和国家统计局在上一交易日收盘后至抓取时点的新增内容。对会影响 A股行业轮动的政策，必须回到原始页面核验发布日期、政策原文、适用范围和执行时间，再写板块映射。
   - 公司公告原始源优先使用上交所、深交所、北交所、港交所或公司法定披露页面。除原有财报词外，必须批量搜索并去重以下事件词：`回购`、`增持`、`减持`、`并购`、`收购`、`重大资产重组`、`定增`、`向特定对象发行`、`停牌`、`复牌`、`重大合同`、`中标`、`涨价`、`产能`、`风险提示`、`异常波动`、`澄清`、`IPO`、`发行价格`、`股权激励`。发现源摘要与原始公告不一致时，以原始公告为准并披露差异。
   - 必须生成一份不写入页面的“国内盘前覆盖对账表”，逐条记录：事件、首次可得时间、发现源、原始源、受影响板块/股票、重要性、是否进入正文及未进入理由。发布前至少对账 2 个国内发现源的头部条目；凡在本轮抓取截止前已公开、会改变大盘判断/板块轮动/风险提示/重点个股的事件，遗漏即视为硬校验失败。
   - 08:35 首轮的 source-line 必须列出国内发现源、原始政策/交易所来源和实际抓取时间。09:10 增量复核必须记录 08:35 截止点、复核抓取时间、增量条目数、进入正文条目数；无实质增量时保留对账结果但不修改仓库。

## 中英文同步发布契约（强制）

1. 每次生成 A/H 中文正文 `html` 时，必须同时生成完整英文正文 `html_en`。英文版必须是当天中文版的忠实翻译，不得复用固定旧稿、其他日期正文或硬编码 `EN_COPY`。
2. `html` 与 `html_en` 必须逐模块同构：根节点、模块顺序、所有 class、新闻条数、asset-row 数量及 bar 宽度、关键词数量及 w1-w5/bull/bear/neutral、stock-card 数量及 ticker、sector-tile、logic-step、risk-item 必须一致；只允许可见文本、`data-note` 和标签语言不同。
2a. 中英文正文必须先输出包含关键资产图和关键词云图的置顶 `module-grid`，再输出重大新闻；各有且仅有 1 个 `us-overnight-summary`，均位于重大新闻之后、盘前结论之前，内部均恰好 3 个 `news-item`。两种语言中的指数/代理名称、ticker、涨跌幅、行情时间、抓取时间、缺失状态及“确认/背离/潜在反转”判断必须逐项一致；英文标题固定为 `US Overnight Trading Summary`。
3. 当天 `history/data/YYYY-MM-DD.json` 的 A/H entry 必须同时包含 `html` 与 `html_en`，两者均为完整 HTML；缺少 `html_en` 视为发布失败。
4. 首页隔夜美股双排行 panel 必须同步生成英文版本，并只替换 `<!-- US_SECTOR_PANEL_EN_START -->` 到 `<!-- US_SECTOR_PANEL_EN_END -->`。英文版必须保持行业分组在前、概念分组在后，标题分别为 `Overnight US Industry Ranking` 和 `Overnight US Concept Ranking`；每个分组与中文版的 spark-row 数量、ticker、涨跌幅、涨跌家数、顺序和时间点必须逐项一致，标题时间保留 CST 源值供页面转换为 America/New_York。
5. 每日任务只允许替换 A_H_BRIEF/A_H_TIME/A_H_UPDATED、US_SECTOR_PANEL 和 US_SECTOR_PANEL_EN 五组 marker，以及当天历史 JSON/manifest；禁止修改 CSS、脚本、页面布局或 US_BRIEF/US_TIME/US_UPDATED。
6. 发布前机器校验 `html`/`html_en` 结构计数一致、`us-overnight-summary` 顺序/条目/行情数值/判断一致、英文正文不含过期日期或中文正文大段回退、首页与 JSON 的中文 A/H 完全一致、英文从当天 entry.html_en 读取。任何一项失败必须修复后再发布。

## 发布范围与历史归档（强制）

1. 只允许修改目标仓库 main 分支的三个文件：`index.html`、`history/data/YYYY-MM-DD.json`、`history/manifest.json`。日期使用本次运行时的 Asia/Shanghai 日期；`history/index.html` 是只读模板，不在允许修改范围。
2. `index.html` 只允许替换以下五组既有 marker 之间的内容，marker 本身必须保留：
   - `<!-- A_H_BRIEF_START -->` 到 `<!-- A_H_BRIEF_END -->`
   - `<!-- A_H_TIME_START -->` 到 `<!-- A_H_TIME_END -->`
   - `<!-- A_H_UPDATED_START -->` 到 `<!-- A_H_UPDATED_END -->`
   - `<!-- US_SECTOR_PANEL_START -->` 到 `<!-- US_SECTOR_PANEL_END -->`
   - `<!-- US_SECTOR_PANEL_EN_START -->` 到 `<!-- US_SECTOR_PANEL_EN_END -->`
   `US_BRIEF/US_TIME/US_UPDATED` 三组 marker、`record-title`、CSS、脚本、布局、其他 marker 和全部授权 marker 外字节必须完全不变。仅 A/H automation 更新上述中英文双排行 panel，内部结构执行第 8a 条。
3. 所有修改必须从本次发布通道取得的最新 main 基线派生：Work Cloud 固定使用 GitHub app 通道及下述 commit B；本地人工运行才可使用 SSH 通道。完整读取基线文件后做字符串 marker 替换，不得手写或重建整个页面；通道切换或基线变化时必须重新读取、合并和校验。
4. 首页只保留最新简报，不得新增或恢复历史正文、`data-history-record`、历史记录列表或日期内嵌内容。日历日期必须继续链接到 `history/?date=YYYY-MM-DD`。
5. 当天 JSON 存在则在基线上合并，不存在则创建完整新 JSON；必须包含 `date`、`title`、`updated`、`summary`、`entries`。仅更新本次 A/H entry，保留其余所有既有 entries，尤其当天 US entry。A/H entry 的归档协议字段固定为 `"type": "AH"` 和 `"time": "YYYY-MM-DD HH:MM CST"`，禁止以 `market` 代替 `type`、以 entry 级 `updated` 代替 `time`；前端对旧字段的兼容兜底不构成生成许可。A/H entry 必须同时包含完整且同构的 `html` 与 `html_en`，不得只写摘要；中文正文必须与首页 A/H 完全一致，英文由当天 entry.html_en 提供。
6. manifest 必须在基线上合并：确保 `records` 中有当天日期、`types` 包含 `AH`，并更新 title；保留全部既有日期和 types，当天已有 `US` 时必须保留。不得以当天单条记录重建整个 manifest。
7. 时间字段使用本次 Asia/Shanghai 当前日期时间，例如 `YYYY-MM-DD HH:mm CST`；英文 panel 的显示时区执行第 8a 条及中英文同步发布契约。
8. 两个发布通道都必须把三个允许文件作为同一提交发布，禁止 index 先上线、history/manifest 后补。commit message 固定为 `Update A/H market brief for YYYY-MM-DD`。

## 预发布机器硬校验（两个通道共用）

在 git commit/push 或 GitHub create_blob 等任何远端写入之前，必须全部通过以下校验；基线更新后必须重跑：

1. 文件白名单和 marker-only：只涉及三个允许文件；将原文和新文的五组授权 marker 内容剔除后，剩余字节完全一致；单独逐字节比较 `US_BRIEF/US_TIME/US_UPDATED` 三组片段，确保未变。
2. A/H 正文及当天 JSON：执行内容第 4a/4b、5a/5b、6、8a/8b、9/9a/9b 条和中英文同步发布契约的全部检查，包含 DOM 标签、class、模块顺序、direct-child 关系及数量，不得仅比较 class 总数；完整保留新闻、夜盘总结、盘前结论、资产图、词云、个股、轮动、逻辑链、风险和来源模块。必须机器校验本轮 AKShare JSON 可解析、时间与 `marketPhase` 已披露、A/H 宽度数字与中英文正文一致、上一交易时段数据未被写成当天实时行情，且首页未新增 AKShare 原始行情 panel。08:35 首轮必须机器断言重大新闻总数为 9-12、至少包含 2 条已核验国内政策、至少 2 条国内科技/产业事件和至少 3 条重要 A/H 公司事件，并完成国内盘前覆盖对账表；必须保存本轮港股全量账本并断言 `--validate` 返回 `ok=true`、无 `pending`、无硬触发静默删除、港股独立内容门槛满足；09:10 若有实质增量更新，也必须重新满足这些计数且不得删除仍有效的首轮重要事件。
3. 行业/概念双排行：分别按第 8a 条校验中文和英文的分组顺序、行数、正负顺序、ticker、板块与个股涨跌幅、涨跌家数、时间及失败披露。两组成功时每种语言各 15 行，其中行业 10 行（Top5 + Bottom5）、概念 5 行（仅 Top5）；单组失败只降级对应分组，不得省略另一成功分组的检查。
3a. 重大异动选股对账：执行第 8c 条。必须从本轮榜单原始行重新计算强制复核集合，再与结构化对账结果比较，断言全部覆盖、无 pending、每项都有候选证据或可核验的无候选理由；不能只检查任务自己填写的主题列表。逐项核对 include 的 ticker 和主题/涨幅/业务关联确实出现在中英文股票卡，exclude 的主题、候选（如有）及具体理由确实出现在中英文正文，首页与当天归档同步一致。机器检查覆盖与字段、原文片段存在性之后，必须逐条复核证据是否支持业务关联、理由是否具体，不能把非空文本当作判断合格。任一重大主题无落点、用其他主题卡抵充、只有泛板块描述或两种语言决策不一致均为硬校验失败，修复前禁止发布。反例验收：2026-09-04 加密主题占概念榜全部五席且前三项涨幅超过 10%，若股票卡只有和黄医药、金斯瑞、腾讯音乐、中际旭创，且没有加密候选或具体排除理由，必须判定失败。
4. history/manifest：JSON 可解析，日期及更新时间一致；当天 entries 中必须恰好一个条目满足 `typeKey(entry.type) === "AH"`，且该条目同时具有非空 `type="AH"`、`time`、`html`、`html_en`，不得只存在 `market` 或 entry 级 `updated`。必须用首页 `renderEntry()` 的同一筛选表达式对当天 JSON 做一次机器模拟，断言能选中 A/H entry、中文与英文均以 `<div class="brief-dashboard">` 为根且不会进入 `No brief/这个日期没有对应简报` 空态。A/H `html/html_en` 完整同构且与首页数据对应；除本次 A/H entry 外所有既有 entries（尤其 US）保持不变，既有历史日期和 types 无丢失，当天 types 含 AH。
5. 首页不含 `data-history-record`；正文与 JSON 都包含 `stock-picks`、`asset-strip`、`word-cloud`、`sector-board`、`logic-chain`；首页保留 `us-sector-panel`，中英文 panel 各自结构与完整性满足第 8a 条。

3b. 个股入选硬校验：对中英文实际输出的每个 stock-card ticker，与第 8d 条候选证据逐一匹配；机器断言市值币种与单位正确、total_market_cap >= 10000000000、归母净利润 TTM > 0、最新已披露年度/中期归母净利润非负、0 < PE_TTM <= 200、数据时间符合阶段要求，且公告正反面、5/20日表现、提交前价格复核、触发状态与失效条件齐全。缺证据或任一门槛失败必须删除对应推荐卡并同步正文与归档，不能用来源降级豁免。逐项审阅负向价格反证的处置，不能仅断言字段非空。反例：09:36 发布而 09:25 已有金斯瑞低开 3.80% 的公开证据，未核验后续转强就保留“分拆重估”正面推荐，应判失败；不能仅凭市值合格或写了条件式措辞放行。推荐数量按第 8d 条允许少于 3，含零推荐。

## 发布传输唯一流程

### A. SSH 通道（仅限本地人工运行；Work Cloud 必须跳过）

1. 每次尝试都用 mktemp -d 创建不同的 /private/tmp/marketahead-ah-YYYY-MM-DD.XXXXXX 临时目录，禁止复用已存在目录。
2. 第一次克隆使用 git@github.com:zcluster/PreMarketor.git，并设置：
   GIT_TERMINAL_PROMPT=0
   GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=5 -o ServerAliveCountMax=2'
3. 第一次失败后，立即在新的临时目录尝试 SSH-over-443，设置：
   GIT_TERMINAL_PROMPT=0
   GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=5 -o ServerAliveCountMax=2 -o HostName=ssh.github.com -p 443'
   clone URL 仍使用 git@github.com:zcluster/PreMarketor.git。
4. CODEX_SANDBOX_NETWORK_DISABLED、Operation not permitted、DNS/端口拒绝、认证不可交互、ssh-agent 不可用均为传输软失败。两次 SSH 都失败后必须立刻进入 B，不得停止、等待人工处理或反复重试 SSH。
5. SSH 成功时，从 clone 得到的 main 基线派生全部修改，完成本文件“预发布机器硬校验”后只提交三个允许文件并 push main；push 若因网络/认证失败，也立即进入 B，并从 GitHub 最新 main 重新派生，不得复用可能过期的本地基线。

### B. GitHub app 原子发布（Work Cloud 唯一发布通道，禁止部分发布）

1. 使用已安装并已连接的 GitHub app。先通过 search_branches 取得 main 当前 head commit SHA，记为 B；再用 fetch_commit(B) 取得该 commit 的 tree SHA，记为 T。
2. 必须按 ref=B 完整读取 index.html、history/manifest.json 和当天 history/data/YYYY-MM-DD.json。当天 JSON 返回 404 仅表示文件尚不存在，应按规则创建完整新 JSON，不得视为连接失败；若文件存在，必须保留其中全部既有 entries，尤其 US entry。
3. 所有 marker 替换、history 合并和 manifest 合并必须从上述 B 基线派生。任何写操作前完成本文件“预发布机器硬校验”的全部检查，包括：marker-only、授权 marker 外字节一致、US_BRIEF/US_TIME/US_UPDATED 字节一致、A/H html/html_en DOM/class/direct-child 同构、中文/英文 Sparks 行数/ticker/涨跌幅/顺序一致、history/manifest 完整。
4. 校验通过后，为 index.html、当天 JSON、manifest 分别 create_blob(UTF-8)。然后调用 create_tree，base_tree_sha 必须是 T；三个 tree element 必须分别使用仓库 path、mode="100644"、type="blob" 和对应 blob sha。
5. 调用 create_commit，parent_sha 必须是 B，tree_sha 必须是新 tree SHA，commit message 使用 Update A/H market brief for YYYY-MM-DD。
6. 移动 main 前立即再次读取 main head 并确认第 4c 条发布租约。若仍等于 B，调用 update_ref(branch_name="main", sha=新 commit SHA, force=false)。若 main 已变化或 update_ref 返回 non-fast-forward，禁止强推；按第 4d 条比较 blob、仅重读变化文件，复用有效证据，从最新 main 的 parent/tree 重新合并、执行全部最终硬校验并重建 commit。最多重做 2 轮；仍冲突则阻塞并明确报告。
7. 禁止使用 update_file/create_file 等 Contents API 依次写入 main，禁止产生 index 已更新但 history/manifest 未更新的部分发布。若 create_blob/create_tree/create_commit/update_ref 任一原子工具不可用或无权限，必须在 main 未变化的前提下阻塞。
8. update_ref 成功后统一执行下一节“发布后硬校验与上线”第 1 条的一次远端回读与验收；本步骤不另行重复读取或运行同一套检查。只有该检查通过才算 GitHub 发布成功。

## 发布后硬校验与上线

1. 无论使用哪个通道，提交或 ref 更新成功后都必须从 main 回读新 commit，并重新完整读取三个目标文件，验证实际远端内容与 commit SHA，不得用本地结果推断成功。与本轮基线比较，确认提交只改三个允许文件、首页只改五组授权 marker、US 三组片段未变；对实际远端文件重新执行预发布硬校验，确认当天 A/H 双语正文完整、原 US entry 保留、manifest 当天含 AH 且未丢历史。
2. GitHub 验证通过后必须继续用真实浏览器验证 Vercel 正式页 `https://premarketor.com/` 的动态归档加载与中英文内容均已上线，不得只用 curl/静态源码判断成功：等待 manifest 和当天 JSON 请求完成，点击 A股/港股，再分别点击中文和 EN；两种语言都必须断言 `#ah-content .brief-dashboard` 恰好 1 个、`#ah-content .empty` 为 0、首条 `.news-title` 非空、重大新闻和 `us-overnight-summary` 条数符合本轮硬校验，并确认控制台无错误。页面必须包含本次 Asia/Shanghai 更新时间或本次标题/关键词，不得仍显示上一版 A_H_TIME；中文正文、英文正文及两种语言的行业/概念 panel 均须对应本次发布。任一空态、字段筛选失败或语言切换失败均视为发布失败，必须修复并重新验证后才能报告成功。
3. 若页面仍为旧内容，短轮询重试，总观察窗口 3–5 分钟；单次等待不超过 60 秒。仍未更新则检查最新 production deployment 是否为 Initializing/Building/Queued/Failed；若已有可用 `VERCEL_DEPLOY_HOOK_URL`、Vercel API token 或 CLI 登录态，触发最新 main 的 redeploy 并再次验证。
4. 若没有可用 redeploy 凭据，或重试后正式页仍未上线，明确报告“GitHub 已更新但 Vercel 未上线/需要 redeploy”。GitHub 或 Vercel 最终回读失败均不得报告完整成功，必须说明失败原因和未完成步骤。

## 失败处理与阻塞条件

1. AKShare、Futu、Sparks、Moomoo 或某一个国内发现源的单点失败按 degrade-and-continue 执行，记录受限项并用可验证替代来源继续；AKShare 失败时不得编造市场宽度或领涨/领跌证据，其他来源专属披露、双排行降级和国内覆盖对账仍按第 8a/8b、9/9a 条执行。国内政策原始源与交易所公告不得仅因一个聚合站不可用而跳过；不得把单源失败或单个浏览器不可用当作整个发布阻塞。
2. Work Cloud 不尝试 SSH；GitHub app 连接、原子提交或 `main` 写权限不可用时直接阻塞并通知。只有本地人工运行才按 A→B 顺序尝试 SSH 后回退 GitHub app。
3. 预发布硬校验失败、GitHub 原子提交/ref 更新失败（含按规定重做后仍冲突）、远端回读失败或 Vercel 最终未上线时必须阻塞。marker 保护、中英文同构、history 完整、原子发布和最终上线校验不得降级；可修复的校验失败必须修复并重验后再发布。

## 运行摘要与最终回复

1. Work Cloud 不读取或写入任何本机 memory 文件；最新 main 的 `brief_rules.md` 是唯一规则源，第 4c 条云端交接证据仅在来源与时效验证通过后复用。
2. 每次发布任务结束前，在任务回复中输出不超过 30 行的本次状态摘要，只记本次完成情况、commit/上线状态及必要失败信息，不累积旧运行内容。
3. 最终回复只列仓库、文件、commit、history 更新结果和主要标题；若失败或仅部分完成，在对应结果中明确原因、未完成步骤及 GitHub/Vercel 的实际状态，不得报告完整成功。
