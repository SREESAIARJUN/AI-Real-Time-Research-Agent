import streamlit as st
import os
import json
import base64
from datetime import datetime
from typing import List, Dict, Any
import re
import io

# Core LangChain imports
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.tools import DuckDuckGoSearchResults, Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Tool-specific imports
import PyPDF2
import matplotlib.pyplot as plt
import pandas as pd

# Configure page with dark theme
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ultra-modern dark theme with gradients
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        font-family: 'Inter', sans-serif;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Custom Header */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5rem;
        font-weight: 700;
        text-align: center;
        margin: 2rem 0;
        text-shadow: 0 0 30px rgba(102, 126, 234, 0.3);
    }

    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e1e1e 0%, #2d2d2d 100%);
        border-right: 1px solid #333;
    }

    /* Chat Container */
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin: 1rem 0;
    }

    /* User Message */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 1rem 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        animation: slideInRight 0.3s ease-out;
    }

    /* Assistant Message */
    .assistant-message {
        background: linear-gradient(135deg, #2d2d2d 0%, #1e1e1e 100%);
        color: #e0e0e0;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 1rem 0;
        max-width: 80%;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        animation: slideInLeft 0.3s ease-out;
    }

    /* Tool Output */
    .tool-output {
        background: linear-gradient(135deg, #1a2332 0%, #2d3748 100%);
        color: #a0aec0;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        border-left: 4px solid #4fd1c7;
        font-family: 'Monaco', monospace;
        font-size: 0.9rem;
        box-shadow: 0 4px 16px rgba(79, 209, 199, 0.2);
    }

    /* Follow-up Questions */
    .follow-up-container {
        background: linear-gradient(135deg, #2d1b69 0%, #11998e 100%);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(45, 27, 105, 0.3);
    }

    .follow-up-title {
        color: #ffffff;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .follow-up-question {
        background: rgba(255, 255, 255, 0.1);
        color: #e0e0e0;
        padding: 0.8rem 1.2rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .follow-up-question:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateX(5px);
        box-shadow: 0 4px 16px rgba(255, 255, 255, 0.1);
    }

    /* Input Styling */
    .stTextInput > div > div > input {
        background: linear-gradient(135deg, #2d2d2d 0%, #1e1e1e 100%);
        color: #e0e0e0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        padding: 1rem;
        font-size: 1rem;
    }

    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3);
    }

    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    }

    /* File Uploader */
    .uploadedFile {
        background: linear-gradient(135deg, #2d2d2d 0%, #1e1e1e 100%);
        border: 2px dashed rgba(255, 255, 255, 0.3);
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        color: #e0e0e0;
    }

    /* Animations */
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(30px); }
        to { opacity: 1; transform: translateX(0); }
    }

    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Loading Animation */
    .loading-dots {
        animation: pulse 1.5s infinite;
    }

    /* Status Indicators */
    .status-success {
        color: #48bb78;
        font-weight: 600;
    }

    .status-error {
        color: #f56565;
        font-weight: 600;
    }

    .status-warning {
        color: #ed8936;
        font-weight: 600;
    }

    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }

    .pdf-status {
        background: linear-gradient(135deg, #1a2332 0%, #2d3748 100%);
        color: #4fd1c7;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #4fd1c7;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)



# ==========================================
# DDGS WITH ANTI-ANOMALY DETECTION
# ==========================================
class SmartDuckDuckGoSearch:
    """
    DuckDuckGo search with anti-anomaly detection
    Uses DDGS with proper configuration to avoid bot detection
    """
    def __init__(self):
        self.name = "web_search"
        self.description = """Search the web for current information using DuckDuckGo.
Use this for: latest news, current events, real-time information, recent updates.
Input should be a clear, specific search query."""

    def run(self, query: str) -> str:
        """Run DuckDuckGo search with anti-detection measures"""
        try:
            from duckduckgo_search import DDGS
            import time
            import random

            # Anti-detection: Add small random delay
            time.sleep(random.uniform(1, 3))

            # Use DDGS with lite backend (less likely to trigger anomaly detection)
            results = []
            with DDGS() as ddgs:
                try:
                    # Use lite backend and conservative parameters
                    search_results = ddgs.text(
                        keywords=query,
                        region='wt-wt',  # worldwide
                        safesearch='moderate',
                        timelimit=None,  # no time limit
                        max_results=5,   # conservative limit
                        backend='lite'   # lite backend avoids heavy detection
                    )

                    # Convert generator to list
                    results = list(search_results) if search_results else []

                except Exception as e:
                    # If DDGS fails, check if it's anomaly detection
                    error_str = str(e).lower()
                    if 'ratelimit' in error_str or '202' in str(e) or 'anomaly' in error_str:
                        return self._handle_anomaly_detection(query)
                    else:
                        raise e

            # Format results
            if not results:
                return f"No results found for: {query}\n\nTip: Try rephrasing your query or using more specific keywords."

            output = [f"🔍 **Search Results for:** {query}\n"]
            for i, r in enumerate(results[:5], 1):
                title = r.get('title', 'No title')
                body = r.get('body', 'No description')
                href = r.get('href', '')
                output.append(f"**{i}. {title}**\n   {body}\n   🔗 {href}\n")

            return "\n".join(output)

        except ImportError:
            return """⚠️ DuckDuckGo search library not installed.

Install with: pip install duckduckgo-search

For now, I'll answer using my training data."""

        except Exception as e:
            error_msg = str(e)
            if 'ratelimit' in error_msg.lower() or '202' in error_msg or 'anomaly' in error_msg.lower():
                return self._handle_anomaly_detection(query)
            else:
                return f"""⚠️ Search error: {error_msg[:100]}

I'll answer your question using my knowledge base instead.

What would you like to know about "{query}"?"""

    def _handle_anomaly_detection(self, query: str) -> str:
        """Handle DuckDuckGo anomaly detection gracefully"""
        return f"""⚠️ **DuckDuckGo Anomaly Detection Triggered**

DuckDuckGo has temporarily flagged automated searches from your IP.

**Why this happens:**
- DuckDuckGo protects against automated scraping
- Multiple rapid searches trigger their anomaly detection
- Not a permanent block - usually clears in 10-30 minutes

**Solutions:**
1. **Wait 10-30 minutes** - Detection usually clears automatically
2. **Use VPN/Different Network** - Change your IP address
3. **Get Brave Search API** (Free tier: 2000/month)
   - Sign up: https://brave.com/search/api/
   - Set: BRAVE_SEARCH_API_KEY=your_key
4. **I'll answer from knowledge** - Ask me directly!

**For now, let me help you with: "{query}"**

I can provide information based on my training data. What specific aspect would you like to know?"""

class PDFReaderTool:
    """Enhanced PDF reader tool with proper error handling"""

    def __init__(self):
        self.name = "pdf_reader"
        self.description = """Extract and analyze text content from uploaded PDF files. 
        Use this tool when users ask to:
        - Analyze uploaded document/PDF
        - Summarize the document
        - Extract information from PDF
        - Ask questions about uploaded content
        - Review the uploaded file
        This tool accesses PDF content stored in session state and returns extracted text with metadata."""

    def run(self, query: str) -> str:
        """Extract text from uploaded PDF"""
        try:
            # Check if PDF content is available in session state
            if not hasattr(st.session_state, 'pdf_content') or st.session_state.pdf_content is None:
                return "⚠️ No PDF file uploaded. Please upload a PDF file using the sidebar first."

            # Get PDF content from session state
            pdf_content = st.session_state.pdf_content
            
            # Create PDF reader from bytes
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))

            # Extract metadata
            num_pages = len(pdf_reader.pages)
            metadata = pdf_reader.metadata if pdf_reader.metadata else {}

            # Extract text from all pages
            full_text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        full_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                except Exception as page_error:
                    full_text += f"\n--- Page {page_num + 1} (Error extracting text) ---\n"

            # Clean and format text
            full_text = re.sub(r'\s+', ' ', full_text).strip()

            if not full_text:
                return "⚠️ No readable text found in the PDF. The PDF might be image-based or corrupted."

            # Create summary
            word_count = len(full_text.split())
            char_count = len(full_text)

            # Store full text for future reference
            st.session_state.pdf_full_text = full_text

            result = f"""📄 PDF Analysis Complete

📊 Document Statistics:
• Pages: {num_pages}
• Words: {word_count:,}
• Characters: {char_count:,}

📝 Content Preview (First 1500 characters):
{full_text[:1500]}{'...' if len(full_text) > 1500 else ''}

✅ Full document content extracted and ready for analysis.

💡 You can now ask specific questions about the document content, request summaries, or ask for analysis of specific sections."""

            return result

        except Exception as e:
            return f"❌ Error processing PDF: {str(e)}. Please ensure the file is a valid, non-corrupted PDF."

