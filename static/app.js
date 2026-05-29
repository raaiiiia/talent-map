const STATUS_OPTIONS = ["待评估", "已收藏", "已排除", "待联系", "已联系", "待确认"];

const WIZARD_QUESTIONS = [
  {
    key: "scope",
    title: "岗位 + 城市 + 平台",
    prompt: "你可以先描述这次招聘岗位、业务方向、公司所在地和候选人常出现的平台。",
    placeholder: "例如：招聘岗位、具体要求、公司地理位置、目标平台...",
    example: "AI算法工程师，杭州，重点看BOSS直聘、猎聘、脉脉、LinkedIn。",
    examples: [
      "AI算法工程师，杭州，重点看BOSS直聘、猎聘、脉脉、LinkedIn。",
      "机器学习工程师，上海，优先AIGC和推荐系统背景，覆盖猎聘、脉脉、GitHub、知乎。",
      "数据科学家，北京，关注大厂和AI创业公司候选人，重点看脉脉、LinkedIn、猎聘。",
      "数据分析师，深圳，增长和电商方向，重点看BOSS直聘、猎聘、脉脉。",
      "产品经理，上海/杭州，AI工具和SaaS方向，重点看脉脉、人人都是产品经理、猎聘。",
      "电商运营负责人，杭州，直播电商和品牌自播方向，重点看BOSS直聘、猎聘、抖音电商、淘宝直播。",
      "短视频内容负责人，杭州，覆盖抖音、小红书、B站、视频号和快手。",
      "前端工程师，广州，偏中后台和数据可视化，重点看BOSS直聘、掘金、GitHub、脉脉。",
    ],
    suggestions: ["杭州优先", "长三角", "BOSS直聘 / 猎聘 / 脉脉 / LinkedIn"],
  },
  {
    key: "company_pool",
    title: "目标公司画像",
    prompt: "可以写候选人可能来自哪些公司、机构、品牌团队或相近业务类型。",
    placeholder: "例如：竞品公司、目标公司类型、上下游公司、可接受背景...",
    example: "阿里、字节、美团、快手、小红书、B站、网易、腾讯等内容/平台团队。",
    examples: [
      "阿里、字节、美团、快手、小红书、B站、网易、腾讯等内容/平台团队。",
      "百度、阿里云、火山引擎、商汤、旷视、第四范式、智谱、MiniMax等AI或云服务团队。",
      "MCN、直播电商服务商、品牌自播团队、淘系生态服务商。",
      "AIGC创业公司、AI视频工具、智能营销SaaS、企业服务团队。",
      "本地生活、电商、教育、游戏、消费品牌的增长或内容中台。",
      "可接受头部外包转甲方，但需要有核心项目职责和可验证成果。",
    ],
    suggestions: ["大厂平台团队", "AI创业公司", "直播电商生态"],
  },
  {
    key: "skills",
    title: "能力关键词",
    prompt: "可以补充最看重的作品类型、技能标签、平台数据或业务结果。",
    placeholder: "例如：核心技能、作品风格、数据表现、加分项、硬性要求...",
    example: "推荐算法、NLP/多模态、召回排序、模型评估、Python/PyTorch、线上AB实验。",
    examples: [
      "推荐算法、NLP/多模态、召回排序、模型评估、Python/PyTorch、线上AB实验。",
      "RAG、Agent、Prompt Engineering、LangChain、向量检索、模型部署和评测体系。",
      "SQL、Python、BI看板、增长分析、用户分层、转化漏斗、实验设计。",
      "产品需求拆解、原型设计、数据分析、跨部门推进、AI工具商业化落地。",
      "React、TypeScript、中后台系统、性能优化、数据可视化、组件库建设。",
      "选题策划、脚本、拍摄统筹、剪辑审美、账号增长、爆款复盘。",
      "投流、货盘、转化率、主播管理、场控SOP、GMV复盘。",
    ],
    suggestions: ["可验证项目", "业务指标", "作品或代码证据"],
  },
  {
    key: "level",
    title: "级别与履历",
    prompt: "可以写期望级别、年限范围、管理经验、预算区间或是否接受潜力型候选人。",
    placeholder: "例如：年限、职级、团队管理经验、薪资范围、可放宽条件...",
    example: "3-5年，核心执行岗，能独立交付项目，有明确作品或业务指标。",
    examples: [
      "3-5年，核心执行岗，能独立交付项目，有明确作品或业务指标。",
      "5-8年，专家/负责人，带过5-15人团队，有从0到1经验。",
      "8年以上，总监级，负责过跨部门项目，能搭建方法论和团队。",
      "接受潜力型候选人，但需要公开作品、GitHub、论文、项目链接或可验证业绩。",
      "优先一线互联网或高成长创业公司经历，薪资预算先不设硬限制。",
      "不要求管理经验，但需要能独立负责模块并推动业务结果。",
    ],
    suggestions: ["3-5年", "专家/负责人", "作品和结果优先"],
  },
  {
    key: "score_rules",
    title: "筛选口径",
    prompt: "可以写优先级、排除项、风险点和你希望 AI 特别留意的证据。",
    placeholder: "例如：必须满足项、优先项、排除项、风险提示、证据要求...",
    example: "必须有可验证证据：作品链接、项目链接、公开账号、专利论文、GitHub或业务数据。",
    examples: [
      "必须有可验证证据：作品链接、项目链接、公开账号、专利论文、GitHub或业务数据。",
      "优先同城或长三角；大厂/高成长公司背景加分；频繁跳槽需标记风险。",
      "排除纯执行、无公开证据、履历断层解释不足、作品与岗位不匹配的人选。",
      "AI方向看工程落地和线上指标；内容方向看作品质量和增长结果。",
      "候选人如果只出现转载内容、培训项目或无法确认个人贡献，需要降低置信度。",
      "需要标注当前岗位、所在地、可触达来源、推荐理由和主要风险。",
    ],
    suggestions: ["证据链接", "风险提示", "置信度"],
  },
  {
    key: "workflow",
    title: "交付与下一步",
    prompt: "可以说明你希望如何保存项目、确认候选人，以及最终需要什么交付格式。",
    placeholder: "例如：项目命名、候选人状态、交付格式、汇报对象...",
    example: "项目名：杭州AI算法工程师；输出候选人表、证据链接、推荐理由、风险提示。",
    examples: [
      "项目名：杭州AI算法工程师；输出候选人表、证据链接、推荐理由、风险提示。",
      "先给30人长名单，再按匹配度筛10人短名单，候选人状态默认待确认。",
      "每位候选人需要来源、当前公司、所在地、关键证据、建议触达话术。",
      "导出Excel给招聘团队，另生成一页老板可读的候选人地图摘要。",
      "先保存项目，后续手动导入简历和候选人链接，再统一评分。",
      "按平台、城市、公司来源拆分人才池，方便招聘负责人分批跟进。",
    ],
    suggestions: ["候选人表", "证据链接", "老板可读报告"],
  },
];

