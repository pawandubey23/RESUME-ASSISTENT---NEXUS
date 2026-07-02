import re
import fitz  # PyMuPDF
from difflib import SequenceMatcher
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ------------------ COMPREHENSIVE SKILLS LIST ------------------
COMPREHENSIVE_SKILLS = [
    # Programming Languages
    "python", "java", "c++", "c#", "javascript", "typescript", "go", "rust", 
    "ruby", "php", "swift", "kotlin", "scala", "r", "c", "matlab", "julia",
    "perl", "haskell", "dart", "objective-c",
    
    # Web Technologies
    "html", "css", "react", "angular", "vue", "vue.js", "node.js", "nodejs", 
    "express", "express.js", "django", "flask", "fastapi", "spring boot", 
    "asp.net", "next.js", "nextjs", "nuxt.js", "svelte", "backbone.js",
    "ember.js", "jquery", "bootstrap", "tailwind css", "sass", "less",
    
    # AI & Machine Learning (EXPANDED)
    "machine learning", "ml", "deep learning", "dl", 
    "artificial intelligence", "ai",
    "generative ai", "gen ai", "genai",
    "natural language processing", "nlp",
    "computer vision", "cv",
    "reinforcement learning", "rl",
    "neural networks", "cnn", "rnn", "lstm", "gru", "transformer",
    "large language models", "llm", "llms",
    "transformers", "gpt", "bert", "t5", "roberta",
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
    "xgboost", "lightgbm", "catboost",
    "hugging face", "langchain", "llama", "claude", "chatgpt",
    "prompt engineering", "fine-tuning", "rag", "retrieval augmented generation",
    "stable diffusion", "diffusion models", "gan", "generative adversarial networks",
    "transfer learning", "few-shot learning", "zero-shot learning",
    "model optimization", "quantization", "pruning",
    
    # AI Agent & Automation
    "ai agents", "autonomous agents", "multi-agent systems",
    "autogen", "crewai", "semantic kernel",
    
    # Data Science & Analytics
    "data analysis", "data visualization", "statistics", "data science",
    "pandas", "numpy", "matplotlib", "seaborn", "plotly", "tableau", "power bi",
    "jupyter", "jupyter notebook", "data mining", "big data",
    "etl", "data pipeline", "data engineering", "data warehouse",
    "apache spark", "pyspark", "hadoop", "hive", "pig",
    
    # Databases
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
    "oracle", "sql server", "dynamodb", "cassandra", "neo4j", 
    "pinecone", "vector database", "chromadb", "weaviate", "milvus",
    "mariadb", "sqlite", "couchdb", "firebase",
    
    # Cloud & DevOps
    "aws", "amazon web services", "azure", "microsoft azure", 
    "gcp", "google cloud", "google cloud platform",
    "docker", "kubernetes", "k8s",
    "jenkins", "gitlab ci", "github actions", "circle ci", "travis ci",
    "terraform", "ansible", "puppet", "chef",
    "ci/cd", "devops", "mlops", "gitops",
    "cloudformation", "helm", "istio", "prometheus", "grafana",
    "nginx", "apache", "load balancing",
    
    # Version Control & Collaboration
    "git", "github", "gitlab", "bitbucket", "subversion", "svn",
    "jira", "confluence", "trello", "asana", "slack",
    
    # Mobile Development
    "ios", "android", "react native", "flutter", "xamarin",
    "mobile development", "swiftui", "jetpack compose",
    
    # Backend & APIs
    "rest api", "restful api", "graphql", "grpc", "microservices",
    "api development", "websockets", "oauth", "jwt",
    "serverless", "lambda", "azure functions", "cloud functions",
    
    # Testing & Quality
    "unit testing", "integration testing", "test-driven development", "tdd",
    "pytest", "junit", "selenium", "cypress", "jest",
    "continuous testing", "test automation", "qa",
    
    # Methodologies & Practices
    "agile", "scrum", "kanban", "waterfall", "devops",
    "continuous integration", "continuous deployment",
    "pair programming", "code review",
    
    # System & Infrastructure
    "linux", "unix", "bash", "shell scripting", "powershell",
    "system design", "software architecture", "distributed systems",
    "microservices architecture", "event-driven architecture",
    "message queues", "kafka", "rabbitmq", "redis pub/sub",
    
    # Security
    "cybersecurity", "security", "encryption", "ssl", "tls",
    "penetration testing", "vulnerability assessment",
    "authentication", "authorization", "oauth", "saml",
    
    # Other Technologies
    "blockchain", "smart contracts", "ethereum", "solidity",
    "iot", "internet of things", "edge computing",
    "ar", "vr", "augmented reality", "virtual reality",
    "game development", "unity", "unreal engine"
]

