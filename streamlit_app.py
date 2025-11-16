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

# ✅ CHANGED: Replace OpenAI import with Google GenAI
# from langchain_openai import ChatOpenAI
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

# [CSS styling remains the same - truncated for brevity]

class PDFReaderTool:
    """Enhanced PDF reader tool with proper error handling"""
    # [Implementation remains the same]
    pass

class ChartMakerTool:
    """Enhanced chart creation tool with multiple chart types"""
    # [Implementation remains the same]
    pass

class CitationFormatterTool:
    """Enhanced citation formatter with multiple styles"""
    # [Implementation remains the same]
    pass

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

[Rest of system prompt remains the same]
"""),
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
    # [Implementation remains the same]
    pass

def initialize_session_state():
    """Initialize session state with enhanced memory management"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=4000
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

    # ✅ CHANGED: Updated sidebar configuration section
    st.sidebar.markdown("### 🔑 Configuration")

    # ✅ CHANGED: Try to get Gemini API key from environment first
    # Priority: GEMINI_API_KEY > GOOGLE_API_KEY
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if gemini_api_key:
        st.sidebar.success("✅ API key loaded from environment")
        # ✅ CHANGED: Updated info message
        key_var = "GEMINI_API_KEY" if os.getenv("GEMINI_API_KEY") else "GOOGLE_API_KEY"
        st.sidebar.info(f"Using environment variable {key_var}")
    else:
        st.sidebar.warning("⚠️ No environment API key found")
        # ✅ CHANGED: Updated input field for Gemini key
        gemini_api_key = st.sidebar.text_input(
            "Google Gemini API Key",
            type="password",
            help="Enter your Gemini API key from aistudio.google.com",
            placeholder="AI..."
        )

    if not gemini_api_key:
        st.sidebar.error("⚠️ API key required to continue")
        # ✅ CHANGED: Updated instructions
        st.sidebar.markdown("""
        **Two ways to provide API key:**
        1. Set environment variable: `GEMINI_API_KEY=your_key` or `GOOGLE_API_KEY=your_key`
        2. Enter manually in the field above

        **Get your free Gemini API key:**
        👉 [Google AI Studio](https://aistudio.google.com/app/apikey)
        """)
        return None

    try:
        # ✅ CHANGED: Initialize Gemini LLM instead of OpenAI
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",  # Using Gemini 2.5 Pro
            temperature=0.3,
            google_api_key=gemini_api_key,
            # ✅ CHANGED: Gemini uses max_output_tokens instead of max_tokens
            max_output_tokens=8192,  # Gemini 2.5 Pro supports up to 65536
            # ✅ CHANGED: Add convert_system_message_to_human for better compatibility
            convert_system_message_to_human=True
        )

        # Initialize enhanced tools (same as before)
        search_tool = DuckDuckGoSearchResults(
            num_results=10,
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

        # ✅ CHANGED: Add better error handling for Gemini-specific errors
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=st.session_state.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=6,
            return_intermediate_steps=True
        )

        return agent_executor

    except Exception as e:
        # ✅ CHANGED: Enhanced error messages for Gemini
        error_msg = str(e)
        if "API key" in error_msg or "authentication" in error_msg.lower():
            st.sidebar.error("❌ Invalid API key. Please check your Gemini API key.")
        elif "quota" in error_msg.lower() or "rate" in error_msg.lower():
            st.sidebar.error("❌ Rate limit exceeded. Please wait and try again.")
        elif "500" in error_msg:
            st.sidebar.error("❌ Gemini server error. Please retry in a few seconds.")
        else:
            st.sidebar.error(f"❌ Setup failed: {error_msg}")
        return None

def display_message(message: Dict[str, str], is_user: bool = True):
    """Display messages with enhanced styling"""
    # [Implementation remains the same]
    pass