const EXAMPLE_LIBRARY = {
  scope: [
    {
      role: "AI算法工程师",
      tags: ["杭州", "BOSS直聘", "猎聘", "脉脉", "LinkedIn", "推荐算法", "NLP", "多模态"],
      text: "常见画像：负责推荐、搜索、NLP或多模态模型落地，能用Python/PyTorch完成训练、评测和线上AB实验；杭州，重点看BOSS直聘、猎聘、脉脉、LinkedIn。",
    },
    {
      role: "机器学习工程师",
      tags: ["上海", "AIGC", "推荐系统", "猎聘", "脉脉", "GitHub", "知乎"],
      text: "常见画像：负责特征工程、模型训练、推理服务和效果优化，熟悉TensorFlow/PyTorch、召回排序或AIGC应用；上海，覆盖猎聘、脉脉、GitHub、知乎。",
    },
    {
      role: "数据科学家",
      tags: ["北京", "AI创业公司", "大厂", "脉脉", "LinkedIn", "猎聘"],
      text: "常见画像：能把业务问题转成实验、建模和指标体系，熟悉Python、SQL、统计建模和因果分析；北京，关注大厂和AI创业公司候选人，重点看脉脉、LinkedIn、猎聘。",
    },
    {
      role: "数据分析师",
      tags: ["深圳", "增长", "电商", "BOSS直聘", "猎聘", "脉脉"],
      text: "常见画像：负责经营分析、增长漏斗、用户分层和BI看板，能用SQL/Python定位转化问题；深圳，增长和电商方向，重点看BOSS直聘、猎聘、脉脉。",
    },
    {
      role: "产品经理",
      tags: ["上海", "杭州", "AI工具", "SaaS", "脉脉", "人人都是产品经理", "猎聘"],
      text: "常见画像：能拆解需求、定义MVP、推进研发上线并用数据验证效果，有AI工具或企业服务产品经验；上海/杭州，重点看脉脉、人人都是产品经理、猎聘。",
    },
    {
      role: "电商运营负责人",
      tags: ["杭州", "直播电商", "品牌自播", "BOSS直聘", "猎聘", "抖音电商", "淘宝直播"],
      text: "常见画像：负责货盘、投流、主播排班、场控SOP和GMV复盘，能搭建直播间增长机制；杭州，直播电商和品牌自播方向，重点看BOSS直聘、猎聘、抖音电商、淘宝直播。",
    },
    {
      role: "短视频内容负责人",
      tags: ["杭州", "抖音", "小红书", "B站", "视频号", "快手"],
      text: "常见画像：负责选题、脚本、拍摄统筹、剪辑审美和账号增长，能复盘爆款方法论；杭州，覆盖抖音、小红书、B站、视频号和快手。",
    },
    {
      role: "前端工程师",
      tags: ["广州", "中后台", "数据可视化", "BOSS直聘", "掘金", "GitHub", "脉脉"],
      text: "常见画像：负责中后台、数据可视化和组件体系，熟悉React、TypeScript、性能优化和工程化；广州，重点看BOSS直聘、掘金、GitHub、脉脉。",
    },
  ],
  company_pool: [
    {
      role: "AI算法工程师",
      tags: ["AI算法工程师", "算法", "杭州", "AIGC", "推荐", "NLP"],
      text: "优先阿里云、火山引擎、百度、字节推荐/搜索、商汤、旷视、第四范式、智谱、MiniMax等AI团队；可补充同城高成长AI创业公司。",
    },
    {
      role: "数据科学家",
      tags: ["数据科学家", "数据", "北京", "AI创业公司", "大厂"],
      text: "优先字节、快手、美团、京东、百度、腾讯、滴滴、贝壳等有成熟数据科学团队的公司；AI创业公司需看真实业务场景和数据规模。",
    },
    {
      role: "电商运营负责人",
      tags: ["电商运营", "直播电商", "杭州", "抖音电商", "淘宝直播"],
      text: "优先淘天生态、抖音电商服务商、品牌自播团队、MCN、直播供应链和头部消费品牌电商部。",
    },
    {
      role: "产品经理",
      tags: ["产品经理", "AI工具", "SaaS", "上海", "杭州"],
      text: "优先AI工具、营销SaaS、协同办公、智能客服、数据产品和企业服务团队；看是否有从0到1和商业化闭环经验。",
    },
    {
      role: "前端工程师",
      tags: ["前端工程师", "中后台", "数据可视化", "广州", "React"],
      text: "优先有复杂B端系统、数据平台、BI、低代码或设计系统经验的互联网和SaaS团队；外包背景需确认核心职责。",
    },
  ],
  skills: [
    {
      role: "AI算法工程师",
      tags: ["AI算法工程师", "算法", "推荐", "NLP", "多模态", "PyTorch"],
      text: "推荐算法、NLP/多模态、召回排序、模型评估、Python/PyTorch、特征工程、线上AB实验和推理性能优化。",
    },
    {
      role: "机器学习工程师",
      tags: ["机器学习", "AIGC", "RAG", "Agent", "向量检索"],
      text: "RAG、Agent、Prompt Engineering、LangChain、向量检索、模型部署、评测体系、监控和成本控制。",
    },
    {
      role: "数据分析师",
      tags: ["数据分析", "增长", "电商", "SQL", "BI"],
      text: "SQL、Python、BI看板、增长分析、用户分层、转化漏斗、实验设计、经营复盘和跨部门解释能力。",
    },
    {
      role: "产品经理",
      tags: ["产品经理", "AI工具", "SaaS", "商业化"],
      text: "产品需求拆解、原型设计、数据分析、跨部门推进、AI工具商业化落地、客户访谈和版本节奏管理。",
    },
    {
      role: "短视频内容负责人",
      tags: ["短视频", "内容", "抖音", "小红书", "B站"],
      text: "选题策划、脚本、拍摄统筹、剪辑审美、账号增长、爆款复盘、平台规则理解和内容团队管理。",
    },
    {
      role: "电商运营负责人",
      tags: ["电商运营", "直播", "GMV", "投流"],
      text: "投流、货盘、转化率、主播管理、场控SOP、GMV复盘、达人合作和直播间数据诊断。",
    },
    {
      role: "前端工程师",
      tags: ["前端", "React", "TypeScript", "数据可视化"],
      text: "React、TypeScript、中后台系统、性能优化、数据可视化、组件库建设、权限体系和工程化质量。",
    },
  ],
  level: [
    {
      role: "AI算法工程师",
      tags: ["AI算法工程师", "算法", "3-5年", "工程落地"],
      text: "3-5年可做核心执行岗，要求独立负责模型模块并有线上指标；5年以上可看技术owner或小团队负责人。",
    },
    {
      role: "数据科学家",
      tags: ["数据科学家", "数据", "5-8年", "实验"],
      text: "3-6年看独立分析和建模能力；5-8年看实验体系、业务影响力和跨团队推动经验。",
    },
    {
      role: "产品经理",
      tags: ["产品经理", "SaaS", "AI工具", "负责人"],
      text: "3-5年看完整模块owner；5-8年看产品线负责人经历、商业化指标和复杂项目推进能力。",
    },
    {
      role: "电商运营负责人",
      tags: ["电商运营", "直播电商", "负责人", "GMV"],
      text: "5年以上优先，最好带过直播间、投流或品牌自播团队；总监级需要能搭建SOP和预算模型。",
    },
    {
      role: "前端工程师",
      tags: ["前端工程师", "React", "中后台", "3-5年"],
      text: "3-5年看模块独立交付和代码质量；5年以上看架构、组件体系、性能治理和技术协作影响力。",
    },
  ],
  score_rules: [
    {
      role: "AI算法工程师",
      tags: ["AI算法工程师", "算法", "GitHub", "论文", "专利", "线上指标"],
      text: "必须有可验证证据：GitHub、论文/专利、线上指标、项目复盘或公开技术分享；只写训练营项目需降低置信度。",
    },
    {
      role: "数据分析师",
      tags: ["数据分析", "BI", "增长", "电商", "转化"],
      text: "优先能说明指标口径、分析链路和业务动作的人；只会出报表但没有业务结论或推动结果的候选人降权。",
    },
    {
      role: "产品经理",
      tags: ["产品经理", "AI工具", "SaaS", "商业化"],
      text: "必须看到需求判断、上线结果和商业化指标；纯项目协调、缺少产品判断或无数据闭环的候选人降权。",
    },
    {
      role: "短视频内容负责人",
      tags: ["短视频", "内容", "账号增长", "作品"],
      text: "优先有公开账号、爆款案例和增长复盘；只展示搬运内容、无法确认个人贡献或作品风格不匹配的候选人降权。",
    },
    {
      role: "电商运营负责人",
      tags: ["电商运营", "直播", "GMV", "投流"],
      text: "必须标注GMV、投流ROI、转化率或直播间阶段成果；无法区分团队贡献和个人贡献时降低置信度。",
    },
  ],
  workflow: [
    {
      role: "AI算法工程师",
      tags: ["AI算法工程师", "算法", "杭州", "候选人表"],
      text: "项目名：杭州AI算法工程师；输出候选人表、技术证据链接、推荐理由、风险提示和建议触达话术。",
    },
    {
      role: "数据分析师",
      tags: ["数据分析师", "深圳", "增长", "电商"],
      text: "项目名：深圳增长数据分析；先给30人长名单，再按电商增长经验筛10人短名单，候选人状态默认待确认。",
    },
    {
      role: "产品经理",
      tags: ["产品经理", "AI工具", "SaaS", "上海", "杭州"],
      text: "项目名：AI工具产品经理；每位候选人需要当前公司、负责产品、上线结果、商业化证据和主要风险。",
    },
    {
      role: "电商运营负责人",
      tags: ["电商运营", "杭州", "直播电商", "GMV"],
      text: "项目名：杭州直播电商运营负责人；按平台、品牌类型和GMV规模拆分人才池，方便招聘负责人分批跟进。",
    },
    {
      role: "前端工程师",
      tags: ["前端工程师", "广州", "React", "数据可视化"],
      text: "项目名：广州中后台前端工程师；导出Excel给招聘团队，另生成组件/可视化项目证据摘要。",
    },
  ],
};