# Skill aliases for better matching
SKILL_ALIASES = {
    "rl": "reinforcement learning",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "llm": "large language models",
    "llms": "large language models",
    "genai": "generative ai",
    "gen ai": "generative ai",
    "k8s": "kubernetes",
    "tf": "tensorflow",
    "ai": "artificial intelligence",
    "js": "javascript",
    "ts": "typescript",
    "db": "database",
}


# ---------- PDF TEXT EXTRACTION ----------
def extract_text_from_pdf(uploaded_file):
    """Extract text from PDF using PyMuPDF"""
    text = ""
    try:
        # PyMuPDF needs bytes, so read the file
        pdf_bytes = uploaded_file.read()
        
        # Reset file pointer for potential reuse
        uploaded_file.seek(0)
        
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""


# ---------- SKILL EXTRACTION ----------
def extract_skills(text, skills_list=None):
    """
    Extract skills from text with improved matching
    Handles both single words and multi-word phrases
    
    Args:
        text: Text to extract skills from
        skills_list: List of skills to search for (defaults to COMPREHENSIVE_SKILLS)
    """
    if skills_list is None:
        skills_list = COMPREHENSIVE_SKILLS
        
    if not text:
        return []
    
    text_lower = text.lower()
    found_skills = []
    
    # Sort skills by length (longest first) to match phrases before single words
    # This ensures "machine learning" is matched before "machine" or "learning"
    sorted_skills = sorted(skills_list, key=len, reverse=True)
    
    for skill in sorted_skills:
        skill_lower = skill.lower()
        
        # For multi-word skills, use flexible matching
        if ' ' in skill_lower:
            # Match with possible variations (hyphens, dots, etc.)
            pattern = skill_lower.replace(' ', r'[\s\-\.]+')
            if re.search(r'\b' + pattern + r'\b', text_lower):
                found_skills.append(skill_lower)
        else:
            # Single word skills - use word boundary regex
            # Also handle common variations like "python3", "nodejs", etc.
            pattern = r'\b' + re.escape(skill_lower) + r'[\d\.]*\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill_lower)
    
    # Return unique skills (preserve order)
    seen = set()
    unique_skills = []
    for skill in found_skills:
        if skill not in seen:
            seen.add(skill)
            unique_skills.append(skill)
    
    return unique_skills


# ---------- SKILL COMPARISON ----------
def compare_skills(resume_skills, jd_skills):
    """
    Compare skills with improved fuzzy matching and alias support
    
    Args:
        resume_skills: List of skills found in resume
        jd_skills: List of skills found in job description
        
    Returns:
        matched: List of matched skills
        missing: List of missing skills
    """
    if not resume_skills:
        resume_skills = []
    if not jd_skills:
        jd_skills = []
    
    # Normalize skills using aliases
    def normalize_skill(skill):
        skill_lower = skill.lower().strip()
        return SKILL_ALIASES.get(skill_lower, skill_lower)
    
    # Convert to lowercase sets with aliases applied
    resume_set = set(normalize_skill(skill) for skill in resume_skills)
    jd_set = set(normalize_skill(skill) for skill in jd_skills)
    
    matched = []
    missing = []
    
    for jd_skill in jd_set:
        found = False
        
        # Exact match first
        if jd_skill in resume_set:
            matched.append(jd_skill)
            found = True
        else:
            # Fuzzy match - check if skill is substring or contains
            for resume_skill in resume_set:
                # Check both ways: "python" matches "python3" and vice versa
                # Also handle variations like "nodejs" vs "node.js"
                normalized_jd = jd_skill.replace('.', '').replace('-', '').replace(' ', '').replace('_', '')
                normalized_resume = resume_skill.replace('.', '').replace('-', '').replace(' ', '').replace('_', '')
                
                if (jd_skill in resume_skill or 
                    resume_skill in jd_skill or
                    normalized_jd == normalized_resume or
                    normalized_jd in normalized_resume or
                    normalized_resume in normalized_jd):
                    matched.append(jd_skill)
                    found = True
                    break
        
        if not found:
            missing.append(jd_skill)
    
    return list(set(matched)), list(set(missing))


