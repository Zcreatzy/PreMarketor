# 美股盘前简报自动化规则

## 任务与规则边界

生成面向投资者的工作日美股盘前简报，同时提供完整中文与忠实英文翻译，并发布到 GitHub 静态页面。本文件是本仓库美股盘前简报的云端规则单一事实来源；自动化提示词只负责启动任务，不重复维护规则。Work Cloud 每次运行必须先从最新 `main` 完整读取本文件，再读取同一 commit 下的页面与历史数据。

- 仓库：zcluster/PreMarketor；分支：main。
- 发布文件白名单：index.html、history/data/YYYY-MM-DD.json、history/manifest.json。
- history/index.html 是既有历史页模板，只读，不在本任务修改范围内。
- 正式页面：https://premarketor.com/
- 日期与持久化时间字段使用 Asia/Shanghai 当前日期时间，例如“2026-06-24 21:00 CST”；中英文显示时间必须对应同一时刻。

## 内容要求

结合最新国际局势、宏观与政策、基本面、当前盘前美股走势、美元/美债/大宗商品/汇率等关键资产，以及近日尤其是上一个交易日收盘后披露的重要财报。基于这些事实分析并预测当天开盘后的大盘走势、板块轮动和重点个股，尤其关注科技方向当天重大利好或利空，区分事实、判断与不确定性。

正文须为可直接嵌入页面的模块化 HTML 片段，不含完整 html/body/head，不使用 script、iframe、外链追踪代码或不必要的内联样式。复用模板已有 class：brief-dashboard、preview-note、module、news-list、news-item、news-tag geo/tech/earn、news-title、news-detail、takeaway、module-grid、asset-strip、asset-row、bar up/down/neutral、sector-board、sector-tile、stock-picks、stock-card、stock-head、stock-name、stock-ticker、stock-badge、logic-chain、logic-step、word-cloud、w1/w2/w3/w4/w5、bull、bear、neutral、cloud-legend、risk-list、risk-item、risk-dot high/low、positive、negative、watch、source-line。

正文图文并茂，以下模块顺序固定，不得省略或压缩：

1. **关键资产图**：必须置顶，用 asset-strip 展示至少 4 个资产或指标，每项含方向条和短文字判断。第三列 `<b>` 必须是可单行显示的短标签，不使用 `·`、`&nbsp;` 等中间分隔符。
2. **关键词云图**：与关键资产图放在同一个置顶 module-grid 中，用 word-cloud 输出 10-14 个关键词；每词同时具有权重 class、情绪 class、tabindex="0" 和 data-note，并含 cloud-legend 图例。
3. **重大新闻汇总**：必须紧跟置顶的关键资产图与关键词云图，约 10 条当天或上一个交易日收盘后的重大新闻。结构为 <details class="module full collapsible-news" open><summary>重大新闻汇总</summary><div class="news-list">...</div></details>。
4. **盘前结论**：基于新闻汇总，用 2-3 段说明事实、判断、不确定性。
5. **重点个股推荐**：用 stock-picks 输出 3-5 张 stock-card；每张必须有 stock-name、stock-ticker、stock-badge，以及推荐理由、触发因素、风险点。
6. **板块轮动看板**：用 sector-board 输出强势观察、事件驱动、压力方向、验证信号。
7. **逻辑链**：用 logic-chain/logic-step 串联新闻事实、资产价格反馈、板块传导与开盘判断。
8. **盘后财报 beat 概率**：点名当日盘后尚未披露的科技公司名称与 ticker，按高/中/低概率分层，说明已知一致预期、历史 surprise、近期指引、卖方修正、行业景气依据；明确概率是判断，不是确定事实。不得用泛化板块替代具体公司。若无值得覆盖的可验证样本，明确写“可验证盘后科技财报公司不足/无大型科技公司”，列出实际检查的财报日历及信息不足原因；可以补充行业判断，但须注明缺少具体公司样本，不虚构公司、来源或概率。
9. **风险雷达**：用 risk-list 输出 3-5 个风险。
10. **数据来源与时间点**：用 source-line 简短列出实际使用的主要来源、抓取时间与数据限制。

### 个股价格反馈约束

盘前价格反馈优先于新闻叙事。对每个 stock-picks 候选标的，先核对盘前涨跌、成交/量能、相对板块强弱和新闻后的市场反应。

- 有看似利好的并购、订单、合作或上调指引，但盘前大跌、瀑布式下跌、暴跌、重挫或明显弱于同板块的公司，不得进入多头推荐卡；降级至风险雷达、压力方向或事件驱动观察，并解释市场为何惩罚该新闻。
- 提及上述公司只用 watch/risk 口径，明确“观察/回避追多/等待止跌确认”，不得用“推荐理由”暗示可买入。
- 并购标的若上涨主要来自交易溢价，只能写“套利观察/事件观察”，不得写成基本面趋势推荐；收购方若盘前大跌，风险须包含整合成本、融资或现金支出、协同不确定性与需求压力。
- 优先选择盘前相对强势、抗跌、放量承接或至少未获显著负反馈的标的；走势与推荐方向冲突时替换。量能等单项缺失按“失败分级”披露降级，不把未知量能写成放量。