const DEFAULT_PROFILE = {
  main_direction: "视频创作",
  assistant_direction: "AI算法",
  region: "长三角，杭州优先",
  industries: ["互联网", "电商", "短视频"],
  company_types: ["MCN机构", "电商公司", "短视频平台", "内容营销公司", "品牌方内容团队", "AI视频工具公司"],
  platforms: ["BOSS直聘", "猎聘", "脉脉", "LinkedIn"],
  content_types: ["品牌广告", "知识科普", "视频剪辑", "调色", "编剧", "文案", "AIGC"],
  ai_algorithm_tags: ["推荐算法", "内容理解", "多模态", "视频生成", "AIGC工具", "投流/广告算法", "搜索排序"],
  levels: ["骨干", "专家"],
  scoring_view: "业务视角优先",
  source_policy: "仅检索公开可读数据和企业已授权数据源",
  max_candidates_before_narrowing: 50,
};

const state = {
  token: localStorage.getItem("talent_map_token") || "",
  user: null,
  projects: [],
  activeProjectId: Number(localStorage.getItem("talent_map_active_project") || 0) || null,
  project: null,
  plan: null,
  candidates: [],
  config: null,
  view: "wizard",
  wizardAnswers: [],
  busy: false,
  thinking: false,
};

const SKIPPED_ANSWER = "跳过，按默认设置。";

const $ = (selector) => document.querySelector(selector);
const byId = (id) => document.getElementById(id);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeList(value) {
  if (Array.isArray(value)) return value.map((item) => String(item).trim()).filter(Boolean);
  return String(value ?? "")
    .split(/[、，,;；\n|/]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function unique(items) {
  return [...new Set(items.filter(Boolean))];
}

function truncate(value, limit = 80) {
  const text = String(value ?? "");
  return text.length > limit ? `${text.slice(0, limit)}…` : text;
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function canSkipQuestion(question) {
  return question && question.key !== "scope";
}

function scoreClass(score) {
  const num = Number(score || 0);
  if (num >= 80) return "high";
  if (num >= 60) return "mid";
  return "low";
}

function setBusy(isBusy) {
  state.busy = isBusy;
  document.body.classList.toggle("loading", isBusy);
  document.querySelectorAll("button").forEach((button) => {
    if (button.dataset.keepEnabled !== "true") button.disabled = isBusy;
  });
}

function showNotice(message, type = "info") {
  const notice = byId("notice");
  if (!message) {
    notice.className = "notice hidden";
    notice.textContent = "";
    return;
  }
  notice.className = `notice ${type === "error" ? "error" : type === "success" ? "success" : ""}`;
  notice.textContent = message;
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const request = { method: options.method || "GET", headers };
  if (options.body instanceof FormData) {
    request.body = options.body;
  } else if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    request.body = JSON.stringify(options.body);
  }
  const response = await fetch(path, request);
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    throw new Error((data && (data.error || data.message)) || `请求失败：${response.status}`);
  }
  return data;
}

async function downloadFile(path, filename) {
  const response = await fetch(path, { headers: { Authorization: `Bearer ${state.token}` } });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "下载失败");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function setView(view) {
  state.view = view;
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === view));
  render();
}

async function refreshAll({ keepNotice = false } = {}) {
  if (!keepNotice) showNotice("");
  const projectsData = await api("/api/projects");
  state.projects = projectsData.projects || [];
  if (state.activeProjectId && !state.projects.some((project) => project.id === state.activeProjectId)) {
    state.activeProjectId = null;
    state.project = null;
    state.plan = null;
    state.candidates = [];
  }
  if (!state.activeProjectId && state.projects.length) {
    state.activeProjectId = state.projects[0].id;
  }
  if (state.activeProjectId) {
    await loadProject(state.activeProjectId);
  }
  renderShell();
  render();
}

async function loadProject(id) {
  const [projectData, candidateData] = await Promise.all([api(`/api/projects/${id}`), api(`/api/projects/${id}/candidates`)]);
  state.activeProjectId = id;
  state.project = projectData.project;
  state.plan = projectData.plan;
  state.candidates = candidateData.candidates || [];
  localStorage.setItem("talent_map_active_project", String(id));
}

async function loadMeAndProjects() {
  const [me, config] = await Promise.all([api("/api/me"), api("/api/config")]);
  state.user = me.user;
  state.config = config.config;
  await refreshAll({ keepNotice: true });
}

function showApp() {
  byId("loginScreen").classList.add("hidden");
  byId("appShell").classList.remove("hidden");
}

function showLogin() {
  byId("loginScreen").classList.remove("hidden");
  byId("appShell").classList.add("hidden");
}

function renderShell() {
  byId("userBadge").textContent = state.user ? "已登录" : "未登录";
  byId("projectList").innerHTML =
    state.projects
      .map(
        (project) => `
          <div class="project-item ${project.id === state.activeProjectId ? "active" : ""}" data-action="select-project" data-id="${project.id}">
            <strong>${escapeHtml(project.title)}</strong>
            <span>${escapeHtml(project.status)} · ${escapeHtml(project.updated_at || "")}</span>
          </div>
        `
      )
      .join("") || `<div class="empty">还没有项目。用 AI 问答创建第一个人才地图。</div>`;
}

function setPageMeta(label, title) {
  byId("viewLabel").textContent = label;
  byId("pageTitle").textContent = title;
}

function render() {
  if (!state.token) return;
  const renderers = {
    wizard: renderWizard,
    candidates: renderCandidates,
    maps: renderMaps,
    imports: renderImports,
    settings: renderSettings,
  };
  (renderers[state.view] || renderWizard)();
}

function currentQuestion() {
  return WIZARD_QUESTIONS[state.wizardAnswers.length] || null;
}

function answersByKey() {
  return Object.fromEntries(state.wizardAnswers.map((item) => [item.key, item.answer]));
}

function exampleText(example) {
  return typeof example === "string" ? example : example?.text || "";
}

function exampleTitle(example, fallback = "") {
  return typeof example === "string" ? fallback : example?.role || example?.title || fallback;
}

function exampleTags(example) {
  if (!example || typeof example === "string") return [];
  return [example.role, example.city, ...(example.platforms || []), ...(example.tags || [])].filter(Boolean);
}

function exampleScore(example, contextText) {
  if (!contextText || typeof example === "string") return 0;
  const haystack = contextText.toLowerCase();
  return exampleTags(example).reduce((score, tag) => {
    const keyword = String(tag).toLowerCase();
    if (!keyword || !haystack.includes(keyword)) return score;
    return score + Math.min(8, Math.max(2, keyword.length));
  }, 0);
}

function currentExampleItems(question = currentQuestion()) {
  if (!question) return [];
  const fallback = question.examples && question.examples.length ? question.examples : question.example ? [question.example] : [];
  const base = EXAMPLE_LIBRARY[question.key] || fallback;
  const contextText = Object.values(answersByKey()).join(" ");
  return base
    .map((item, index) => ({ item, index, score: exampleScore(item, contextText) }))
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .map(({ item }) => item);
}