# ---------- MATCH SCORE (FIXED AND IMPROVED) ----------
def combined_match_score(resume_text, job_description, resume_skills=None, jd_skills=None):
    """
    Calculate comprehensive match score with improved weighting
    Uses skills-based matching as primary factor
    
    Args:
        resume_text: Resume text
        job_description: Job description text
        resume_skills: Pre-extracted resume skills (optional)
        jd_skills: Pre-extracted JD skills (optional)
        
    Returns:
        float: Match score between 0 and 100
    """
    if not resume_text or not job_description:
        return 0.0
    
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()
    
    # Factor 1: Skills-based matching (60% weight)
    # This is the most accurate indicator
    skills_score = 0
    if resume_skills is not None and jd_skills is not None:
        if len(jd_skills) > 0:
            matched_skills, _ = compare_skills(resume_skills, jd_skills)
            skills_match_rate = len(matched_skills) / len(jd_skills)
            skills_score = skills_match_rate * 60
        else:
            # If no skills in JD, don't penalize
            skills_score = 0
    
    # Factor 2: Keyword matching (30% weight)
    # Extract meaningful keywords from JD
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
        'your', 'our', 'their', 'work', 'team', 'role', 'job', 'position',
        'experience', 'years', 'skills', 'required', 'preferred', 'looking',
        'seeking', 'candidate', 'apply', 'application', 'company', 'opportunity'
    }
    
    # Extract keywords (3+ characters, not stop words)
    jd_words = re.findall(r'\b[a-z]{3,}\b', jd_lower)
    jd_keywords = [word for word in jd_words if word not in stop_words]
    
    keyword_score = 0
    if jd_keywords:
        unique_keywords = set(jd_keywords)
        matched_keywords = sum(1 for keyword in unique_keywords if keyword in resume_lower)
        keyword_score = (matched_keywords / len(unique_keywords)) * 30
    
    # Factor 3: Overall text similarity (10% weight)
    # Using a more lenient similarity measure
    # Limit text length for performance
    matcher = SequenceMatcher(None, resume_lower[:3000], jd_lower[:3000])
    text_similarity = matcher.ratio() * 10
    
    # Combined score
    total_score = skills_score + keyword_score + text_similarity
    
    # Ensure score is between 0 and 100
    final_score = max(0, min(total_score, 100))
    
    return round(final_score, 2)


# ---------- COMPANY-SPECIFIC OPTIMIZATION ----------