## 文件、marker 与双语契约

1. index.html 只替换以下三组 marker 之间的内容，保留 marker 本身：
   - <!-- US_BRIEF_START --> 到 <!-- US_BRIEF_END -->
   - <!-- US_TIME_START --> 到 <!-- US_TIME_END -->
   - <!-- US_UPDATED_START --> 到 <!-- US_UPDATED_END -->
2. 首页其他字节不变，特别保护 A_H_BRIEF、A_H_TIME、A_H_UPDATED、US_SECTOR_PANEL、US_SECTOR_PANEL_EN 的完整 marker 区块；不修改 CSS、脚本、页面布局。不新增或恢复历史正文、data-history-record、历史列表或日期内嵌内容；日历继续链接到 history/?date=YYYY-MM-DD。
3. 从同一模块结构同时生成当天中文 html 与英文 html_en。英文是忠实翻译，不复用固定旧稿、其他日期正文或硬编码 EN_COPY。两者根节点、标签顺序、模块顺序、class、直接子节点结构（direct-child）、新闻/asset-row/关键词/stock-card/sector-tile/logic-step/risk-item 数量、ticker 与 bar 宽度必须一致；只允许可见文本、data-note 和标签语言不同。保持既有组件布局，不以缩减模块掩盖同构问题。
4. 当天 history/data/YYYY-MM-DD.json 必须含 date、title、updated、summary、entries；新增或替换 US entry，完整保留既有 A/H 等其他 entry。US entry 同时保存完整 html 与 html_en，中文与首页本次 US 正文一致，不能只存摘要。首页英文继续从当天 US entry.html_en 读取。
5. history/manifest.json 的 records 必须包含当天日期和 US 类型，并同步 title、updated 与摘要；保留所有既有日期及其他市场类型，不能以 US 信息覆盖当天 A/H 记录。
6. 组件检查：asset-row 恰有标签、方向条、短判断三个直接子项；资产图与词云使用既有双列 module-grid；每个 logic-step 只有一个直接 wrapper 子节点，不添加手写编号或直接 b/p 子节点；词云图例使用 bull-dot、bear-dot、neutral-dot。情绪色按句意，不将涨跌方向与对股市的影响混为一谈。

## 执行与发布传输

### 获取基线和生成三文件

先取得最新 main 的 commit、三个目标文件及现有文件 SHA，再从同一基线派生修改；当天 JSON 不存在时创建，存在时合并。编辑前记录文件/marker 白名单、受保护区块及 DOM 结构签名。不要读取或覆盖工作区中不属于本次任务的修改。

### SSH 通道（仅限本地人工运行；Work Cloud 必须跳过）

1. clone main 到 /private/tmp 的独立临时目录。先用 git@github.com:zcluster/PreMarketor.git；失败后立即尝试 ssh://git@ssh.github.com:443/zcluster/PreMarketor.git。
2. SSH 两次尝试均显式使用 ~/.ssh/id_ed25519、IdentitiesOnly=yes，不依赖 ssh-agent；push 遇到同类传输故障时遵循同样回退顺序。
3. 本地三文件通过下文全部发布前检查后，以“Update US premarket brief for YYYY-MM-DD”为消息原子提交并普通 push。

### GitHub app 原子发布（Work Cloud 唯一发布通道，禁止部分发布）

1. 使用已安装并已连接的 GitHub app。先取得 main 当前 head commit SHA，记为 B；再取得 B 的 tree SHA，记为 T。
2. 必须按 ref=B 完整读取 `us_brief_rules.md`、`index.html`、`history/manifest.json` 和当天 `history/data/YYYY-MM-DD.json`。当天 JSON 返回 404 仅表示尚不存在，应按规则创建；若存在，必须保留其中全部既有 entries，尤其 A/H entry。
3. 所有 marker 替换、history 合并和 manifest 合并必须从 B 基线派生；不得用工作区旧文件或缓存整文件覆盖远端。任何写操作前完成本文件全部发布前机器硬校验。
4. 依次使用连接器实际提供的等价原子 Git Data 能力：create_blob → create_tree(base tree=T) → create_commit(parent=B) → update_ref(force=false)。三个目标文件必须位于同一 commit，其余 tree 条目不变；commit message 固定为 `Update US premarket brief for YYYY-MM-DD`。
5. 移动 main 前立即再次读取 main head。若仍等于 B，才可 update_ref；若 main 已变化或返回 non-fast-forward，禁止强推，必须从新 head 完整重读、重新合并、重新校验并重建 commit，最多重做 2 轮。
6. 禁止使用 Contents API 逐文件更新 main，禁止产生首页已更新但 history/manifest 未更新的部分发布。若原子 Git Data 能力不可用或无权限，应在 main 未变化的前提下阻塞。
7. 只有 update_ref 成功且新 commit 可从 main 回读，才算 GitHub 发布成功。GitHub app 报登录或授权失效时应明确报告；Work Cloud 不依赖本机浏览器、SSH 私钥、PAT、deploy key 或本地网络。