function buildDraftProfile() {
  const answers = answersByKey();
  const scope = answers.scope || "";
  const skills = answers.skills || "";
  const companyPool = answers.company_pool || "";
  const workflow = answers.workflow || "";
  const regionHits = unique(["杭州", "上海", "苏州", "南京", "宁波", "无锡", "合肥", "嘉兴"].filter((city) => scope.includes(city)));
  const platformHits = unique(
    ["BOSS直聘", "猎聘", "脉脉", "LinkedIn", "GitHub", "知乎", "掘金", "人人都是产品经理", "抖音电商", "淘宝直播", "抖音", "小红书", "B站", "视频号", "快手"].filter(
      (platform) => scope.includes(platform) || skills.includes(platform)
    )
  );
  const contentHits = unique(["品牌广告", "知识科普", "视频剪辑", "调色", "编剧", "文案", "AIGC", "直播", "短剧"].filter((tag) => skills.includes(tag)));
  const companyTypes = normalizeList(companyPool);
  return {
    ...DEFAULT_PROFILE,
    region: regionHits.length ? regionHits.join("、") : DEFAULT_PROFILE.region,
    platforms: platformHits.length ? platformHits : DEFAULT_PROFILE.platforms,
    platform_scope_note: platformHits.length
      ? `已根据目标筛选平台缩小范围：${platformHits.join("、")}。`
      : `未指定目标筛选平台，按默认平台检索：${DEFAULT_PROFILE.platforms.join("、")}。`,
    content_types: contentHits.length ? contentHits : DEFAULT_PROFILE.content_types,
    company_types: companyTypes.length ? companyTypes : DEFAULT_PROFILE.company_types,
    scoring_notes: answers.score_rules || "作品优先，公开证据优先，AI评分仅作辅助。",
    workflow_notes: workflow || "保存为项目；候选人先待确认；输出 Excel、PDF、图片。",
    raw_requirements: state.wizardAnswers.map((item) => `${item.title}：${item.answer}`).join("\n"),
  };
}

function defaultAnswer(question) {
  if (!question) return "";
  const example = currentExampleItems(question)[0];
  if (example) return exampleText(example);
  return question.example || question.placeholder || "";
}