def main():
    """Enhanced main application with modern UI"""

    # Modern header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 ARIA - Advanced Research Intelligence Assistant</h1>
        <p>Powered by Google Gemini 2.5 Pro • LangChain Agents • Real-time Web Search</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state
    initialize_session_state()

    # Sidebar configuration
    with st.sidebar:
        st.markdown("## ⚙️ Control Panel")

        # PDF upload section
        st.markdown("### 📄 Document Upload")
        uploaded_file = st.file_uploader(
            "Upload PDF for analysis",
            type=['pdf'],
            help="Upload a PDF document to analyze with the AI assistant"
        )

        if uploaded_file is not None:
            st.session_state.pdf_content = uploaded_file.read()
            st.session_state.pdf_filename = uploaded_file.name
            st.success(f"✅ Loaded: {uploaded_file.name}")

        # Clear conversation
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.memory.clear()
            st.session_state.chart_image = None
            st.rerun()

        # Model info
        st.markdown("---")
        st.markdown("### 🤖 Model Information")
        st.info("""
        **Model:** Gemini 2.5 Pro
        **Context:** 1M tokens
        **Output:** 65K tokens max
        **Features:** Multimodal, Function calling
        """)

    # Setup agent
    if st.session_state.agent_executor is None:
        st.session_state.agent_executor = setup_enhanced_agent()

    if st.session_state.agent_executor is None:
        st.warning("⚠️ Please configure your Gemini API key in the sidebar to begin research.")
        return

    # Display chat messages
    for message in st.session_state.messages:
        display_message(message, is_user=message["role"] == "user")

    # Chat input
    if prompt := st.chat_input("Ask me anything... I can search the web, analyze PDFs, create charts, and more!"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_message({"role": "user", "content": prompt}, is_user=True)

        # Get agent response with error handling
        with st.spinner("🔍 Researching and analyzing..."):
            try:
                # ✅ CHANGED: Add retry logic for Gemini-specific errors
                max_retries = 3
                retry_count = 0
                response = None

                while retry_count < max_retries:
                    try:
                        response = st.session_state.agent_executor.invoke({"input": prompt})
                        break  # Success, exit retry loop
                    except Exception as e:
                        error_str = str(e)
                        if "500" in error_str and retry_count < max_retries - 1:
                            # Gemini 500 error - retry with exponential backoff
                            import time
                            wait_time = 2 ** retry_count
                            st.warning(f"⚠️ Temporary error. Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                            retry_count += 1
                        else:
                            raise e

                if response:
                    assistant_response = response["output"]

                    # Add assistant message
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response
                    })

                    # Display response
                    display_message({
                        "role": "assistant",
                        "content": assistant_response
                    }, is_user=False)

                    # Generate and display follow-up questions
                    followups = generate_intelligent_followups(prompt, assistant_response)
                    if followups:
                        st.markdown("### 💡 Suggested Follow-ups:")
                        for i, followup in enumerate(followups[:3], 1):
                            st.markdown(f"{i}. {followup}")

            except Exception as e:
                error_message = f"❌ Error: {str(e)}"

                # ✅ CHANGED: Enhanced error handling for Gemini-specific issues
                if "quota" in str(e).lower() or "rate" in str(e).lower():
                    error_message = """❌ Rate limit exceeded. 

**Solutions:**
- Wait a few minutes and try again
- Check your Gemini API quota at console.cloud.google.com
- Consider upgrading to a paid tier for higher limits"""

                elif "500" in str(e):
                    error_message = """❌ Gemini server error (500).

**Solutions:**
- This is a temporary Google server issue
- Try again in a few seconds
- The error usually resolves automatically"""

                elif "authentication" in str(e).lower() or "api key" in str(e).lower():
                    error_message = """❌ Authentication error.

**Solutions:**
- Verify your API key is correct
- Get a new key at https://aistudio.google.com/app/apikey
- Check that the key is active and not expired"""

                st.error(error_message)

                # Add error to conversation for context
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })

if __name__ == "__main__":
    main()