class ChartMakerTool:
    """Enhanced chart creation tool with multiple chart types"""

    def __init__(self):
        self.name = "chart_maker"
        self.description = """Create professional charts and visualizations from data.
        Input format: 'Chart Title|chart_type|label1,value1|label2,value2|...'
        Chart types: bar, line, pie, scatter
        Example: 'Sales Data|bar|Jan,100|Feb,150|Mar,120'"""

    def run(self, data_input: str) -> str:
        """Create charts from structured data"""
        try:
            # Parse input
            parts = data_input.split('|')
            if len(parts) < 3:
                return """❌ Invalid format. Use: 'Title|chart_type|label1,value1|label2,value2'

📊 Supported chart types: bar, line, pie, scatter
📝 Example: 'Monthly Sales|bar|Jan,1200|Feb,1500|Mar,1300'"""

            title = parts[0].strip()
            chart_type = parts[1].strip().lower()
            data_parts = parts[2:]

            # Extract data
            labels = []
            values = []

            for part in data_parts:
                if ',' in part:
                    label, value = part.split(',', 1)
                    labels.append(label.strip())
                    try:
                        values.append(float(value.strip()))
                    except ValueError:
                        values.append(0)

            if not labels or not values:
                return "❌ No valid data found. Ensure format: label1,value1|label2,value2"

            # Set up the plot with dark theme
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(12, 8))
            fig.patch.set_facecolor('#1e1e1e')
            ax.set_facecolor('#2d2d2d')

            # Color palette
            colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']

            # Create chart based on type
            if chart_type == 'bar':
                bars = ax.bar(labels, values, color=colors[:len(labels)])
                # Add value labels on bars
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{value:,.0f}', ha='center', va='bottom', 
                           color='white', fontweight='bold')

            elif chart_type == 'line':
                ax.plot(labels, values, marker='o', linewidth=3, 
                       markersize=8, color='#667eea')
                ax.fill_between(labels, values, alpha=0.3, color='#667eea')

            elif chart_type == 'pie':
                wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors[:len(labels)],
                                                 autopct='%1.1f%%', startangle=90)
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')

            elif chart_type == 'scatter':
                ax.scatter(range(len(values)), values, s=100, 
                          c=colors[:len(values)], alpha=0.7)
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels)
            else:
                return f"❌ Unsupported chart type: {chart_type}. Use: bar, line, pie, scatter"

            # Styling
            ax.set_title(title, fontsize=16, fontweight='bold', color='#e0e0e0', pad=20)
            ax.tick_params(colors='#e0e0e0')
            ax.grid(True, alpha=0.3)

            if chart_type != 'pie':
                ax.set_xlabel('Categories', fontsize=12, color='#e0e0e0')
                ax.set_ylabel('Values', fontsize=12, color='#e0e0e0')

            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            # Save to session state for display
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, 
                       bbox_inches='tight', facecolor='#1e1e1e')
            img_buffer.seek(0)

            # Encode image
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            st.session_state.chart_image = img_base64

            plt.close()

            return f"""📊 Chart Created Successfully!

📈 Chart Details:
• Type: {chart_type.title()}
• Title: {title}
• Data Points: {len(labels)}
• Values Range: {min(values):,.0f} - {max(values):,.0f}

✅ Chart has been generated and will be displayed below this message."""

        except Exception as e:
            return f"❌ Error creating chart: {str(e)}"