async function advanceWizard(answer) {
  const q = currentQuestion();
  if (!q) return;
  if (state.wizardAnswers.length === WIZARD_QUESTIONS.length - 1) {
    setBusy(true);
    try {
      await createProjectFromWizard(answer);
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
    return;
  }
  state.wizardAnswers.push({ key: q.key, title: q.title, question: q.prompt, answer });
  state.thinking = true;
  render();
  await wait(520);
  state.thinking = false;
  render();
}

function inferProjectTitle(profile = {}, answers = answersByKey()) {
  const text = `${Object.values(answers).join(" ")} ${profile.raw_requirements || ""}`;
  const explicitRoles = [
    "AI算法工程师",
    "算法工程师",
    "AIGC创作者",
    "短视频编导",
    "视频剪辑师",
    "内容策划",
    "内容运营",
    "直播运营",
    "品牌广告策划",
  ];
  const exactRole = explicitRoles.find((role) => text.includes(role));
  if (exactRole) return exactRole;
  if (/(AI|AIGC|大模型|算法|机器学习|深度学习|推荐|搜索)/i.test(text)) return "AI算法工程师";
  if (/编导|导演|分镜/.test(text)) return "短视频编导";
  if (/剪辑|调色|后期|包装/.test(text)) return "视频剪辑师";
  if (/直播|主播|场控/.test(text)) return "直播运营";
  if (/内容|选题|脚本|文案|策划/.test(text)) return "内容策划";
  return "视频创作人才";
}

async function createProjectFromWizard(answerFromForm = "") {
  const q = currentQuestion();
  if (q) {
    state.wizardAnswers.push({
      key: q.key,
      title: q.title,
      question: q.prompt,
      answer: answerFromForm || defaultAnswer(q),
    });
  }
  const profile = buildDraftProfile();
  const title = inferProjectTitle(profile);
  const payloadAnswers = state.wizardAnswers.map((item) => ({ question: item.title, answer: item.answer }));
  const created = await api("/api/projects", {
    method: "POST",
    body: { title, answers: payloadAnswers, profile, saved: true },
  });
  state.project = created.project;
  state.plan = created.plan;
  state.activeProjectId = created.project.id;
  state.candidates = [];
  localStorage.setItem("talent_map_active_project", String(state.activeProjectId));
  await refreshAll({ keepNotice: true });
  showNotice("项目已创建。你可以先查看检索方案，也可以在设置里填入 Tavily / DeepSeek Key 后启动公开检索。", "success");
}

function renderWizard() {
  setPageMeta("", "通过 AI 问答检索你的候选人");
  const q = currentQuestion();
  const exampleItems = currentExampleItems(q);
  const messages = [];
  if (WIZARD_QUESTIONS[0]) {
    messages.push({ role: "ai", title: WIZARD_QUESTIONS[0].title, text: WIZARD_QUESTIONS[0].prompt, progress: `1 / ${WIZARD_QUESTIONS.length}` });
  }
  state.wizardAnswers.forEach((item, index) => {
    messages.push({ role: "user", title: item.title, text: item.answer });
    const next = WIZARD_QUESTIONS[index + 1];
    if (next && !(state.thinking && index === state.wizardAnswers.length - 1)) {
      messages.push({ role: "ai", title: next.title, text: next.prompt, progress: `${index + 2} / ${WIZARD_QUESTIONS.length}` });
    }
  });
  const conversation = messages
    .map(
      (message) => `
        <div class="bubble ${message.role}">
          <div class="question-title">
            <strong>${message.role === "ai" ? "候选人" : "你"}${message.title ? ` ${escapeHtml(message.title)}` : ""}</strong>
            ${message.progress ? `<span class="progress">${escapeHtml(message.progress)}</span>` : ""}
          </div>
          <p>${escapeHtml(message.text)}</p>
        </div>
      `
    )
    .join("");
  const thinkingHtml = state.thinking
    ? `
        <div class="bubble ai thinking" aria-live="polite">
          <div class="question-title">
            <strong>候选人正在思考</strong>
          </div>
          <div class="typing-line">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span>正在理解你的要求并组织下一步问题…</span>
          </div>
        </div>
      `
    : "";

  const wizardHtml = `
    <div class="wizard-home">
      <div class="page-head wizard-intro">
        <h1>通过 AI 问答检索你的候选人</h1>
        <p>像和招聘顾问对话一样输入岗位、要求、地理位置、目标公司和筛选口径，系统会整理成项目并生成候选人检索方案。</p>
      </div>
      <div class="chat wizard-chat">
      <div class="chat-flow">
        ${conversation}
        ${thinkingHtml}
        ${
          q && !state.thinking
            ? `
          <form id="wizardForm" class="chat-composer">
              <div class="field">
                <label for="wizardAnswer">你的描述</label>
                <textarea id="wizardAnswer" name="answer" autocomplete="off" placeholder="${escapeHtml(q.placeholder)}"></textarea>
              </div>
              <div class="form-actions">
                <button class="primary" type="submit">${state.wizardAnswers.length === WIZARD_QUESTIONS.length - 1 ? "创建项目" : "发送"}</button>
                <button class="quiet" data-action="toggle-examples" type="button" aria-expanded="false" aria-controls="exampleCatalog">查看示例描述</button>
                ${canSkipQuestion(q) ? '<button class="quiet" data-action="skip-question" type="button">跳过</button>' : ""}
                ${state.wizardAnswers.length ? '<button class="quiet" data-action="back-question" type="button">上一步</button>' : ""}
                <button class="quiet" data-action="reset-wizard" type="button">重置</button>
              </div>
              <div id="exampleCatalog" class="example-catalog" hidden>
                <div class="example-head">示例目录 · ${escapeHtml(q.title)}</div>
                <div class="example-list">
                  ${exampleItems
                    .map(
                      (item, index) => `
                      <div class="example-item">
                        <div>
                          <div class="example-meta">
                            <strong>示例 ${index + 1}</strong>
                            ${exampleTitle(item) ? `<span>${escapeHtml(exampleTitle(item))}</span>` : ""}
                          </div>
                          <p>${escapeHtml(exampleText(item))}</p>
                        </div>
                        <button class="quiet" data-action="apply-example" data-example-index="${index}" type="button">应用</button>
                      </div>
                    `
                    )
                    .join("")}
                </div>
              </div>
          </form>
        `
            : state.project
              ? `
          <div class="bubble ai saved-project">
            <div class="question-title">
              <strong>候选人 项目已保存</strong>
            </div>
            <p>已保存为「${escapeHtml(state.project.title)}」。你可以继续检索候选人；缺少检索配置时，系统会给出下一步提示。</p>
            <div class="form-actions">
              <button class="primary" data-action="discover" type="button">公开检索候选人</button>
              <button data-action="show-candidates" type="button">查看候选人</button>
              <button class="quiet" data-action="reset-wizard" type="button">重新创建</button>
            </div>
          </div>
        `
              : ""
        }
      </div>
      </div>
    </div>
  `;

  byId("content").innerHTML = wizardHtml;
}

function renderPlan(plan) {
  if (!plan) return `<div class="empty">暂无检索方案。</div>`;
  return `
    <div class="grid-2">
      <div>
        <h3>建议竞品池</h3>
        <div class="chips">${(plan.competitor_pool || []).map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("")}</div>
      </div>
      <div>
        <h3>关联词</h3>
        <div class="chips">${(plan.related_keywords || []).slice(0, 24).map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("")}</div>
      </div>
    </div>
    <details>
      <summary>更多：检索式与缩小范围问题</summary>
      <div class="grid-2" style="margin-top:12px">
        <div>
          <h3>检索式</h3>
          <ul>${(plan.queries || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <button data-action="copy-queries" type="button">复制检索式</button>
        </div>
        <div>
          <h3>超过 50 人时继续追问</h3>
          <ul>${(plan.narrow_questions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>
      </div>
    </details>
  `;
}

function projectRequiredHtml() {
  return `
    <div class="empty">
      <p>请先创建或选择一个项目。</p>
      <button class="primary" data-action="go-wizard" type="button">回到创建项目</button>
    </div>
  `;
}

function candidateMetrics() {
  const total = state.candidates.length;
  const collected = state.candidates.filter((item) => item.status === "已收藏").length;
  const follow = state.candidates.filter((item) => item.status === "待联系" || item.status === "已联系").length;
  const high = state.candidates.filter((item) => Number(item.score || 0) >= 80).length;
  return { total, collected, follow, high };
}

function renderMetrics() {
  const metrics = candidateMetrics();
  return `
    <div class="metrics">
      <div class="metric"><span>候选人</span><strong>${metrics.total}</strong></div>
      <div class="metric"><span>高分人选</span><strong>${metrics.high}</strong></div>
      <div class="metric"><span>已收藏</span><strong>${metrics.collected}</strong></div>
      <div class="metric"><span>待/已联系</span><strong>${metrics.follow}</strong></div>
    </div>
  `;
}

function renderCandidates() {
  setPageMeta("Candidate Pool", state.project ? `${state.project.title} · 候选人` : "候选人");
  if (!state.project) {
    byId("content").innerHTML = projectRequiredHtml();
    return;
  }
  const rows = state.candidates
    .map(
      (candidate) => `
        <tr>
          <td>
            <div class="candidate-name">
              <strong>${escapeHtml(candidate.name || "未命名候选人")}</strong>
              <span class="muted">${escapeHtml(candidate.city || "城市待确认")} · ${escapeHtml(candidate.years || "年限待确认")}</span>
              <span class="status" data-status="${escapeHtml(candidate.status)}">${escapeHtml(candidate.status)}</span>
            </div>
          </td>
          <td>${escapeHtml(candidate.current_company || "待确认")}</td>
          <td>${escapeHtml(candidate.title || "待确认")}</td>
          <td>${tagList(candidate.skill_tags)}</td>
          <td><span class="score ${scoreClass(candidate.score)}">${candidate.score ?? "-"}</span><div class="muted">${escapeHtml(candidate.score_band || "未评分")}</div></td>
          <td>
            <select class="status-select" data-id="${candidate.id}">
              ${STATUS_OPTIONS.map((status) => `<option value="${status}" ${status === candidate.status ? "selected" : ""}>${status}</option>`).join("")}
            </select>
            <div class="split-actions" style="margin-top:8px">
              <button data-action="set-status" data-id="${candidate.id}" data-status="已收藏" type="button">收藏</button>
              <button data-action="set-status" data-id="${candidate.id}" data-status="待联系" type="button">待联系</button>
              <button class="danger" data-action="set-status" data-id="${candidate.id}" data-status="已排除" type="button">排除</button>
            </div>
          </td>
          <td>
            <strong>推荐</strong>
            <div>${escapeHtml(candidate.recommendation_reason || "暂无推荐理由")}</div>
            ${candidate.risk_notes ? `<strong>风险</strong><div>${escapeHtml(candidate.risk_notes)}</div>` : ""}
            <details>
              <summary>更多</summary>
              <div class="fine">
                <p><strong>作品/项目：</strong>${listText(candidate.works)}</p>
                <p><strong>平台：</strong>${listText(candidate.platforms)}</p>
                <p><strong>过往公司：</strong>${listText(candidate.past_companies)}</p>
                <p><strong>AIGC 使用：</strong>${escapeHtml(candidate.aigc_usage || "待确认")}</p>
                <p><strong>证据：</strong>${escapeHtml(candidate.raw_evidence || "待补充")}</p>
                <div class="source-list">${linkList(candidate.source_links)}</div>
              </div>
            </details>
          </td>
        </tr>
      `
    )
    .join("");

  byId("content").innerHTML = `
    <div class="page-head">
      <div>
        <h1>候选人池</h1>
        <p>候选人来自公开网页、手动链接或企业授权文件。AI 生成的人选建议先保持“待确认”。</p>
      </div>
      <div class="split-actions">
        <button class="primary" data-action="discover" type="button">公开检索候选人</button>
        <button data-action="go-imports" type="button">导入链接/文件</button>
      </div>
    </div>
    ${renderMetrics()}
    <div class="section">
      <h3>手动添加候选人</h3>
      ${renderManualCandidateForm()}
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>候选人</th><th>当前公司</th><th>职位</th><th>技能</th><th>评分</th><th>状态</th><th>推荐理由与证据</th>
          </tr>
        </thead>
        <tbody>${rows || `<tr><td colspan="7"><div class="empty">还没有候选人。可以先公开检索，或导入公开链接、Excel/CSV/简历 PDF。</div></td></tr>`}</tbody>
      </table>
    </div>
  `;
}

function renderManualCandidateForm() {
  return `
    <form id="manualCandidateForm" class="form">
      <div class="grid-3">
        <div class="field"><label>姓名</label><input name="name" placeholder="候选人姓名或账号名" required></div>
        <div class="field"><label>当前公司</label><input name="current_company" placeholder="当前公司 / 机构 / 自媒体"></div>
        <div class="field"><label>职位</label><input name="title" placeholder="内容负责人 / 编导 / 创作者"></div>
      </div>
      <div class="grid-3">
        <div class="field"><label>城市</label><input name="city" placeholder="杭州"></div>
        <div class="field"><label>年限</label><input name="years" placeholder="5年"></div>
        <div class="field"><label>平台</label><input name="platforms" placeholder="抖音、小红书"></div>
      </div>
      <div class="grid-2">
        <div class="field"><label>技能标签</label><input name="skill_tags" placeholder="爆款选题、剪辑审美、品牌内容"></div>
        <div class="field"><label>来源链接</label><input name="source_links" placeholder="https://..."></div>
      </div>
      <div class="field"><label>作品/项目</label><textarea name="works" placeholder="公开作品、账号、商业案例"></textarea></div>
      <div class="field"><label>推荐理由</label><textarea name="recommendation_reason" placeholder="为什么值得进入人才池"></textarea></div>
      <div class="form-actions"><button class="primary" type="submit">添加候选人</button></div>
    </form>
  `;
}

function listText(value) {
  const items = normalizeList(value);
  return items.length ? escapeHtml(items.join("、")) : "待补充";
}

function tagList(value) {
  const items = normalizeList(value);
  return items.length ? items.map((item) => `<span class="tag">${escapeHtml(item)}</span>`).join("") : `<span class="muted">待补充</span>`;
}

function linkList(value) {
  const links = normalizeList(value);
  if (!links.length) return `<span class="muted">暂无链接</span>`;
  return links
    .map((link) => {
      const safe = escapeHtml(link);
      return `<a href="${safe}" target="_blank" rel="noreferrer">${safe}</a>`;
    })
    .join("");
}

function countsFor(key) {
  const map = {};
  state.candidates.forEach((candidate) => {
    normalizeList(candidate[key]).forEach((item) => {
      map[item] = (map[item] || 0) + 1;
    });
  });
  return map;
}

function countScalar(key) {
  const map = {};
  state.candidates.forEach((candidate) => {
    const value = candidate[key] || "待确认";
    map[value] = (map[value] || 0) + 1;
  });
  return map;
}

function topEntries(map, limit = 12) {
  return Object.entries(map)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit);
}