### 并发保护（两通道共用）

写入前确认 base commit 仍为最新 main；GitHub app 的 update_ref 必须 force=false，本地 SSH 也禁止强推。若 main 前移、non-fast-forward 或 SHA 冲突，重新读取最新 main、重新应用三文件变更并重跑全部发布前检查；重试仍失败才按传输阻塞处理。

## 统一校验与上线验收

以下检查对 Work Cloud GitHub app 和本地人工 SSH 运行完全相同；通道不同不豁免任何检查。

### 发布前

- 差异仅涉及三个白名单文件和三组授权 marker。将授权区块抹平后，首页其余部分与基线字节比较一致；逐一核对受保护 marker。
- 对照既有组件结构检查布局，并核对中英完整 DOM/class/direct-child 签名、模块顺序、计数、ticker、bar 宽度；仅 class 计数相同不足以通过。
- 检查当天 JSON 完整性、首页与 US entry 正文一致性，以及既有 entry、manifest 日期/类型未丢失。
- 核对财报披露时点与状态、预期/实际区分、价格反馈、推荐方向及句子情绪色。stock-picks 中不得存在“盘前大跌/瀑布式下跌/暴跌/重挫”却被写成多头推荐的标的；财报模块满足具体待披露公司或无样本例外。

### GitHub main 回读

发布后通过 GitHub app 重新读取 main commit、index.html、当天 history JSON 与 manifest，确认远端确已保存本次三文件及上述所有检查。本地人工运行可用 fresh clone 提供等价回读证据。

首页与 US entry 必须包含 stock-picks、asset-strip、word-cloud、sector-board、logic-chain，首页不含 data-history-record；分别验证 main 上的中文 html 与英文 html_en 均为本次内容。不能凭本地文件或单次写入成功推断发布完成。

### Vercel 正式页

1. GitHub 验证通过后，验证正式页与当天 history 数据已上线本次内容：页面 HTML 含本次 Asia/Shanghai 更新时间或本次标题/关键词，当前 US 时间不得残留上一版 US_TIME。
2. 验证中文与 EN 显示同一批新闻、资产、关键词、ticker、板块、逻辑链、风险，时间源于同一当天 US entry；中文 CST 与英文 ET 可按既有页面逻辑显示同一时刻。常规优先文本、JSON、DOM/class/direct-child 机器验证；机器结果矛盾、无法确认语言切换或显示异常时才启用浏览器，实际切换中文和 EN 检查。浏览器不可用时，改用已部署页面与当天 JSON 的读取/渲染证据完成同等双语验证，不能省略最终验收。
3. 若返回旧内容，以短轮询累计等待 3-5 分钟并保持进度可见，不单次长时间静默等待；随后检查最新 production deployment 是否 Initializing/Building/Queued/Failed。
4. 仍未上线且云任务可用 Vercel 连接或 deploy hook 时，自动触发最新 main 的 redeploy 并再次验证。没有可用云端凭据或可用手段耗尽后仍未上线，按下文报告未完成，不得报告发布成功；不得依赖本机 CLI 登录态或本地浏览器。

## 失败分级

- **软失败，降级继续**：单个新闻、行情、成交量或财报日历来源不可用时记录限制，换用其他已核验来源；浏览器不可用时换用等效验证手段。Work Cloud 不检查本机 SSH、ssh-agent、浏览器或本地网络。常规验证不安装 Playwright、Chromium 或新增依赖。
- **内容与保护校验失败，阻止发布**：文件/marker 越界、A/H 或 sector-panel 字节保护失败、结构/双语同构或完整性失败、JSON/manifest 不完整、推荐或财报状态自相矛盾。先修复并重检；不得带着失败继续提交。这些门槛独立于传输通道。
- **传输与最终验收阻塞**：GitHub app 未连接或没有写权限、缺少原子提交能力、main 竞态重试失败、GitHub main 最终回读失败、Vercel 在规定等待和可用 redeploy 手段耗尽后仍未上线或不能通过双语验收。明确失败原因、已完成部分与未完成步骤；不得用传输成功掩盖内容或上线失败。

## 运行摘要与最终回复

不要读取本机或云端任何 memory 归档作为当天内容、事实或约束来源。运行状态以本次任务回复、GitHub commit 和部署回读为准，不要求读写本机 memory 文件。

最终回复简短列明仓库、文件路径、commit 结果、历史 JSON/manifest 更新结果和主要标题。失败时同时明确原因及未完成步骤；GitHub 已更新但正式页未上线时明确写“GitHub 已更新但 Vercel 未上线/需要 redeploy”，不得报告发布成功。