class CitationFormatterTool:
    """Enhanced citation formatter with multiple styles"""

    def __init__(self):
        self.name = "citation_formatter"
        self.description = """Format academic citations in multiple styles.
        Input: 'style|author|title|year|source'
        Styles: APA, MLA, Chicago, Harvard
        Example: 'APA|Smith, J.|Research Methods|2024|Journal of Science'"""

    def run(self, citation_input: str) -> str:
        """Format citations in academic styles"""
        try:
            parts = citation_input.split('|')
            if len(parts) < 5:
                return """❌ Invalid format. Use: 'style|author|title|year|source'

📚 Supported styles: APA, MLA, Chicago, Harvard
📝 Example: 'APA|Smith, J.|AI Research|2024|Tech Journal'"""

            style = parts[0].strip().upper()
            author = parts[1].strip()
            title = parts[2].strip()
            year = parts[3].strip()
            source = parts[4].strip()

            # Get current date for access dates
            current_date = datetime.now()
            access_date = current_date.strftime("%B %d, %Y")

            citations = {}

            # APA Style
            if 'APA' in style or style == 'APA':
                if 'http' in source.lower():
                    citations['APA'] = f"{author} ({year}). {title}. Retrieved {access_date}, from {source}"
                else:
                    citations['APA'] = f"{author} ({year}). {title}. {source}."

            # MLA Style  
            if 'MLA' in style or style == 'MLA':
                if 'http' in source.lower():
                    citations['MLA'] = f'{author}. "{title}." Web. {access_date}. <{source}>.'
                else:
                    citations['MLA'] = f'{author}. "{title}." {source}, {year}.'

            # Chicago Style
            if 'CHICAGO' in style or style == 'CHICAGO':
                if 'http' in source.lower():
                    citations['Chicago'] = f'{author}. "{title}." Accessed {access_date}. {source}.'
                else:
                    citations['Chicago'] = f'{author}. "{title}." {source} ({year}).'

            # Harvard Style
            if 'HARVARD' in style or style == 'HARVARD':
                citations['Harvard'] = f"{author} {year}, '{title}', {source}."

            if not citations:
                return f"❌ Unsupported citation style: {style}. Use: APA, MLA, Chicago, Harvard"

            # Format result
            result = "📚 Citation Formatted Successfully!\n\n"
            for style_name, citation in citations.items():
                result += f"**{style_name} Style:**\n{citation}\n\n"

            result += f"""📋 Citation Details:
• Author: {author}
• Title: {title}  
• Year: {year}
• Source: {source}
• Generated: {access_date}"""

            return result

        except Exception as e:
            return f"❌ Error formatting citation: {str(e)}"