function barSvg(id, title, entries, color = "#2f5f8f") {
  const safeEntries = entries.length ? entries : [["暂无数据", 1]];
  const height = 72 + safeEntries.length * 34;
  const max = Math.max(...safeEntries.map(([, value]) => value), 1);
  const rows = safeEntries
    .map(([label, value], index) => {
      const y = 58 + index * 34;
      const width = Math.max(12, Math.round((value / max) * 430));
      return `
        <text x="24" y="${y + 14}" fill="#3f4449" font-size="13">${escapeHtml(truncate(label, 18))}</text>
        <rect x="184" y="${y}" width="${width}" height="20" rx="4" fill="${color}" opacity="${0.85 - Math.min(index * 0.035, 0.35)}"></rect>
        <text x="${196 + width}" y="${y + 15}" fill="#202124" font-size="12">${value}</text>
      `;
    })
    .join("");
  return `
    <svg id="${id}" viewBox="0 0 680 ${height}" role="img" aria-label="${escapeHtml(title)}">
      <rect width="680" height="${height}" fill="#fbfbfa"></rect>
      <text x="24" y="34" fill="#202124" font-size="18" font-weight="700">${escapeHtml(title)}</text>
      ${rows}
    </svg>
  `;
}

function networkSvg() {
  const companies = topEntries(countScalar("current_company"), 8).map(([company]) => company);
  const candidates = state.candidates.slice(0, 12);
  const height = Math.max(360, 80 + Math.max(companies.length, candidates.length) * 34);
  const companyRows = companies
    .map((company, index) => {
      const y = 72 + index * 38;
      return `<circle cx="110" cy="${y}" r="7" fill="#29705f"></circle><text x="126" y="${y + 5}" font-size="12" fill="#202124">${escapeHtml(truncate(company, 14))}</text>`;
    })
    .join("");
  const candidateRows = candidates
    .map((candidate, index) => {
      const y = 72 + index * 32;
      return `<circle cx="520" cy="${y}" r="6" fill="#2f5f8f"></circle><text x="536" y="${y + 4}" font-size="12" fill="#202124">${escapeHtml(truncate(candidate.name || "未命名", 12))}</text>`;
    })
    .join("");
  const lines = candidates
    .map((candidate, index) => {
      const companyIndex = Math.max(0, companies.indexOf(candidate.current_company || "待确认"));
      const y1 = 72 + companyIndex * 38;
      const y2 = 72 + index * 32;
      return `<path d="M 230 ${y1} C 340 ${y1}, 380 ${y2}, 506 ${y2}" stroke="#c8c8c2" stroke-width="1.5" fill="none"></path>`;
    })
    .join("");
  return `
    <svg id="networkMap" viewBox="0 0 680 ${height}" role="img" aria-label="公司候选人网络">
      <rect width="680" height="${height}" fill="#fbfbfa"></rect>
      <text x="24" y="34" fill="#202124" font-size="18" font-weight="700">竞品公司人才池</text>
      <text x="80" y="56" fill="#6f7378" font-size="12">公司</text>
      <text x="500" y="56" fill="#6f7378" font-size="12">候选人</text>
      ${lines}${companyRows}${candidateRows}
    </svg>
  `;
}

function flowSvg() {
  const flows = {};
  state.candidates.forEach((candidate) => {
    normalizeList(candidate.past_companies).slice(0, 3).forEach((past) => {
      const current = candidate.current_company || "待确认";
      const key = `${past} → ${current}`;
      flows[key] = (flows[key] || 0) + 1;
    });
  });
  const entries = topEntries(flows, 12);
  const safeEntries = entries.length ? entries : [["公开信息不足，待补充流动路径", 1]];
  const height = 74 + safeEntries.length * 34;
  const max = Math.max(...safeEntries.map(([, value]) => value), 1);
  const rows = safeEntries
    .map(([label, value], index) => {
      const y = 62 + index * 34;
      const [from, to] = label.split(" → ");
      const width = Math.max(30, Math.round((value / max) * 150));
      return `
        <text x="28" y="${y + 14}" fill="#202124" font-size="12">${escapeHtml(truncate(from || label, 16))}</text>
        <path d="M 190 ${y + 9} L ${350 + width} ${y + 9}" stroke="#9a6a25" stroke-width="${Math.min(8, 2 + value)}" stroke-linecap="round"></path>
        <path d="M ${350 + width} ${y + 9} l -8 -5 v10 z" fill="#9a6a25"></path>
        <text x="${370 + width}" y="${y + 14}" fill="#202124" font-size="12">${escapeHtml(truncate(to || "", 18))} · ${value}</text>
      `;
    })
    .join("");
  return `
    <svg id="flowMap" viewBox="0 0 680 ${height}" role="img" aria-label="候选人流动路径">
      <rect width="680" height="${height}" fill="#fbfbfa"></rect>
      <text x="24" y="34" fill="#202124" font-size="18" font-weight="700">候选人流动路径</text>
      ${rows}
    </svg>
  `;
}

function renderMapCard(title, svg, id) {
  return `
    <div class="map-card">
      <h3>
        <span>${escapeHtml(title)}</span>
        <span class="svg-actions">
          <button data-action="download-svg" data-id="${id}" type="button">SVG</button>
          <button data-action="download-png" data-id="${id}" type="button">图片</button>
        </span>
      </h3>
      ${svg}
    </div>
  `;
}

function renderMaps() {
  setPageMeta("Talent Map", state.project ? `${state.project.title} · 地图` : "地图");
  if (!state.project) {
    byId("content").innerHTML = projectRequiredHtml();
    return;
  }
  if (!state.candidates.length) {
    byId("content").innerHTML = `
      <div class="page-head"><div><h1>可视化人才地图</h1><p>先导入或检索候选人，再按技能、平台、公司和流动路径生成地图。</p></div></div>
      ${projectRequiredHtml().replace("请先创建或选择一个项目。", "当前项目还没有候选人。")}
    `;
    return;
  }
  const skillEntries = topEntries(countsFor("skill_tags"), 12);
  const platformEntries = topEntries(countsFor("platforms"), 10);
  const cityEntries = topEntries(countScalar("city"), 8);
  byId("content").innerHTML = `
    <div class="page-head">
      <div>
        <h1>可视化人才地图</h1>
        <p>可按公司、技能分布、竞品人才池、候选人流动路径和内容创作者平台分布生成地图，并导出图片。</p>
      </div>
      <div class="split-actions">
        <button data-action="download-xlsx" type="button">导出 Excel 数据源</button>
        <button class="primary" data-action="open-report" type="button">打开 PDF 报告</button>
      </div>
    </div>
    ${renderMetrics()}
    <div class="map-grid">
      ${renderMapCard("技能分布", barSvg("skillMap", "技能分布", skillEntries, "#2f5f8f"), "skillMap")}
      ${renderMapCard("平台分布", barSvg("platformMap", "平台分布", platformEntries, "#29705f"), "platformMap")}
      ${renderMapCard("城市分布", barSvg("cityMap", "城市分布", cityEntries, "#9a6a25"), "cityMap")}
      ${renderMapCard("公司人才池", networkSvg(), "networkMap")}
      ${renderMapCard("流动路径", flowSvg(), "flowMap")}
    </div>
  `;
}