COMPANY_DATABASE = {
    "google": {
        "name": "Google",
        "keywords": ["innovation", "scale", "impact", "user-focused", "data-driven", "collaboration", "leadership principles"],
        "culture": ["Googleyness", "growth mindset", "intellectual humility", "collaborative", "impact-driven"],
        "priorities": [
            "Demonstrate impact at scale (mention user numbers, data scale)",
            "Show innovation and problem-solving creativity",
            "Highlight collaborative projects and cross-team work",
            "Emphasize data-driven decision making",
            "Include metrics that show business impact"
        ],
        "tips": [
            "Use STAR method for all experience bullets",
            "Quantify everything: users affected, performance improvements, cost savings",
            "Highlight ownership and initiative in ambiguous situations",
            "Show how you balanced multiple stakeholder needs",
            "Mention any open-source contributions or technical blogs"
        ],
        "avoid": ["Avoid jargon without context", "Don't focus only on individual work", "Avoid vague statements without metrics"]
    },
    "microsoft": {
        "name": "Microsoft",
        "keywords": ["growth mindset", "customer obsessed", "diverse", "inclusive", "innovation", "cloud", "azure"],
        "culture": ["growth mindset", "customer obsession", "diversity and inclusion", "one microsoft", "making a difference"],
        "priorities": [
            "Demonstrate growth mindset and learning agility",
            "Show customer-focused solutions and impact",
            "Highlight inclusive collaboration and teamwork",
            "Emphasize cloud technologies (Azure, Office 365)",
            "Show adaptability to changing requirements"
        ],
        "tips": [
            "Lead with impact on customers or business outcomes",
            "Show examples of learning from failures",
            "Highlight cross-functional collaboration",
            "Mention experience with Microsoft tech stack if applicable",
            "Demonstrate how you've helped others grow"
        ],
        "avoid": ["Don't show fixed mindset", "Avoid solo-hero narratives", "Don't ignore diversity/inclusion aspects"]
    },
    "amazon": {
        "name": "Amazon",
        "keywords": ["customer obsession", "ownership", "bias for action", "frugality", "leadership principles", "high standards"],
        "culture": ["leadership principles", "customer obsession", "ownership", "dive deep", "deliver results"],
        "priorities": [
            "Align experiences with Amazon's 16 Leadership Principles",
            "Show customer obsession in every bullet point",
            "Demonstrate ownership and accountability",
            "Highlight bias for action and results delivery",
            "Show how you've raised the bar and built scalable systems"
        ],
        "tips": [
            "Structure bullets around Leadership Principles (LP)",
            "Use metrics: revenue impact, cost savings, efficiency gains",
            "Show examples of working backwards from customer needs",
            "Highlight instances where you challenged status quo",
            "Demonstrate frugality and resourcefulness"
        ],
        "avoid": ["Don't make excuses or blame others", "Avoid focusing on process over results", "Don't ignore customer impact"]
    },
    "meta": {
        "name": "Meta (Facebook)",
        "keywords": ["move fast", "bold", "social", "focus on impact", "build social value", "be open"],
        "culture": ["move fast", "be bold", "focus on impact", "be open", "build awesome things"],
        "priorities": [
            "Show rapid iteration and shipping mentality",
            "Demonstrate building at scale (billions of users)",
            "Highlight A/B testing and data-informed decisions",
            "Show impact on user engagement and growth",
            "Emphasize cross-functional collaboration"
        ],
        "tips": [
            "Quantify user impact and engagement metrics",
            "Show how you moved fast and iterated",
            "Highlight experiments and learnings from failures",
            "Mention experience with social products or platforms",
            "Demonstrate comfort with ambiguity"
        ],
        "avoid": ["Don't show analysis paralysis", "Avoid overly cautious approach", "Don't ignore user metrics"]
    },
    "apple": {
        "name": "Apple",
        "keywords": ["innovation", "excellence", "design", "user experience", "quality", "attention to detail"],
        "culture": ["innovation", "excellence", "simplicity", "design-driven", "secrecy"],
        "priorities": [
            "Show obsession with quality and user experience",
            "Demonstrate attention to detail",
            "Highlight design thinking and simplicity",
            "Show innovation in product or process",
            "Emphasize cross-functional collaboration"
        ],
        "tips": [
            "Focus on end-user experience and delight",
            "Show examples of going above and beyond for quality",
            "Highlight any design or UX improvements",
            "Mention experience with Apple ecosystem if relevant",
            "Demonstrate pride in craft and excellence"
        ],
        "avoid": ["Don't show 'good enough' mentality", "Avoid complexity over simplicity", "Don't ignore user experience"]
    },
    "netflix": {
        "name": "Netflix",
        "keywords": ["freedom and responsibility", "context not control", "highly aligned loosely coupled", "candor"],
        "culture": ["freedom and responsibility", "context not control", "judgment", "courage", "selflessness"],
        "priorities": [
            "Show independent decision-making with context",
            "Demonstrate high judgment in ambiguous situations",
            "Highlight candid feedback and communication",
            "Show how you've adapted to rapid change",
            "Emphasize results over process"
        ],
        "tips": [
            "Show examples of making tough calls independently",
            "Highlight transparent and direct communication",
            "Demonstrate comfort with minimal process",
            "Show how you've given/received candid feedback",
            "Emphasize outcomes over hours worked"
        ],
        "avoid": ["Don't show need for hand-holding", "Avoid politics or bureaucracy", "Don't focus on process over results"]
    },
    "startup": {
        "name": "Startup/Generic Tech",
        "keywords": ["agile", "fast-paced", "wear multiple hats", "ownership", "scrappy", "growth"],
        "culture": ["move fast", "ownership", "resourcefulness", "adaptability", "growth mindset"],
        "priorities": [
            "Show ability to wear multiple hats",
            "Demonstrate resourcefulness with limited resources",
            "Highlight end-to-end ownership",
            "Show comfort with ambiguity and change",
            "Emphasize rapid learning and adaptation"
        ],
        "tips": [
            "Show examples of doing more with less",
            "Highlight instances where you built things from scratch",
            "Demonstrate ability to context-switch quickly",
            "Show comfort with uncertainty and pivots",
            "Emphasize hustle and scrappiness"
        ],
        "avoid": ["Don't show need for structure", "Avoid specialized-only experience", "Don't ignore business impact"]
    }
}