def create_advanced_prompt():
    """Create an advanced prompt template with context engineering"""

    return ChatPromptTemplate.from_messages([
        ("system", """You are ARIA (Advanced Research Intelligence Assistant), a sophisticated AI research agent designed to provide comprehensive, accurate, and contextually aware assistance.

🎯 CORE OBJECTIVES:
1. Conduct thorough web research using real-time search capabilities
2. Synthesize information into structured, actionable insights
3. Maintain conversational context and build upon previous interactions
4. Provide intelligent follow-up suggestions to deepen understanding
5. Utilize specialized tools for document analysis, visualization, and citation management

🧠 INTELLIGENCE PROTOCOLS:

SEARCH STRATEGY:
- Before searching, analyze the query for key concepts, entities, and intent
- Use multiple search approaches: broad overview, specific details, recent developments
- Prioritize authoritative sources and recent information
- Cross-reference information across multiple sources for accuracy

RESPONSE STRUCTURE:
- Lead with executive summary for complex topics
- Use bullet points for key findings and structured lists
- Include relevant data, statistics, and expert opinions
- Provide context and background when necessary
- End with 2-3 intelligent follow-up questions

TOOL UTILIZATION - CRITICAL:
- ALWAYS use pdf_reader when users mention "document", "PDF", "uploaded file", "analyze document", or similar terms
- Use chart_maker when data visualization would enhance understanding
- Use citation_formatter when academic references are needed
- Use DuckDuckGo search for web research and current information
- Combine tools strategically for comprehensive analysis

PDF ANALYSIS TRIGGERS:
When users say ANY of these phrases, IMMEDIATELY use the pdf_reader tool:
- "analyze the document"
- "analyze the uploaded document" 
- "summarize the PDF"
- "what's in the document"
- "review the file"
- "analyze uploaded file"
- "examine the document"
- "tell me about the document"

CONTEXT AWARENESS:
- Reference previous conversation points when relevant
- Build upon established context and user interests
- Adapt communication style to user's apparent expertise level
- Remember user preferences and research patterns

🔍 SEARCH TRIGGERS:
Automatically search when queries involve:
- Current events, news, or recent developments
- Factual information, statistics, or data
- Comparisons between concepts, products, or ideas
- Technical explanations or how-to information
- Market research or trend analysis
- Academic or scientific topics

💡 RESPONSE ENHANCEMENT:
- Provide actionable insights, not just information
- Include relevant examples and case studies
- Explain implications and significance of findings
- Suggest practical applications or next steps
- Maintain professional yet conversational tone

🚀 ADVANCED FEATURES:
- Synthesize information from multiple sources
- Identify patterns and connections across topics
- Provide balanced perspectives on controversial topics
- Suggest related research directions
- Adapt depth and complexity to user needs

Remember: You are not just answering questions—you are facilitating discovery, enabling deeper understanding, and empowering informed decision-making through intelligent research assistance."""),

        MessagesPlaceholder(variable_name="chat_history"),

        ("human", """Query: {input}

Context Analysis:
- Previous conversation context: Available in chat history
- Query type: [Analyze if this is factual, analytical, creative, or procedural]
- Required tools: [Determine if web search, document analysis, or other tools are needed]
- Response depth: [Assess complexity level needed]

Please provide a comprehensive response following the intelligence protocols above."""),

        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

def generate_intelligent_followups(query: str, response: str) -> List[str]:
    """Generate contextually relevant follow-up questions"""

    # Analyze query and response for context
    query_lower = query.lower()
    response_lower = response.lower()

    # Category-based follow-ups
    followups = []

    if any(term in query_lower for term in ['technology', 'ai', 'software', 'digital']):
        followups = [
            "What are the latest technological advancements in this field?",
            "How might this technology impact different industries?", 
            "What are the potential risks or limitations to consider?"
        ]
    elif any(term in query_lower for term in ['market', 'business', 'economic', 'financial']):
        followups = [
            "What are the current market trends and projections?",
            "How do competitors compare in this space?",
            "What economic factors might influence these developments?"
        ]
    elif any(term in query_lower for term in ['health', 'medical', 'research', 'scientific']):
        followups = [
            "What does the latest research reveal about this topic?",
            "Are there any ongoing clinical trials or studies?",
            "What are the practical implications for healthcare?"
        ]
    elif any(term in query_lower for term in ['education', 'learning', 'academic']):
        followups = [
            "What are the most effective learning approaches for this topic?",
            "How is this subject being taught in modern curricula?",
            "What resources would you recommend for deeper study?"
        ]
    else:
        # Generic intelligent follow-ups
        followups = [
            "What are the most significant recent developments in this area?",
            "How does this compare to similar concepts or alternatives?",
            "What practical applications or implications should I consider?"
        ]

    return followups

def initialize_session_state():
    """Initialize session state with enhanced memory management"""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "memory" not in st.session_state:
        st.session_state.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=4000  # Prevent memory overflow
        )

    if "agent_executor" not in st.session_state:
        st.session_state.agent_executor = None

    if "pdf_content" not in st.session_state:
        st.session_state.pdf_content = None

    if "pdf_filename" not in st.session_state:
        st.session_state.pdf_filename = None

    if "pdf_full_text" not in st.session_state:
        st.session_state.pdf_full_text = None

    if "chart_image" not in st.session_state:
        st.session_state.chart_image = None

def setup_enhanced_agent():
    """Setup the enhanced LangChain agent with improved tools"""

    # API Key input with better styling - try environment first
    st.sidebar.markdown("### 🔑 Configuration")
    
    # Try to get API key from environment first
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if gemini_api_key:
        st.sidebar.success("✅ API key loaded from environment")
        st.sidebar.info("Using environment variable OPENAI_API_KEY")
    else:
        st.sidebar.warning("⚠️ No environment API key found")
        gemini_api_key = st.sidebar.text_input(
            "Google Gemini API Key", 
            type="password",
            help="Enter your OpenAI API key from platform.openai.com",
            placeholder="AI..."
        )

    if not gemini_api_key:
        st.sidebar.error("⚠️ API key required to continue")
        st.sidebar.markdown("""
        **Two ways to provide API key:**
        1. Set environment variable: `OPENAI_API_KEY=your_key`
        2. Enter manually in the field above
        """)
        return None

    try:
        # Initialize enhanced LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",  # Using more capable model
            temperature=0.3,  # Lower temperature for more focused responses
            google_api_key=gemini_api_key,
            max_output_tokens=8192,
            convert_system_message_to_human=True
        )

        # Initialize enhanced tools
        search_tool = DuckDuckGoSearchResults(
            num_results=10,  # More results for better coverage
            max_snippet_length=300
        )

        # Enhanced custom tools with better descriptions
        pdf_tool = PDFReaderTool()
        chart_tool = ChartMakerTool() 
        citation_tool = CitationFormatterTool()

        tools = [
            Tool(
                name="pdf_reader",
                description="""Use this tool to analyze uploaded PDF documents. Call this tool when users ask to:
                - analyze document, analyze the document, analyze uploaded document
                - summarize PDF, summarize document, what's in the document  
                - review file, examine document, tell me about the document
                - extract information from PDF, read the document
                This tool extracts and analyzes text content from uploaded PDF files.""",
                func=pdf_tool.run
            ),
            search_tool,
            Tool(
                name=chart_tool.name,
                description=chart_tool.description,
                func=chart_tool.run
            ),
            Tool(
                name=citation_tool.name,
                description=citation_tool.description,
                func=citation_tool.run
            )
        ]

        # Create advanced prompt
        prompt = create_advanced_prompt()

        # Create enhanced agent
        agent = create_openai_functions_agent(llm, tools, prompt)

        # Create agent executor with better error handling
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=st.session_state.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=6,  # Allow more iterations for complex queries
            return_intermediate_steps=True
        )

        return agent_executor

    except Exception as e:
        st.sidebar.error(f"❌ Setup failed: {str(e)}")
        return None