function renderImports() {
  setPageMeta("Sources & Export", state.project ? `${state.project.title} · 导入导出` : "导入导出");
  if (!state.project) {
    byId("content").innerHTML = projectRequiredHtml();
    return;
  }
  byId("content").innerHTML = `
    <div class="page-head">
      <div>
        <h1>导入、检索与导出</h1>
        <p>支持最多 20 条公开链接、CSV、Excel、简历 PDF。平台登录后的非公开内容不做自动爬取。</p>
      </div>
      <div class="split-actions">
        <button class="primary" data-action="discover" type="button">Tavily 公开检索</button>
      </div>
    </div>
    <div class="grid-2">
      <div class="import-box">
        <h3>公开链接</h3>
        <form id="linksForm" class="form">
          <div class="field">
            <label>每行一个 URL，最多 20 条</label>
            <textarea name="links" placeholder="抖音公开主页、小红书公开主页、B站主页、淘宝直播公开信息、公司官网、公众号文章、媒体报道、招聘网站公开职位页"></textarea>
          </div>
          <div class="form-actions"><button class="primary" type="submit">采集并尝试生成候选人</button></div>
        </form>
      </div>
      <div class="import-box">
        <h3>授权文件</h3>
        <form id="fileImportForm" class="form">
          <div class="field">
            <label>CSV / Excel / 简历 PDF</label>
            <input name="file" type="file" accept=".csv,.xlsx,.pdf" required>
          </div>
          <div class="form-actions"><button class="primary" type="submit">导入文件</button></div>
        </form>
      </div>
    </div>
    <div class="section">
      <h3>导出</h3>
      <div class="split-actions">
        <button data-action="download-csv" type="button">CSV</button>
        <button data-action="download-xlsx" type="button">Excel</button>
        <button class="primary" data-action="open-report" type="button">业务人才洞察报告</button>
      </div>
      <details>
        <summary>更多：数据与合规口径</summary>
        <p class="fine muted">本工具只处理公开可读网页、你手动输入的链接，以及企业已授权文件。DeepSeek 生成的评分、推荐理由和风险提示均为辅助判断，不代表事实定论；候选人进入正式名单前应人工确认。</p>
      </details>
    </div>
  `;
}

function renderSettings() {
  setPageMeta("Settings", "设置");
  const config = state.config || {};
  byId("content").innerHTML = `
    <div class="page-head">
      <div>
        <h1>设置</h1>
        <p>填写你自己的 DeepSeek 与 Tavily Key。Key 保存在本机 SQLite，不会展示明文。</p>
      </div>
    </div>
    <div class="section">
      <form id="settingsForm" class="form">
        <div class="config-grid">
          <div class="field">
            <label>DeepSeek API Key ${config.has_deepseek_api_key ? "（已配置）" : ""}</label>
            <input name="deepseek_api_key" type="password" placeholder="sk-... 留空则不修改">
          </div>
          <div class="field">
            <label>DeepSeek 模型</label>
            <input name="deepseek_model" value="${escapeHtml(config.deepseek_model || "deepseek-chat")}">
          </div>
          <div class="field">
            <label>Tavily API Key ${config.has_tavily_api_key ? "（已配置）" : ""}</label>
            <input name="tavily_api_key" type="password" placeholder="tvly-... 留空则不修改">
          </div>
          <div class="field">
            <label>检索提供商</label>
            <select name="search_provider">
              <option value="tavily" ${config.search_provider === "tavily" ? "selected" : ""}>Tavily</option>
            </select>
          </div>
          <div class="field">
            <label>Tavily 单次结果数</label>
            <input name="tavily_max_results" type="number" min="1" max="10" value="${escapeHtml(config.tavily_max_results || "8")}">
          </div>
          <div class="field">
            <label>最多采集网页数</label>
            <input name="max_web_pages" type="number" min="1" max="80" value="${escapeHtml(config.max_web_pages || "50")}">
          </div>
        </div>
        <div class="form-actions">
          <button class="primary" type="submit">保存设置</button>
          <button class="danger" data-action="clear-deepseek" type="button">清除 DeepSeek Key</button>
          <button class="danger" data-action="clear-tavily" type="button">清除 Tavily Key</button>
        </div>
      </form>
    </div>
    <div class="section">
      <h3>更多</h3>
      <details>
        <summary>辅助爬虫和产品形态建议</summary>
        <p class="fine muted">这个需求需要 AI 辅助采集和结构化抽取，但第一版不建议做“登录爬虫插件”。更稳妥的形态是本地 Web 应用：用搜索 API 找公开网页，用 DeepSeek 抽取候选人，再由 HR 人工确认。浏览器插件适合以后做“手动打开页面后一键保存当前公开内容”，不适合绕过招聘网站或平台的访问限制。</p>
      </details>
    </div>
  `;
}

async function discoverCandidates() {
  if (!state.project) return showNotice("请先创建或选择项目。", "error");
  setBusy(true);
  try {
    const result = await api(`/api/projects/${state.project.id}/discover`, { method: "POST", body: {} });
    if (result.requires_narrowing) {
      showNotice(`${result.message} 建议：${(result.narrow_questions || []).join("；")}`, "error");
      return;
    }
    if (result.message) showNotice(result.message, result.ok ? "success" : "error");
    if (result.candidates && result.candidates.length) showNotice(`已生成候选人 ${result.candidates.length} 条，建议先逐条确认。`, "success");
    await loadProject(state.project.id);
    renderShell();
    render();
  } catch (error) {
    showNotice(error.message, "error");
  } finally {
    setBusy(false);
  }
}

function collectCandidateForm(form) {
  const data = Object.fromEntries(new FormData(form).entries());
  ["skill_tags", "past_companies", "works", "source_links", "platforms"].forEach((key) => {
    data[key] = normalizeList(data[key]);
  });
  data.status = "待评估";
  data.raw_evidence = data.source_links.length ? "手动添加，需结合来源链接人工确认。" : "手动添加，暂无来源链接。";
  return data;
}

async function saveCandidateStatus(id, status) {
  await api(`/api/candidates/${id}`, { method: "PUT", body: { status } });
  await loadProject(state.project.id);
  renderShell();
  render();
}

async function openReport() {
  const response = await fetch(`/api/projects/${state.project.id}/report.html`, { headers: { Authorization: `Bearer ${state.token}` } });
  if (!response.ok) throw new Error(await response.text());
  const html = await response.text();
  const url = URL.createObjectURL(new Blob([html], { type: "text/html;charset=utf-8" }));
  window.open(url, "_blank", "noopener,noreferrer");
}