def detect_company(job_description):
    """
    Detect company from job description
    Returns company key and confidence score
    """
    jd_lower = job_description.lower()
    
    # Direct company name detection
    company_patterns = {
        "google": ["google", "alphabet inc"],
        "microsoft": ["microsoft", "msft"],
        "amazon": ["amazon", "aws", "amazon web services"],
        "meta": ["meta", "facebook", "instagram", "whatsapp"],
        "apple": ["apple inc", "apple"],
        "netflix": ["netflix"],
    }
    
    detected = None
    confidence = 0
    
    # Check for direct mentions
    for company, patterns in company_patterns.items():
        for pattern in patterns:
            if pattern in jd_lower:
                detected = company
                confidence = 100
                return detected, confidence
    
    # Check for culture keywords (fuzzy detection)
    if not detected:
        scores = {}
        for company, data in COMPANY_DATABASE.items():
            score = 0
            keywords = data["keywords"] + data["culture"]
            for keyword in keywords:
                if keyword.lower() in jd_lower:
                    score += 1
            if score > 0:
                scores[company] = score
        
        if scores:
            detected = max(scores, key=scores.get)
            confidence = min(scores[detected] * 15, 75)  # Cap at 75% for fuzzy detection
    
    # Default to startup if no specific company detected
    if not detected or confidence < 30:
        detected = "startup"
        confidence = 50
    
    return detected, confidence

def generate_company_specific_tips(company_key, resume_text, missing_skills):
    """
    Generate company-specific optimization tips
    """
    company_data = COMPANY_DATABASE.get(company_key, COMPANY_DATABASE["startup"])
    
    tips = {
        "company_name": company_data["name"],
        "culture_keywords": company_data["culture"],
        "optimization_tips": company_data["tips"],
        "priorities": company_data["priorities"],
        "keywords_to_add": [],
        "avoid": company_data["avoid"]
    }
    
    # Check which culture keywords are missing from resume
    resume_lower = resume_text.lower()
    for keyword in company_data["keywords"]:
        if keyword.lower() not in resume_lower:
            tips["keywords_to_add"].append(keyword)
    
    return tips
def mock_ai_suggestions(resume_text, job_description, missing_skills=None):
    """
    Generate realistic AI-like suggestions without API
    
    Args:
        resume_text: The full resume text
        job_description: The job description text
        missing_skills: List of skills missing from resume
        
    Returns:
        str: Mock AI suggestions
    """
    suggestions = []
    
    # Analyze missing skills
    if missing_skills and len(missing_skills) > 0:
        top_missing = ', '.join(missing_skills[:5])
        suggestions.append(f"🎯 **Add Missing Skills**: Your resume lacks these key skills: **{top_missing}**. Add them to your skills section or incorporate them into project descriptions where you've used similar technologies.")
    else:
        suggestions.append("✅ **Skills Coverage**: Great! You have all the required technical skills mentioned in the job description.")
    
    # Generic but useful suggestions
    suggestions.extend([
        "📊 **Quantify Achievements**: Replace generic statements with measurable results. Example: 'Improved system performance by 40%, reducing response time from 500ms to 300ms' instead of 'Improved system performance'.",
        
        "🔑 **Keywords Optimization**: Mirror exact phrases from the job description. If they say 'machine learning pipelines', use 'machine learning pipelines' instead of 'ML workflows'. ATS systems look for exact matches.",
        
        "💼 **Experience Alignment**: Reorder your work experience bullets to put the most relevant ones first. Match your achievements to the job requirements mentioned in the description.",
        
        "🎨 **ATS-Friendly Format**: Use standard section headers (Work Experience, Education, Technical Skills). Avoid tables, images, text boxes, or complex formatting that ATS systems can't parse correctly.",
        
        "🚀 **Action Verbs**: Start bullet points with strong action verbs: **Led, Developed, Implemented, Architected, Optimized, Achieved, Reduced, Increased**. This makes your accomplishments more impactful."
    ])
    
    return "\n\n".join(suggestions)