def display_message(message: Dict[str, str], is_user: bool = True):
    """Display messages with enhanced styling"""
    if is_user:
        st.markdown(f"""
        <div class="user-message">
            <strong>You:</strong> {message['content']}
        </div>
        """, unsafe_allow_html=True)
    else:
        # Process assistant message content to handle markdown properly
        content = message['content']
        
        # Check if content starts with markdown headers and format accordingly
        if content.startswith('###') or content.startswith('##') or content.startswith('#'):
            # Split the content to separate the header from the rest
            lines = content.split('\n', 1)
            if len(lines) > 1:
                header = lines[0]
                rest_content = lines[1]
                st.markdown(f"""
                <div class="assistant-message">
                    <strong>🔍 ARIA:</strong>
                </div>
                """, unsafe_allow_html=True)
                # Display header and content separately to maintain proper markdown
                st.markdown(header)
                st.markdown(rest_content)
            else:
                st.markdown(f"""
                <div class="assistant-message">
                    <strong>🔍 ARIA:</strong>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(content)
        else:
            st.markdown(f"""
            <div class="assistant-message">
                <strong>🔍 ARIA:</strong> {content}
            </div>
            """, unsafe_allow_html=True)
        
        # Check if this message triggered a chart creation and display it immediately after the message
        if hasattr(st.session_state, 'chart_image') and st.session_state.chart_image and hasattr(st.session_state, 'show_chart_after_message'):
            st.markdown("### 📊 Generated Chart")
            chart_html = f'<img src="data:image/png;base64,{st.session_state.chart_image}" style="width:100%; border-radius: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); margin: 1rem 0;">'
            st.markdown(chart_html, unsafe_allow_html=True)
            # Clear the flag but keep the chart
            if hasattr(st.session_state, 'show_chart_after_message'):
                del st.session_state.show_chart_after_message

def main():
    """Enhanced main application with modern UI"""

    # Modern header
    st.markdown('<h1 class="main-header">🔍 ARIA Research Assistant</h1>', unsafe_allow_html=True)

    # Initialize session state
    initialize_session_state()

    # Sidebar configuration
    st.sidebar.title("🛠️ Control Panel")

    # Setup agent
    if st.session_state.agent_executor is None:
        st.session_state.agent_executor = setup_enhanced_agent()

    # Enhanced file upload with better feedback
    st.sidebar.markdown("### 📄 Document Upload")
    uploaded_file = st.sidebar.file_uploader(
        "Upload PDF for analysis",
        type=["pdf"],
        help="Upload a PDF document to extract and analyze its content"
    )

    # Handle file upload
    if uploaded_file is not None:
        if st.session_state.pdf_filename != uploaded_file.name:
            # New file uploaded
            st.session_state.pdf_content = uploaded_file.read()
            st.session_state.pdf_filename = uploaded_file.name
            st.session_state.pdf_full_text = None  # Reset extracted text
            
            st.sidebar.success(f"✅ {uploaded_file.name} uploaded successfully!")
            st.sidebar.markdown(f"""
            <div class="pdf-status">
                📄 PDF Ready: {uploaded_file.name}<br>
                💡 Ask me to analyze this document!
            </div>
            """, unsafe_allow_html=True)
    elif st.session_state.pdf_content is not None:
        # Show current PDF status
        st.sidebar.markdown(f"""
        <div class="pdf-status">
            📄 Current PDF: {st.session_state.pdf_filename}<br>
            ✅ Ready for analysis
        </div>
        """, unsafe_allow_html=True)

    # Tool examples with modern styling
    st.sidebar.markdown("### 🎯 Example Queries")

    example_queries = [
        "🔍 Search: Latest AI developments in healthcare",
        "📊 Chart: Create a bar chart with Q1,100|Q2,150|Q3,120", 
        "📄 PDF: Analyze the uploaded document",
        "📚 Citation: Format in APA style: Smith|AI Research|2024|Journal"
    ]

    for query in example_queries:
        if st.sidebar.button(query, key=query):
            st.session_state.example_query = query.split(": ", 1)[1]

    # Clear conversation
    if st.sidebar.button("🗑️ Clear Conversation", type="secondary"):
        st.session_state.messages = []
        st.session_state.memory.clear()
        st.session_state.pdf_content = None
        st.session_state.pdf_filename = None
        st.session_state.pdf_full_text = None
        st.session_state.chart_image = None
        # Clear any chart flags
        if hasattr(st.session_state, 'show_chart_after_message'):
            del st.session_state.show_chart_after_message
        st.rerun()

    # Clear chart button
    if hasattr(st.session_state, 'chart_image') and st.session_state.chart_image:
        if st.sidebar.button("🗑️ Clear Chart", type="secondary"):
            st.session_state.chart_image = None
            # Clear any chart flags
            if hasattr(st.session_state, 'show_chart_after_message'):
                del st.session_state.show_chart_after_message
            st.rerun()

    # Main interface
    if st.session_state.agent_executor is None:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: rgba(255,255,255,0.05); border-radius: 20px; margin: 2rem 0;">
            <h3 style="color: #667eea;">🔑 Authentication Required</h3>
            <p style="color: #a0aec0;">Please enter your OpenAI API key in the sidebar to begin research.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Chat history display
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    for message in st.session_state.messages:
        display_message(message, message["role"] == "user")

    st.markdown('</div>', unsafe_allow_html=True)

    # Display persistent charts (only charts not immediately after messages)
    if hasattr(st.session_state, 'chart_image') and st.session_state.chart_image and not hasattr(st.session_state, 'show_chart_after_message'):
        st.markdown("### 📊 Current Chart")
        chart_html = f'<img src="data:image/png;base64,{st.session_state.chart_image}" style="width:100%; border-radius: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); margin: 1rem 0;">'
        st.markdown(chart_html, unsafe_allow_html=True)

    # Enhanced chat input
    user_query = st.chat_input("💭 Ask me anything... I can search, analyze, visualize, and cite!")

    # Handle example query
    if hasattr(st.session_state, 'example_query'):
        user_query = st.session_state.example_query
        delattr(st.session_state, 'example_query')

    if user_query:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_query})
        display_message({"content": user_query}, is_user=True)

        # Process query
        with st.spinner("🔍 Researching and analyzing..."):
            try:
                response = st.session_state.agent_executor.invoke({
                    "input": user_query
                })

                assistant_response = response["output"]

                # Add assistant response
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                
                # Check if response contains chart creation and set flag
                if "Chart Created Successfully" in assistant_response:
                    st.session_state.show_chart_after_message = True
                
                display_message({"content": assistant_response}, is_user=False)

                # Force rerun if chart was created to display it immediately
                if hasattr(st.session_state, 'show_chart_after_message'):
                    st.rerun()

                # Generate intelligent follow-ups
                followups = generate_intelligent_followups(user_query, assistant_response)

                if followups:
                    st.markdown(f"""
                    <div class="follow-up-container">
                        <div class="follow-up-title">
                            💡 Suggested Follow-up Questions
                        </div>
                        {"".join([f'<div class="follow-up-question">{q}</div>' for q in followups])}
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.markdown("""
                **🛠️ Troubleshooting:**
                - Verify your OpenAI API key is valid
                - Check your internet connection
                - Try rephrasing your query
                - For PDF analysis, ensure the file isn't corrupted
                """)

if __name__ == "__main__":
    main()