function downloadSvg(id) {
  const svg = byId(id);
  if (!svg) return;
  const blob = new Blob([new XMLSerializer().serializeToString(svg)], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${id}.svg`;
  link.click();
  URL.revokeObjectURL(url);
}

function downloadPng(id) {
  const svg = byId(id);
  if (!svg) return;
  const serializer = new XMLSerializer();
  const text = serializer.serializeToString(svg);
  const svgBlob = new Blob([text], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(svgBlob);
  const image = new Image();
  const viewBox = svg.viewBox.baseVal;
  image.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(680, viewBox.width || 680) * 2;
    canvas.height = Math.max(320, viewBox.height || 320) * 2;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#fbfbfa";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (!blob) return;
      const pngUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = pngUrl;
      link.download = `${id}.png`;
      link.click();
      URL.revokeObjectURL(pngUrl);
      URL.revokeObjectURL(url);
    }, "image/png");
  };
  image.src = url;
}

async function handleSubmit(event) {
  if (event.target.id === "loginForm") {
    event.preventDefault();
    setBusy(true);
    try {
      const result = await api("/api/login", {
        method: "POST",
        body: { email: byId("loginEmail").value, password: byId("loginPassword").value },
      });
      state.token = result.token;
      state.user = result.user;
      localStorage.setItem("talent_map_token", state.token);
      showApp();
      await loadMeAndProjects();
      showNotice("已登录。可以从默认问答创建项目，或选择左侧已有项目。", "success");
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  }

    if (event.target.id === "wizardForm") {
      event.preventDefault();
      const q = currentQuestion();
      if (!q) return;
      const answer = byId("wizardAnswer").value.trim();
      if (!answer) {
        showNotice(canSkipQuestion(q) ? "请先输入描述、选择示例，或点击“跳过”。" : "请先输入具体应聘岗位和基础筛选范围。", "error");
        return;
      }
      await advanceWizard(answer);
    }

  if (event.target.id === "manualCandidateForm") {
    event.preventDefault();
    setBusy(true);
    try {
      const payload = collectCandidateForm(event.target);
      await api(`/api/projects/${state.project.id}/candidates`, { method: "POST", body: payload });
      await loadProject(state.project.id);
      renderShell();
      render();
      showNotice("候选人已添加。", "success");
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  }

  if (event.target.id === "linksForm") {
    event.preventDefault();
    setBusy(true);
    try {
      const links = new FormData(event.target).get("links");
      const result = await api(`/api/projects/${state.project.id}/links`, { method: "POST", body: { links } });
      await loadProject(state.project.id);
      renderShell();
      render();
      const extra = result.errors && result.errors.length ? ` 部分失败：${result.errors.slice(0, 2).join("；")}` : "";
      showNotice(`${result.message || "链接已处理"} 已生成 ${result.candidates?.length || 0} 条候选人。${extra}`, result.errors?.length ? "error" : "success");
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  }

  if (event.target.id === "fileImportForm") {
    event.preventDefault();
    setBusy(true);
    try {
      const formData = new FormData(event.target);
      const result = await api(`/api/projects/${state.project.id}/import-file`, { method: "POST", body: formData });
      await loadProject(state.project.id);
      renderShell();
      render();
      showNotice(result.message || `已导入 ${result.count || 0} 条候选人。`, "success");
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  }

  if (event.target.id === "settingsForm") {
    event.preventDefault();
    setBusy(true);
    try {
      const form = new FormData(event.target);
      const payload = {};
      for (const [key, value] of form.entries()) {
        if (String(value).trim()) payload[key] = String(value).trim();
      }
      await api("/api/config", { method: "POST", body: payload });
      state.config = (await api("/api/config")).config;
      render();
      showNotice("设置已保存。", "success");
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  }
}

async function handleClick(event) {
  const nav = event.target.closest(".nav-item");
  if (nav) {
    setView(nav.dataset.view);
    return;
  }
  const actionEl = event.target.closest("[data-action]");
  if (!actionEl) return;
  const action = actionEl.dataset.action;

  if (action === "select-project") {
    setBusy(true);
    try {
      await loadProject(Number(actionEl.dataset.id));
      renderShell();
      render();
      showNotice("");
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  }
  if (action === "new-project" || action === "go-wizard") {
    state.project = null;
    state.plan = null;
    state.candidates = [];
    state.activeProjectId = null;
    localStorage.removeItem("talent_map_active_project");
    state.view = "wizard";
    state.wizardAnswers = [];
    state.thinking = false;
    renderShell();
    render();
  }
  if (action === "reset-wizard") {
    state.wizardAnswers = [];
    state.thinking = false;
    state.project = null;
    state.plan = null;
    state.candidates = [];
    state.activeProjectId = null;
    localStorage.removeItem("talent_map_active_project");
    renderShell();
    render();
  }
    if (action === "answer-default") {
      const q = currentQuestion();
      if (!q) return;
      await advanceWizard(defaultAnswer(q));
    }
    if (action === "toggle-examples") {
      const catalog = byId("exampleCatalog");
      if (!catalog) return;
      const willOpen = catalog.hidden;
      catalog.hidden = !willOpen;
      actionEl.setAttribute("aria-expanded", String(willOpen));
    }
    if (action === "apply-example") {
      const index = Number(actionEl.dataset.exampleIndex);
      const q = currentQuestion();
      const examples = currentExampleItems(q);
      const example = exampleText(examples[index] || "");
      const textarea = byId("wizardAnswer");
      if (textarea) {
        textarea.value = example;
        textarea.focus();
      }
    }
    if (action === "skip-question") {
      const q = currentQuestion();
      if (!canSkipQuestion(q)) return;
      await advanceWizard(SKIPPED_ANSWER);
    }
  if (action === "create-default-project") {
    state.wizardAnswers = WIZARD_QUESTIONS.map((q) => ({ key: q.key, title: q.title, question: q.prompt, answer: defaultAnswer(q) }));
    setBusy(true);
    try {
      const profile = buildDraftProfile();
      const result = await api("/api/projects", {
        method: "POST",
        body: { title: inferProjectTitle(profile), answers: state.wizardAnswers, profile, saved: true },
      });
      state.project = result.project;
      state.plan = result.plan;
      state.activeProjectId = result.project.id;
      await refreshAll({ keepNotice: true });
      showNotice("默认项目已创建。", "success");
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  }
  if (action === "back-question") {
    state.wizardAnswers.pop();
    state.thinking = false;
    render();
  }
  if (action === "discover") {
    await discoverCandidates();
  }
  if (action === "show-candidates" || action === "go-imports") {
    setView(action === "show-candidates" ? "candidates" : "imports");
  }
  if (action === "set-status") {
    setBusy(true);
    try {
      await saveCandidateStatus(actionEl.dataset.id, actionEl.dataset.status);
      showNotice(`状态已更新为${actionEl.dataset.status}。`, "success");
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  }
  if (action === "download-csv") {
    setBusy(true);
    try {
      await downloadFile(`/api/projects/${state.project.id}/export.csv`, "candidates.csv");
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  }
  if (action === "download-xlsx") {
    setBusy(true);
    try {
      await downloadFile(`/api/projects/${state.project.id}/export.xlsx`, "candidates.xlsx");
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  }
  if (action === "open-report") {
    setBusy(true);
    try {
      await openReport();
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  }
  if (action === "download-svg") {
    downloadSvg(actionEl.dataset.id);
  }
  if (action === "download-png") {
    downloadPng(actionEl.dataset.id);
  }
  if (action === "copy-queries") {
    const text = (state.plan?.queries || []).join("\n");
    await navigator.clipboard.writeText(text);
    showNotice("检索式已复制。", "success");
  }
  if (action === "clear-deepseek" || action === "clear-tavily") {
    setBusy(true);
    try {
      const key = action === "clear-deepseek" ? "deepseek_api_key" : "tavily_api_key";
      await api("/api/config", { method: "POST", body: { [key]: "__clear__" } });
      state.config = (await api("/api/config")).config;
      render();
      showNotice("Key 已清除。", "success");
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  }
}

async function handleChange(event) {
  if (event.target.classList.contains("status-select")) {
    setBusy(true);
    try {
      await saveCandidateStatus(event.target.dataset.id, event.target.value);
      showNotice("状态已更新。", "success");
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  }
}

async function init() {
  document.addEventListener("submit", handleSubmit);
  document.addEventListener("click", handleClick);
  document.addEventListener("change", handleChange);
  byId("refreshBtn").addEventListener("click", async () => {
    setBusy(true);
    try {
      await loadMeAndProjects();
      showNotice("已刷新。", "success");
    } catch (error) {
      showNotice(error.message, "error");
    } finally {
      setBusy(false);
    }
  });
  byId("newProjectBtn").addEventListener("click", () => {
    state.project = null;
    state.plan = null;
    state.candidates = [];
    state.activeProjectId = null;
    state.wizardAnswers = [];
    localStorage.removeItem("talent_map_active_project");
    setView("wizard");
  });
  byId("logoutBtn").addEventListener("click", () => {
    state.token = "";
    state.user = null;
    localStorage.removeItem("talent_map_token");
    localStorage.removeItem("talent_map_active_project");
    showLogin();
    showNotice("");
  });

  if (!state.token) {
    showLogin();
    return;
  }
  showApp();
  setBusy(true);
  try {
    await loadMeAndProjects();
  } catch (error) {
    state.token = "";
    localStorage.removeItem("talent_map_token");
    showLogin();
    showNotice("登录已过期，请重新登录。", "error");
  } finally {
    setBusy(false);
  }
}

init();
