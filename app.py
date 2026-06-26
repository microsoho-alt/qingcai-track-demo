import re
import math
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    from docx import Document
except Exception:
    Document = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

st.set_page_config(
    page_title="青才轨道｜苏州青年留才AI Demo",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Style
# -----------------------------
st.markdown(
    """
    <style>
    :root{
        --bg:#f6f8fb;
        --card:#ffffff;
        --line:#e8edf4;
        --ink:#0f172a;
        --muted:#64748b;
        --blue:#1d4ed8;
        --cyan:#0891b2;
        --purple:#6d28d9;
        --green:#059669;
        --orange:#ea580c;
        --red:#dc2626;
    }
    .stApp{background:linear-gradient(180deg,#f7faff 0%,#f8fafc 52%,#eef3fb 100%); color:var(--ink);}    
    /* 侧边栏：改为浅色政务表单风格，保证所有输入项可读 */
    section[data-testid="stSidebar"]{
        background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%) !important;
        border-right:1px solid #dbe3ee;
        box-shadow:8px 0 28px rgba(15,23,42,.06);
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3{
        color:#0f172a !important;
        font-weight:900 !important;
        letter-spacing:-0.02em;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"]{
        color:#1e293b !important;
    }
    section[data-testid="stSidebar"] label{
        font-weight:800 !important;
    }
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] [data-baseweb="input"] > div,
    section[data-testid="stSidebar"] [data-baseweb="textarea"] > div{
        background:#ffffff !important;
        color:#0f172a !important;
        border:1px solid #cbd5e1 !important;
        border-radius:12px !important;
        box-shadow:0 1px 2px rgba(15,23,42,.05) !important;
    }
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] div[data-baseweb="select"] span,
    section[data-testid="stSidebar"] div[data-baseweb="select"] input,
    section[data-testid="stSidebar"] [data-baseweb="input"] input,
    section[data-testid="stSidebar"] [data-baseweb="textarea"] textarea{
        color:#0f172a !important;
        -webkit-text-fill-color:#0f172a !important;
        caret-color:#1d4ed8 !important;
    }
    section[data-testid="stSidebar"] input::placeholder,
    section[data-testid="stSidebar"] textarea::placeholder{
        color:#64748b !important; opacity:1 !important;
        -webkit-text-fill-color:#64748b !important;
    }
    section[data-testid="stSidebar"] button{
        background:#eff6ff !important;
        color:#1d4ed8 !important;
        border:1px solid #bfdbfe !important;
        border-radius:10px !important;
        font-weight:800 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"]{
        background:#ffffff !important;
        border:1.5px dashed #94a3b8 !important;
        border-radius:16px !important;
        color:#0f172a !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"] *{
        color:#334155 !important;
        -webkit-text-fill-color:#334155 !important;
    }
    section[data-testid="stSidebar"] small,
    section[data-testid="stSidebar"] span{
        color:inherit;
    }
    section[data-testid="stSidebar"] hr{border-color:#e2e8f0 !important;}
    .block-container{padding-top:1.25rem; padding-bottom:3rem; max-width:1440px;}
    h1,h2,h3{letter-spacing:-0.025em;}
    .hero{
        padding:28px 32px; border-radius:28px;
        background: radial-gradient(circle at 10% 10%, rgba(59,130,246,.38), transparent 30%),
                    radial-gradient(circle at 80% 20%, rgba(124,58,237,.26), transparent 28%),
                    linear-gradient(135deg,#0b1220 0%,#102a56 48%,#123b5f 100%);
        color:white; box-shadow:0 24px 60px rgba(15,23,42,.22); position:relative; overflow:hidden;
        margin-bottom:18px;
    }
    .hero:after{content:""; position:absolute; width:300px; height:300px; right:-80px; top:-120px; background:rgba(255,255,255,.08); border-radius:999px;}
    .hero .kicker{font-size:14px; opacity:.88; font-weight:700; letter-spacing:.22em; text-transform:uppercase;}
    .hero h1{font-size:38px; line-height:1.16; margin:10px 0 10px 0; color:white;}
    .hero p{font-size:17px; color:#dbeafe; max-width:980px; line-height:1.72; margin:0;}
    .badge{display:inline-block; padding:6px 11px; border-radius:999px; background:rgba(255,255,255,.13); border:1px solid rgba(255,255,255,.2); margin-right:8px; margin-top:14px; font-size:13px; color:#f8fafc;}
    .card{background:rgba(255,255,255,.92); border:1px solid var(--line); border-radius:22px; padding:20px 22px; box-shadow:0 12px 34px rgba(15,23,42,.07); margin-bottom:16px;}
    .card-tight{background:rgba(255,255,255,.94); border:1px solid var(--line); border-radius:18px; padding:16px 18px; box-shadow:0 8px 22px rgba(15,23,42,.06); margin-bottom:14px;}
    .section-title{font-size:24px; font-weight:900; color:#0f172a; margin:8px 0 6px 0;}
    .section-sub{font-size:14px; color:#64748b; line-height:1.65; margin-bottom:12px;}
    .metric-card{background:#fff; border:1px solid #e5e7eb; border-radius:18px; padding:16px; min-height:120px; box-shadow:0 8px 20px rgba(15,23,42,.05);}
    .metric-label{font-size:13px; color:#64748b; font-weight:700;}
    .metric-value{font-size:30px; font-weight:900; color:#0f172a; margin:4px 0;}
    .metric-note{font-size:12px; color:#64748b; line-height:1.45;}
    .pill{display:inline-block; padding:5px 10px; border-radius:999px; background:#eff6ff; color:#1d4ed8; font-weight:800; font-size:12px; margin:3px 5px 3px 0; border:1px solid #dbeafe;}
    .pill-green{background:#ecfdf5; color:#047857; border-color:#d1fae5;}
    .pill-orange{background:#fff7ed; color:#c2410c; border-color:#fed7aa;}
    .pill-purple{background:#f5f3ff; color:#6d28d9; border-color:#ddd6fe;}
    .pill-red{background:#fef2f2; color:#b91c1c; border-color:#fecaca;}
    .timeline{border-left:3px solid #dbeafe; padding-left:16px; margin-left:6px;}
    .timeline-item{position:relative; padding:4px 0 16px 0;}
    .timeline-item:before{content:""; position:absolute; left:-24px; top:8px; width:13px; height:13px; background:#2563eb; border:3px solid #eff6ff; border-radius:999px;}
    .timeline-title{font-weight:900; color:#0f172a; font-size:16px;}
    .timeline-body{color:#475569; font-size:14px; line-height:1.7;}
    .route-card{border:1px solid #e5e7eb; border-radius:20px; padding:18px; background:linear-gradient(180deg,#fff,#f8fafc); margin-bottom:14px;}
    .route-card.best{border:2px solid #2563eb; box-shadow:0 14px 35px rgba(37,99,235,.13);}
    .route-head{display:flex; align-items:flex-start; justify-content:space-between; gap:12px;}
    .route-title{font-size:20px; font-weight:900; color:#0f172a;}
    .score-bubble{background:#eff6ff; color:#1d4ed8; font-weight:900; border-radius:999px; padding:8px 12px; font-size:14px; white-space:nowrap;}
    .gov-report{background:#fff; border:1px solid #dbeafe; border-radius:22px; padding:26px; box-shadow:0 18px 48px rgba(30,64,175,.08); line-height:1.75;}
    .gov-report h2{border-bottom:2px solid #dbeafe; padding-bottom:8px;}
    .small-muted{font-size:12px; color:#64748b;}
    .warning-box{border-left:5px solid #ea580c; background:#fff7ed; padding:14px 16px; border-radius:14px; color:#7c2d12; line-height:1.7;}
    .success-box{border-left:5px solid #059669; background:#ecfdf5; padding:14px 16px; border-radius:14px; color:#064e3b; line-height:1.7;}
    .info-box{border-left:5px solid #2563eb; background:#eff6ff; padding:14px 16px; border-radius:14px; color:#1e3a8a; line-height:1.7;}
    div[data-testid="stHorizontalBlock"]{gap:1rem;}
    .stTabs [data-baseweb="tab-list"]{gap:8px; border-bottom:1px solid #e2e8f0;}
    .stTabs [data-baseweb="tab"]{height:46px; border-radius:14px 14px 0 0; padding:10px 14px; font-weight:800;}
    .stTabs [aria-selected="true"]{background:#eff6ff; color:#1d4ed8;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Data
# -----------------------------
POLICY_DB = [
    {
        "level": "苏州市级",
        "name": "来苏求职面试交通补贴",
        "target": "全日制应届本科及以上毕业生来苏求职面试",
        "value": "最高2000元一次性交通补贴",
        "conditions": "应届、来苏面试、按主管部门规定提交材料",
        "risk": "以当年度人社/人才部门申报通知为准",
        "tags": ["来苏第一站", "面试", "应届"],
    },
    {
        "level": "苏州市级",
        "name": "青年人才驿站",
        "target": "来苏求职、面试、实习青年",
        "value": "单次3天2晚，累计最长14天免费住宿服务",
        "conditions": "需提前预约，符合入住条件，房源以实际供给为准",
        "risk": "具体入住资格、站点和房源以平台审核为准",
        "tags": ["住宿", "求职", "来苏"],
    },
    {
        "level": "苏州市级",
        "name": "青年人才租房补贴",
        "target": "新引进全日制应届博士、硕士、本科生",
        "value": "博士不低于1500元/月、硕士不低于1000元/月、本科不低于800元/月，期限一般2年",
        "conditions": "新引进、应届、就业社保等条件需满足主管部门口径",
        "risk": "不同年度、不同区域可能有细则差异，系统只做资格预评估",
        "tags": ["租房", "应届", "市级基础包"],
    },
    {
        "level": "苏州工业园区",
        "name": "重点产业紧缺人才生活补贴",
        "target": "符合园区重点产业紧缺人才目录的应届毕业生",
        "value": "本科1万/年、硕士2万/年、博士3万/年；高紧缺等级可进一步提高，连续两年",
        "conditions": "单位、岗位、学历、专业、职责需匹配目录；通常需劳动合同和社保条件",
        "risk": "须以园区当年度紧缺目录、企业资质和岗位审核为准",
        "tags": ["园区", "紧缺岗位", "高端产业"],
    },
    {
        "level": "吴中区",
        "name": "人才房票资格评估",
        "target": "符合吴中人才政策条件的学历型、技能型或产业人才",
        "value": "博士、硕士、本科、大专及技能人才对应不同房票支持额度",
        "conditions": "一般涉及就业创业、社保/个税连续缴纳、人才类别等条件",
        "risk": "房票属于中长期安居政策，系统只做三年路径预评估，不承诺取得",
        "tags": ["吴中", "安居", "房票"],
    },
    {
        "level": "相城区",
        "name": "重点产业骨干人才房票资格评估",
        "target": "相城重点产业企业骨干人才、紧缺人才、学历型人才",
        "value": "本科、硕士、博士及紧缺人才对应不同房票支持额度",
        "conditions": "与重点产业、企业资质、社保、人才类别认定有关",
        "risk": "需以相城区当年度申报细则和审核结果为准",
        "tags": ["相城", "重点产业", "房票"],
    },
    {
        "level": "就业创业政策",
        "name": "就业见习补贴与职业培训补贴联动",
        "target": "离校未就业高校毕业生、16-24岁登记失业青年、毕业年度高校毕业生等",
        "value": "见习补贴、就业技能培训补贴、企业新录用高校毕业生岗位技能培训补贴等",
        "conditions": "需匹配人员身份、培训类型、证书或合格证明、企业录用等条件",
        "risk": "由主管部门按现行政策审核，系统用于路径推荐和材料提醒",
        "tags": ["培训", "见习", "技能补齐"],
    },
]

ROUTES = {
    "智能制造设备工程轨道": {
        "industries": ["智能制造", "高端装备", "工业互联网"],
        "regions": ["工业园区", "相城区", "高新区"],
        "first_jobs": ["设备助理工程师", "自动化助理工程师", "设备运维技术员"],
        "one_year": "设备工程师 / 产线运维工程师",
        "three_year": "产线数字化工程师 / 工艺改善工程师",
        "skills": ["机械制图", "Excel", "PLC基础", "MES工单", "设备点检", "异常记录"],
        "training": ["PLC基础认知", "MES工单流程", "设备点检记录", "安全生产基础", "异常上报规范"],
        "policy_focus": ["市级租房补贴", "青年人才驿站", "园区紧缺岗位生活补贴", "职业培训补贴", "就业见习补贴"],
        "salary_start": "6k-8k",
        "salary_3y": "10k-15k",
        "why": "苏州智能制造、高端装备和工业互联网企业密度高，机械、自动化、机电类青年容易通过首岗进入产业链。",
    },
    "新能源材料与工艺轨道": {
        "industries": ["新能源", "先进材料", "光伏储能"],
        "regions": ["相城区", "吴中区", "工业园区"],
        "first_jobs": ["材料研发助理", "工艺助理工程师", "实验室技术员"],
        "one_year": "工艺工程师 / 材料测试工程师",
        "three_year": "研发工程师 / 工艺平台负责人助理",
        "skills": ["材料基础", "实验记录", "数据分析", "质量体系", "工艺参数", "英文文献"],
        "training": ["实验数据规范", "工艺参数记录", "质量体系基础", "研发周报写作", "产业链知识"],
        "policy_focus": ["市级租房补贴", "园区/相城重点产业政策", "吴中房票资格评估", "见习补贴"],
        "salary_start": "7k-10k",
        "salary_3y": "12k-18k",
        "why": "苏州新能源、先进材料和高端制造基础较强，硕士或理工本科可通过研发助理/工艺助理岗位切入。",
    },
    "数字贸易与跨境运营轨道": {
        "industries": ["数字贸易", "跨境电商", "品牌出海"],
        "regions": ["吴中区", "工业园区", "高新区"],
        "first_jobs": ["跨境运营助理", "海外内容助理", "外贸客户开发助理"],
        "one_year": "跨境运营专员 / 海外营销专员",
        "three_year": "独立站运营 / 海外增长负责人助理",
        "skills": ["英语", "内容生成", "平台规则", "产品分析", "客户开发", "数据复盘"],
        "training": ["AI英文卖点生成", "海外平台标题", "客户开发邮件", "竞品分析", "短视频脚本"],
        "policy_focus": ["市级青年政策", "吴中安居评估", "职业培训补贴", "见习实训"],
        "salary_start": "5.5k-8k",
        "salary_3y": "9k-16k",
        "why": "苏州制造企业出海需求上升，数字贸易岗位适合外语、国贸、电商、营销类青年转化。",
    },
    "AI办公与企业数字化服务轨道": {
        "industries": ["企业服务", "数字化转型", "人力资源服务"],
        "regions": ["工业园区", "姑苏区", "相城区", "吴中区"],
        "first_jobs": ["AI办公助理", "数据运营助理", "人事共享服务专员"],
        "one_year": "数字化运营专员 / HR共享服务专员",
        "three_year": "企业数字化项目专员 / 人效数据分析师",
        "skills": ["Excel", "PPT", "AI工具", "流程梳理", "数据整理", "沟通协调"],
        "training": ["AI文档生成", "Excel数据清洗", "会议纪要", "流程SOP", "人效报表"],
        "policy_focus": ["市级租房补贴", "职业技能培训", "青年夜校/公益培训", "企业新录用培训补贴"],
        "salary_start": "5k-7k",
        "salary_3y": "8k-13k",
        "why": "大量中小企业正在补数字化运营能力，文科、商科青年可通过AI办公和数据运营能力实现留苏就业。",
    },
    "生物医药质量与注册轨道": {
        "industries": ["生物医药", "医疗器械", "质量合规"],
        "regions": ["工业园区", "高新区", "吴中区"],
        "first_jobs": ["QA助理", "注册助理", "实验室文控专员"],
        "one_year": "QA专员 / 注册事务专员",
        "three_year": "质量体系工程师 / 注册项目专员",
        "skills": ["生物医药基础", "GMP", "文档规范", "英文资料", "法规意识", "质量记录"],
        "training": ["GMP基础", "质量记录", "注册资料整理", "审计清单", "法规检索"],
        "policy_focus": ["园区紧缺岗位生活补贴", "市级租房补贴", "职业培训", "见习基地"],
        "salary_start": "6k-9k",
        "salary_3y": "10k-16k",
        "why": "苏州生物医药和医疗器械产业链完整，适合生物、药学、化学、医学相关专业青年形成长期轨道。",
    },
}

CASE_PROFILES = {
    "正式版：手动填写/上传简历": None,
    "案例A｜机械本科应届生：想留苏但缺经验": {
        "name": "小张",
        "age": 22,
        "education": "本科",
        "major": "机械设计制造及其自动化",
        "grad_status": "2026届应届毕业生",
        "work_years": 0,
        "preferred_industry": "智能制造",
        "expected_salary": 7000,
        "rent_budget": 1800,
        "commute": 60,
        "preferred_regions": ["工业园区", "相城区", "高新区"],
        "skills": ["机械制图", "CAD", "Excel", "基础设备认知"],
        "pain": "没有实习经验，投递设备工程师岗位经常被要求2年经验。",
    },
    "案例B｜材料硕士：纠结苏州和上海": {
        "name": "小陈",
        "age": 25,
        "education": "硕士",
        "major": "材料科学与工程",
        "grad_status": "2026届应届毕业生",
        "work_years": 0,
        "preferred_industry": "新能源",
        "expected_salary": 10000,
        "rent_budget": 2500,
        "commute": 50,
        "preferred_regions": ["相城区", "吴中区", "工业园区"],
        "skills": ["材料基础", "实验记录", "英文文献", "数据分析"],
        "pain": "上海机会多但成本高，想知道苏州是否有长期成长空间。",
    },
    "案例C｜工作2年工程师：有离苏风险": {
        "name": "小王",
        "age": 25,
        "education": "本科",
        "major": "自动化",
        "grad_status": "已毕业",
        "work_years": 2,
        "preferred_industry": "智能制造",
        "expected_salary": 9500,
        "rent_budget": 2200,
        "commute": 75,
        "preferred_regions": ["相城区", "工业园区", "高新区"],
        "skills": ["PLC基础", "设备点检", "MES工单", "异常记录", "班组沟通"],
        "pain": "当前企业薪资成长停滞，通勤时间长，正在考虑去上海或杭州。",
    },
    "案例D｜文科本科：想转AI办公/企业服务": {
        "name": "小林",
        "age": 23,
        "education": "本科",
        "major": "人力资源管理",
        "grad_status": "离校未就业青年",
        "work_years": 0,
        "preferred_industry": "企业服务",
        "expected_salary": 6000,
        "rent_budget": 1600,
        "commute": 45,
        "preferred_regions": ["姑苏区", "相城区", "吴中区"],
        "skills": ["Excel", "PPT", "沟通协调", "活动组织"],
        "pain": "不知道文科专业在苏州能进入哪条数字化岗位轨道。",
    },
}

INDUSTRY_HINTS = {
    "智能制造": ["智能制造设备工程轨道", "AI办公与企业数字化服务轨道"],
    "新能源": ["新能源材料与工艺轨道", "智能制造设备工程轨道"],
    "跨境电商": ["数字贸易与跨境运营轨道", "AI办公与企业数字化服务轨道"],
    "生物医药": ["生物医药质量与注册轨道", "AI办公与企业数字化服务轨道"],
    "企业服务": ["AI办公与企业数字化服务轨道", "数字贸易与跨境运营轨道"],
    "不确定": ["AI办公与企业数字化服务轨道", "智能制造设备工程轨道"],
}

# -----------------------------
# Utilities
# -----------------------------
def extract_text_from_upload(uploaded_file):
    if uploaded_file is None:
        return ""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".txt"):
            return uploaded_file.read().decode("utf-8", errors="ignore")
        if name.endswith(".docx") and Document is not None:
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        if name.endswith(".pdf") and PdfReader is not None:
            reader = PdfReader(uploaded_file)
            texts = []
            for page in reader.pages[:5]:
                texts.append(page.extract_text() or "")
            return "\n".join(texts)
    except Exception as e:
        return f"简历解析失败：{e}"
    return "暂不支持该格式自动解析，可在下方手动补充。"


def infer_from_resume(text: str) -> Dict:
    text = text or ""
    profile = {}
    if "硕士" in text or "研究生" in text:
        profile["education"] = "硕士"
    elif "博士" in text:
        profile["education"] = "博士"
    elif "本科" in text or "学士" in text:
        profile["education"] = "本科"
    elif "大专" in text or "专科" in text:
        profile["education"] = "大专"
    majors = ["机械", "自动化", "材料", "新能源", "计算机", "软件", "生物", "药学", "化学", "英语", "国贸", "电商", "人力资源", "工商管理"]
    for m in majors:
        if m in text:
            profile["major"] = m
            break
    skills = []
    skill_keywords = ["Excel", "PPT", "Python", "CAD", "PLC", "MES", "WMS", "英语", "数据分析", "机械制图", "短视频", "跨境", "实验", "质量", "GMP", "AI"]
    for s in skill_keywords:
        if s.lower() in text.lower():
            skills.append(s)
    if skills:
        profile["skills"] = list(dict.fromkeys(skills))
    return profile


def score_route(profile: Dict, route_name: str, route: Dict) -> Tuple[int, List[str], List[str]]:
    score = 42
    skills = set([s.lower() for s in profile.get("skills", [])])
    route_skills = route["skills"]
    matched = []
    missing = []
    for s in route_skills:
        if any(s.lower() in x or x in s.lower() for x in skills):
            matched.append(s)
        else:
            missing.append(s)
    score += min(26, len(matched) * 6)

    major = profile.get("major", "")
    pref = profile.get("preferred_industry", "")
    if pref in route["industries"] or any(pref in i or i in pref for i in route["industries"]):
        score += 14
    if any(k in major for k in ["机械", "自动化", "机电"]) and "智能制造" in route["industries"]:
        score += 12
    if any(k in major for k in ["材料", "化学", "新能源"]) and "新能源" in route["industries"]:
        score += 12
    if any(k in major for k in ["生物", "药学", "医学", "化学"]) and "生物医药" in route["industries"]:
        score += 12
    if any(k in major for k in ["英语", "国贸", "电商", "营销"]) and "数字贸易" in route["industries"]:
        score += 12
    if any(k in major for k in ["人力", "管理", "中文", "新闻", "工商"]) and "企业服务" in route["industries"]:
        score += 10

    preferred_regions = set(profile.get("preferred_regions", []))
    if preferred_regions.intersection(set(route["regions"])):
        score += 8
    work_years = profile.get("work_years", 0)
    if work_years >= 2:
        score += 4
    if "应届" in profile.get("grad_status", "") and route_name in ["智能制造设备工程轨道", "AI办公与企业数字化服务轨道"]:
        score += 3
    return min(score, 96), matched, missing[:5]


def match_routes(profile: Dict):
    results = []
    for name, route in ROUTES.items():
        score, matched, missing = score_route(profile, name, route)
        results.append({"name": name, "score": score, "matched": matched, "missing": missing, **route})
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    return results


def policy_matches(profile: Dict, top_route: Dict):
    matched = []
    edu = profile.get("education", "本科")
    grad = profile.get("grad_status", "")
    regions = profile.get("preferred_regions", []) + top_route.get("regions", [])
    for p in POLICY_DB:
        ok = False
        if "应届" in grad and any(t in p["tags"] for t in ["应届", "来苏", "租房", "面试"]):
            ok = True
        if any(r.replace("区", "") in p["level"] for r in regions):
            ok = True
        if any(tag in p["tags"] for tag in ["培训", "见习"]) and (top_route.get("missing") or "离校未就业" in grad):
            ok = True
        if "硕士" in edu or "博士" in edu:
            if "紧缺" in p["name"] or "生活补贴" in p["name"]:
                ok = True
        if ok:
            matched.append(p)
    # always include baseline city policies for demo
    baseline = [p for p in POLICY_DB if p["level"] == "苏州市级"]
    final = []
    for p in baseline + matched:
        if p["name"] not in [x["name"] for x in final]:
            final.append(p)
    return final[:7]


def retention_risk(profile: Dict, top_route: Dict):
    risk = 18
    factors = []
    if profile.get("commute", 45) > 65:
        risk += 22
        factors.append("通勤半径偏长，入职90天内流失风险上升")
    if profile.get("rent_budget", 1800) < 1800 and "工业园区" in top_route.get("regions", []):
        risk += 12
        factors.append("租房预算与推荐区域成本可能存在错配")
    if profile.get("expected_salary", 7000) > 9000 and profile.get("work_years", 0) == 0:
        risk += 12
        factors.append("薪资预期高于首岗常见区间，需要用政策包和成长路径缓冲")
    if profile.get("work_years", 0) >= 2 and "薪资" in profile.get("pain", ""):
        risk += 18
        factors.append("已有工作经验但薪资成长停滞，存在外流或跳槽风险")
    if len(top_route.get("missing", [])) >= 4:
        risk += 10
        factors.append("岗位技能缺口较多，若直接入职可能适应慢")
    if not factors:
        factors.append("当前风险主要来自首岗选择不确定，需用见习和政策触达提升稳定性")
    risk = min(risk, 88)
    level = "低" if risk < 35 else "中" if risk < 62 else "高"
    return risk, level, factors


def gauge(value, title, suffix="分"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": suffix, "font": {"size": 34}},
        title={"text": title, "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": "#2563eb"},
            "bgcolor": "white",
            "borderwidth": 1,
            "bordercolor": "#e5e7eb",
            "steps": [
                {"range": [0, 40], "color": "#fee2e2"},
                {"range": [40, 70], "color": "#ffedd5"},
                {"range": [70, 100], "color": "#dcfce7"},
            ],
        },
    ))
    fig.update_layout(height=240, margin=dict(l=20, r=20, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def progress_bar(value, label, color="#2563eb"):
    st.markdown(f"""
    <div style='margin:8px 0 12px 0;'>
      <div style='display:flex;justify-content:space-between;font-size:13px;font-weight:800;color:#334155;margin-bottom:5px;'><span>{label}</span><span>{value}%</span></div>
      <div style='height:10px;background:#e5e7eb;border-radius:999px;overflow:hidden;'>
        <div style='width:{value}%;height:10px;background:{color};border-radius:999px;'></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def profile_input():
    st.sidebar.markdown("### 演示模式")
    case_name = st.sidebar.selectbox("选择样本或正式填写", list(CASE_PROFILES.keys()), index=1)
    base = CASE_PROFILES[case_name] or {
        "name": "",
        "age": 22,
        "education": "本科",
        "major": "",
        "grad_status": "2026届应届毕业生",
        "work_years": 0,
        "preferred_industry": "不确定",
        "expected_salary": 7000,
        "rent_budget": 1800,
        "commute": 60,
        "preferred_regions": ["工业园区", "相城区"],
        "skills": [],
        "pain": "",
    }
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 正式入口：简历上传")
    uploaded = st.sidebar.file_uploader("上传简历 PDF / DOCX / TXT", type=["pdf", "docx", "txt"], help="演示版支持本地解析部分文本，不上传外部服务器。")
    resume_text = extract_text_from_upload(uploaded)
    inferred = infer_from_resume(resume_text)
    if resume_text:
        with st.sidebar.expander("查看简历解析文本", expanded=False):
            st.write(resume_text[:1500])
    for k, v in inferred.items():
        if k == "skills":
            base["skills"] = list(dict.fromkeys(base.get("skills", []) + v))
        elif not base.get(k):
            base[k] = v
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 青年画像校准")
    name = st.sidebar.text_input("姓名/昵称", value=base.get("name", ""))
    age = st.sidebar.number_input("年龄", min_value=18, max_value=45, value=int(base.get("age", 22)))
    education = st.sidebar.selectbox("最高学历", ["大专", "本科", "硕士", "博士"], index=["大专", "本科", "硕士", "博士"].index(base.get("education", "本科")) if base.get("education", "本科") in ["大专", "本科", "硕士", "博士"] else 1)
    major = st.sidebar.text_input("专业", value=base.get("major", ""))
    grad_status = st.sidebar.selectbox("毕业/就业状态", ["2026届应届毕业生", "毕业年度高校毕业生", "离校未就业青年", "已毕业", "已在苏工作"], index=["2026届应届毕业生", "毕业年度高校毕业生", "离校未就业青年", "已毕业", "已在苏工作"].index(base.get("grad_status", "2026届应届毕业生")) if base.get("grad_status") in ["2026届应届毕业生", "毕业年度高校毕业生", "离校未就业青年", "已毕业", "已在苏工作"] else 0)
    work_years = st.sidebar.slider("工作年限", 0, 10, int(base.get("work_years", 0)))
    preferred_industry = st.sidebar.selectbox("意向产业", ["不确定", "智能制造", "新能源", "跨境电商", "生物医药", "企业服务"], index=["不确定", "智能制造", "新能源", "跨境电商", "生物医药", "企业服务"].index(base.get("preferred_industry", "不确定")) if base.get("preferred_industry") in ["不确定", "智能制造", "新能源", "跨境电商", "生物医药", "企业服务"] else 0)
    expected_salary = st.sidebar.slider("期望月薪", 4000, 20000, int(base.get("expected_salary", 7000)), step=500)
    rent_budget = st.sidebar.slider("可接受月租", 800, 5000, int(base.get("rent_budget", 1800)), step=100)
    commute = st.sidebar.slider("可接受通勤分钟", 20, 120, int(base.get("commute", 60)), step=5)
    regions = st.sidebar.multiselect("偏好区域", ["工业园区", "相城区", "吴中区", "高新区", "姑苏区", "昆山市", "太仓市", "张家港市"], default=base.get("preferred_regions", ["工业园区", "相城区"]))
    skills_text = st.sidebar.text_area("已有技能（用顿号/逗号分隔）", value="、".join(base.get("skills", [])), height=80)
    pain = st.sidebar.text_area("当前困惑", value=base.get("pain", ""), height=90)
    skills = [s.strip() for s in re.split(r"[、,，\n/]+", skills_text) if s.strip()]
    return {
        "case_name": case_name,
        "name": name or "青年用户",
        "age": age,
        "education": education,
        "major": major,
        "grad_status": grad_status,
        "work_years": work_years,
        "preferred_industry": preferred_industry,
        "expected_salary": expected_salary,
        "rent_budget": rent_budget,
        "commute": commute,
        "preferred_regions": regions,
        "skills": skills,
        "pain": pain,
        "resume_text": resume_text,
        "uploaded": uploaded.name if uploaded else "未上传",
    }

# -----------------------------
# App
# -----------------------------
profile = profile_input()
routes = match_routes(profile)
top = routes[0]
policies = policy_matches(profile, top)
risk_score, risk_level, risk_factors = retention_risk(profile, top)
readiness = top["score"]
policy_fit = min(96, 55 + len(policies) * 6 + (8 if profile.get("education") in ["硕士", "博士"] else 0))
city_fit = round((readiness * 0.48 + policy_fit * 0.28 + (100 - risk_score) * 0.24), 1)

st.markdown(
    f"""
    <div class="hero">
      <div class="kicker">SUZHOU YOUTH CAREER TRACK AI · DEMO</div>
      <h1>青才轨道｜AI驱动的苏州青年职业发展路线图</h1>
      <p>不是再做一个招聘网站，而是把青年画像、苏州产业岗位、各区人才政策、技能补齐资源、见习机会和留才预警连接起来，为每个青年生成一份可执行、可追踪、可优化的“留苏发展方案”。</p>
      <span class="badge">首岗匹配</span><span class="badge">政策礼包</span><span class="badge">技能补齐</span><span class="badge">三年留苏</span><span class="badge">政府驾驶舱</span>
    </div>
    """,
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>留苏综合适配度</div><div class='metric-value'>{city_fit}</div><div class='metric-note'>综合岗位、政策、成本与留才风险。</div></div>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>首岗匹配度</div><div class='metric-value'>{readiness}%</div><div class='metric-note'>与推荐产业轨道首岗要求的匹配程度。</div></div>", unsafe_allow_html=True)
with k3:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>政策匹配项</div><div class='metric-value'>{len(policies)}</div><div class='metric-note'>市级、区级、培训、见习等可评估政策。</div></div>", unsafe_allow_html=True)
with k4:
    color = "#059669" if risk_level == "低" else "#ea580c" if risk_level == "中" else "#dc2626"
    st.markdown(f"<div class='metric-card'><div class='metric-label'>90天留才风险</div><div class='metric-value' style='color:{color}'>{risk_level}</div><div class='metric-note'>用于提前触发政策、安居、企业带教或本地接力。</div></div>", unsafe_allow_html=True)

st.markdown("<div class='info-box'><b>大学生最想看到的不是一堆岗位。</b>他真正想知道：我适合留在苏州哪条产业路线上？第一份工作怎么选？差哪些技能？能拿哪些政策？租房通勤扛不扛得住？三年后有没有更好的公司和安居可能？本Demo围绕这些问题组织输出。</div>", unsafe_allow_html=True)

tabs = st.tabs([
    "① 我的留苏路线总览",
    "② 首岗与产业轨道",
    "③ 技能补齐计划",
    "④ 苏州政策礼包",
    "⑤ 安居与三年计划",
    "⑥ 留才预警与本地接力",
    "⑦ 政府驾驶舱",
    "⑧ 专业报告"
])

with tabs[0]:
    st.markdown("<div class='section-title'>一页看懂：这名青年为什么适合留苏、怎么留苏</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>本页给青年看的核心答案：推荐轨道、当前短板、政策支持、下一步动作。不要先给一堆数据，要先把路线说清楚。</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1.15, .85])
    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"### {profile['name']} 的苏州职业路线建议")
        st.markdown(f"<span class='pill'>推荐主轨道</span> <b style='font-size:22px'>{top['name']}</b>", unsafe_allow_html=True)
        st.write(top["why"])
        st.markdown("#### 系统判断")
        st.markdown(f"- **第一步首岗**：{ ' / '.join(top['first_jobs'][:2]) }")
        st.markdown(f"- **一年目标**：{top['one_year']}")
        st.markdown(f"- **三年目标**：{top['three_year']}")
        st.markdown(f"- **适配区域**：{'、'.join(top['regions'])}")
        st.markdown(f"- **薪资轨迹**：首岗约 {top['salary_start']}，三年成熟后约 {top['salary_3y']}")
        st.markdown("#### 现在最该做的三件事")
        st.markdown(f"1. 先进入 **{top['first_jobs'][0]}** 候选池，不要盲投所有岗位。")
        st.markdown(f"2. 用 **7-14天岗位技能补齐包** 补齐：{'、'.join(top['missing'][:3]) if top['missing'] else '基础能力已较完整，建议直接进入企业面试/见习'}。")
        st.markdown("3. 同步评估市级基础政策和区级产业政策，把求职、租房、见习、培训放到同一条路线上。")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.plotly_chart(gauge(city_fit, "留苏综合适配度"), use_container_width=True)
        st.markdown("<div class='card-tight'>", unsafe_allow_html=True)
        st.markdown("#### 青年画像")
        df = pd.DataFrame([
            ["学历", profile["education"]], ["专业", profile["major"] or "未填写"], ["状态", profile["grad_status"]],
            ["意向产业", profile["preferred_industry"]], ["期望月薪", f"{profile['expected_salary']}元"],
            ["租房预算", f"{profile['rent_budget']}元/月"], ["可接受通勤", f"{profile['commute']}分钟"], ["简历入口", profile["uploaded"]]
        ], columns=["字段", "内容"])
        st.dataframe(df, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with tabs[1]:
    st.markdown("<div class='section-title'>首岗不是终点，轨道才是重点</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>普通招聘平台推荐岗位；青才轨道推荐的是“首岗—一年岗—三年岗—本地接力企业群”。</div>", unsafe_allow_html=True)
    for i, r in enumerate(routes[:3]):
        best = " best" if i == 0 else ""
        st.markdown(f"<div class='route-card{best}'>", unsafe_allow_html=True)
        st.markdown(f"<div class='route-head'><div><div class='route-title'>{'⭐ ' if i==0 else ''}{r['name']}</div><div class='small-muted'>{r['why']}</div></div><div class='score-bubble'>{r['score']}% 匹配</div></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        a, b, c, d = st.columns(4)
        a.markdown(f"**首岗入口**  \n{r['first_jobs'][0]}")
        b.markdown(f"**一年目标**  \n{r['one_year']}")
        c.markdown(f"**三年目标**  \n{r['three_year']}")
        d.markdown(f"**适配区域**  \n{'、'.join(r['regions'])}")
        st.markdown("**已匹配能力**：" + (" ".join([f"<span class='pill-green'>{x}</span>" for x in r['matched']]) if r['matched'] else "<span class='pill-orange'>能力记录不足，需要先做测评任务</span>"), unsafe_allow_html=True)
        st.markdown("**需补齐能力**：" + (" ".join([f"<span class='pill-orange'>{x}</span>" for x in r['missing']]) if r['missing'] else "<span class='pill-green'>暂无明显短板</span>"), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with tabs[2]:
    st.markdown("<div class='section-title'>技能补齐计划：把培训变成岗位入场券</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>系统不泛泛推荐课程，而是从目标岗位倒推最小技能缺口。补齐后生成岗位能力记录，可进入企业见习/实训/面试候选池。</div>", unsafe_allow_html=True)
    left, right = st.columns([1, 1])
    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### 7-14天岗位技能补齐包")
        training = top["training"]
        days = []
        for idx, item in enumerate(training[:5], start=1):
            days.append({"周期": f"第{idx}阶段", "训练任务": item, "考核方式": "AI任务评分 + 导师/企业复核", "结果沉淀": "写入岗位能力记录"})
        days.append({"周期": "结业任务", "训练任务": f"模拟完成{top['first_jobs'][0]}真实岗位任务", "考核方式": "场景任务通关", "结果沉淀": "进入见习/面试候选池"})
        st.dataframe(pd.DataFrame(days), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### 岗位任务模拟评分")
        task = st.text_area("模拟任务：请描述一次岗位任务处理过程", value="设备运行中出现异响，温度偏高，班组长要求记录并上报。", height=120)
        completeness = min(95, 60 + len(task) // 4 + (10 if "时间" in task or "设备" in task else 0))
        norm = min(92, 58 + len([w for w in ["编号", "时间", "原因", "处理", "上报", "复盘"] if w in task]) * 7)
        risk = min(96, 65 + (12 if "温度" in task else 0) + (10 if "停机" in task else 0) + (8 if "上报" in task else 0))
        progress_bar(completeness, "信息完整度", "#2563eb")
        progress_bar(norm, "记录规范性", "#7c3aed")
        progress_bar(risk, "风险识别能力", "#059669")
        st.markdown("<div class='warning-box'><b>AI建议：</b>补充设备编号、发生时间、是否停机、现场处理人、班组长确认结果。通过该类训练后，青年不是只拿结业证，而是形成可被企业识别的岗位任务能力记录。</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with tabs[3]:
    st.markdown("<div class='section-title'>苏州政策礼包：从政策文件变成个人路线</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>政府政策不是没有，而是分散在市级、区级、园区、培训、见习、安居等不同入口。系统把政策拆成可计算规则，再生成个人政策包。</div>", unsafe_allow_html=True)
    for p in policies:
        st.markdown("<div class='card-tight'>", unsafe_allow_html=True)
        st.markdown(f"### {p['name']} <span class='pill-purple'>{p['level']}</span>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.2, 1.2, 1])
        c1.markdown(f"**适用对象**  \n{p['target']}")
        c2.markdown(f"**政策价值**  \n{p['value']}")
        c3.markdown(f"**匹配标签**  \n" + " ".join([f"`{t}`" for t in p['tags']]))
        st.markdown(f"**条件提示**：{p['conditions']}")
        st.markdown(f"<div class='small-muted'>风险提示：{p['risk']}。Demo仅做政策路径预评估，最终以主管部门审核为准。</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with tabs[4]:
    st.markdown("<div class='section-title'>三年留苏计划：把就业、租房、培训、政策放在同一张图里</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>青年关心的不只是今天投哪家公司，而是未来三年能不能留下、能不能成长、能不能安居。</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='timeline'>", unsafe_allow_html=True)
    items = [
        ("0-3个月｜来苏求职与首岗进入", f"使用青年人才驿站/面试交通补贴等基础服务；优先投递{top['first_jobs'][0]}等首岗；完成{'、'.join(top['training'][:2])}训练，进入见习或实训候选池。"),
        ("3-12个月｜稳定首岗与租房缓冲", "关注租房补贴、企业带教、岗位适应度回访；若通勤或租房压力高，系统推荐更适配区域或人才公寓/青年公寓资源。"),
        ("1-2年｜能力标签成型", f"围绕{top['one_year']}建立能力标签，沉淀岗位任务记录、项目成果、技能证书或企业评价，避免一年后重新陷入低质量跳槽。"),
        ("2-3年｜安居评估与本地接力", f"评估吴中/相城等区级房票或安居政策资格；若当前企业成长受限，优先推荐苏州本地同生态位企业，完成城市内部接力。"),
    ]
    for title, body in items:
        st.markdown(f"<div class='timeline-item'><div class='timeline-title'>{title}</div><div class='timeline-body'>{body}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='card-tight'>", unsafe_allow_html=True)
        st.markdown("### 区域选择建议")
        for r in top["regions"]:
            note = "产业机会密集，但租房压力可能较高" if r == "工业园区" else "居住成本和产业机会相对均衡" if r in ["相城区", "吴中区"] else "适合制造和高新技术岗位拓展"
            st.markdown(f"- **{r}**：{note}")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='card-tight'>", unsafe_allow_html=True)
        st.markdown("### 生活成本提醒")
        rent_ratio = round(profile["rent_budget"] / max(profile["expected_salary"], 1) * 100, 1)
        st.markdown(f"- 租房预算占期望薪资比例：**{rent_ratio}%**")
        st.markdown(f"- 可接受通勤：**{profile['commute']}分钟**")
        if rent_ratio > 35:
            st.markdown("<span class='pill-red'>租房压力偏高</span>", unsafe_allow_html=True)
        elif profile["commute"] > 65:
            st.markdown("<span class='pill-orange'>通勤压力需关注</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='pill-green'>生活成本相对可控</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with tabs[5]:
    st.markdown("<div class='section-title'>留才预警：一家公司留不住，苏州产业生态要接住</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>系统不做隐私监控，不替青年做决定。它基于青年授权回访、岗位反馈和政策触达记录，提前识别流失风险并生成服务动作。</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([.9, 1.1])
    with c1:
        st.plotly_chart(gauge(100 - risk_score, "留任稳定指数"), use_container_width=True)
        st.markdown(f"<div class='card-tight'><b>风险等级：</b><span class='pill-orange'>{risk_level}</span><br><b>建议动作：</b>政策推送 + 企业带教沟通 + 本地同轨道岗位备选</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### 主要风险因子")
        for f in risk_factors:
            st.markdown(f"- {f}")
        st.markdown("### 本地接力建议")
        st.markdown(f"- 若当前企业无法满足成长，可优先在 **{'、'.join(top['regions'])}** 寻找{top['name']}同生态位岗位。")
        st.markdown("- 青年可选择匿名开放能力画像，企业未获授权前只看到技能标签、经验年限和求职意向。")
        st.markdown("- 政府端看到的是脱敏趋势，用于优化政策和企业服务，不做个人隐私监控。")
        st.markdown("</div>", unsafe_allow_html=True)

with tabs[6]:
    st.markdown("<div class='section-title'>政府驾驶舱：看见青年人才总账</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>给政府看的不是单个青年，而是就业、培训、政策、见习、留任、流失原因的全过程数据。</div>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("青年首岗匹配", "4,120人", "+18.6%")
    m2.metric("技能补齐完成", "1,860人", "+27.3%")
    m3.metric("见习转正率", "63.8%", "+8.1%")
    m4.metric("90天留任率", "81.2%", "+6.4%")
    a, b = st.columns(2)
    with a:
        funnel = go.Figure(go.Funnel(
            y=["进入系统", "生成路线图", "完成技能补齐", "进入见习/面试", "实现首岗就业", "90天留任"],
            x=[12000, 9600, 5200, 4100, 2860, 2322],
            marker={"color": ["#1d4ed8", "#2563eb", "#0891b2", "#059669", "#65a30d", "#16a34a"]},
        ))
        funnel.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10), title="青年留苏转化漏斗")
        st.plotly_chart(funnel, use_container_width=True)
    with b:
        reasons = pd.DataFrame({
            "原因": ["薪资成长", "租房压力", "通勤距离", "岗位不匹配", "企业带教弱", "外地机会吸引"],
            "占比": [26, 21, 17, 14, 12, 10]
        })
        bar = go.Figure(go.Bar(x=reasons["占比"], y=reasons["原因"], orientation="h", marker_color="#2563eb"))
        bar.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10), title="青年流失风险原因分布", xaxis_title="占比%")
        st.plotly_chart(bar, use_container_width=True)
    st.markdown("<div class='success-box'><b>政策建议样例：</b>下阶段可将普惠型政策触达与轨道型留才激励结合：对已进入本地重点产业轨道、完成技能补齐并稳定留任的青年，提高租房、见习、技能培训和安居政策的联动效率。</div>", unsafe_allow_html=True)

with tabs[7]:
    st.markdown("<div class='section-title'>自动生成：苏州青年留才专业评估报告</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>这份报告可以作为Demo交付件，让评委看到系统不是玩具，而是能输出政府和青年都看得懂的正式材料。</div>", unsafe_allow_html=True)
    report_md = f"""
## 《{profile['name']}留苏职业发展路线图》专业评估报告

### 一、基本结论

经系统综合分析，{profile['name']}当前最适合进入苏州 **{top['name']}**。该轨道与其专业背景、已有技能、期望薪资和区域偏好具有较高匹配度，首岗建议为 **{top['first_jobs'][0]}**，一年目标为 **{top['one_year']}**，三年目标为 **{top['three_year']}**。

系统测算其留苏综合适配度为 **{city_fit}分**，首岗匹配度为 **{readiness}%**，90天留才风险为 **{risk_level}**。综合判断：该青年具备留苏发展基础，但需要通过岗位技能补齐、政策礼包触达和入职后90天陪跑，提高首岗转化率和稳定留任概率。

### 二、推荐职业轨道

推荐轨道：**{top['name']}**  
适配区域：**{'、'.join(top['regions'])}**  
首岗入口：**{' / '.join(top['first_jobs'])}**  
一年成长方向：**{top['one_year']}**  
三年成长方向：**{top['three_year']}**  
薪资轨迹参考：首岗约 **{top['salary_start']}**，三年成熟后约 **{top['salary_3y']}**。

推荐理由：{top['why']}

### 三、当前技能缺口与补齐方案

已匹配能力：{('、'.join(top['matched']) if top['matched'] else '系统暂未识别到明确岗位能力记录，建议先做岗位任务测评')}。  
需补齐能力：{('、'.join(top['missing']) if top['missing'] else '暂无明显短板，可直接进入企业见习或面试候选池')}。

建议采用 **7-14天岗位技能补齐包**，围绕 {'、'.join(top['training'][:4])} 开展训练。训练结果不以“听完课程”为标准，而以岗位任务通关、AI评分、导师/企业复核和能力记录沉淀为标准。

### 四、苏州政策礼包预评估

系统为该青年匹配到以下政策路径：

"""
    for p in policies:
        report_md += f"- **{p['level']}｜{p['name']}**：{p['value']}。适用对象：{p['target']}。风险提示：{p['risk']}。\n"
    report_md += f"""

以上政策仅作为系统预评估和办理提醒，最终以主管部门当年度政策文件、申报通知和审核结果为准。

### 五、三年留苏路径建议

**0-3个月：来苏求职与首岗进入。** 使用青年人才驿站、面试交通补贴等基础服务；围绕{top['first_jobs'][0]}完成岗位技能补齐；进入见习、实训或企业面试候选池。

**3-12个月：稳定首岗与租房缓冲。** 关注租房补贴、企业带教、岗位适应度和通勤压力；通过90天回访判断是否需要政策介入或企业HR沟通。

**1-2年：能力标签成型。** 围绕{top['one_year']}积累项目记录、技能证书、岗位成果和企业评价，形成可迁移的本地产业能力标签。

**2-3年：安居评估与本地接力。** 评估吴中、相城等区级房票或安居政策资格；若当前企业无法提供成长空间，优先在苏州本地同产业链企业完成职业接力。

### 六、留才风险与政府服务建议

当前识别到的风险因子包括：{ '；'.join(risk_factors) }。

建议政府端将该类青年纳入“首岗匹配—技能补齐—政策触达—入职90天陪跑—本地产业接力”的全过程服务链条。项目价值不在于替青年做决定，而在于将苏州现有的岗位、政策、培训、见习和企业资源组织成一条青年能理解、企业可转化、政府可运营的留才路线。
"""
    st.markdown(f"<div class='gov-report'>{report_md}</div>", unsafe_allow_html=True)
    st.download_button("下载Markdown报告", data=report_md, file_name=f"{profile['name']}_留苏职业发展路线图.md", mime="text/markdown")

