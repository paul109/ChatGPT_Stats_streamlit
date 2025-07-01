from __future__ import annotations

import json
import os
import requests

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# ────────────────────────  Request Capping  ──────────────────────────
# Initialize session state for request counting
if 'request_count' not in st.session_state:
    st.session_state.request_count = 0

# Get the request limit from environment variable or default to 500
REQUEST_LIMIT = int(os.getenv('REQUEST_LIMIT', '500'))

# ────────────────────────  Page setup  ──────────────────────────
st.set_page_config(page_title='ChatGPT Wrapped', page_icon='🤖', layout='centered')

# Custom CSS for Notion/Apple font
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Apply SF Pro Display (Apple's system font) with fallbacks */
* {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Inter', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

/* Ensure all text elements use the font */
.stMarkdown, .stText, .stTitle, .stHeader, .stSubheader, .stMetric, .stButton, .stSelectbox, .stTextInput, .stFileUploader {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Inter', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

/* Specific styling for headers to match Notion's style */
h1, h2, h3, h4, h5, h6 {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Inter', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.025em !important;
}

/* Body text styling */
p, div, span {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Inter', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
    font-weight: 400 !important;
    line-height: 1.5 !important;
}

/* Increase font size for metric values */
.stMetric [data-testid="metric-container"] [data-testid="metric-value"] {
    font-size: 2rem !important;
    font-weight: 600 !important;
}

/* Increase font size for metric labels */
.stMetric [data-testid="metric-container"] [data-testid="metric-label"] {
    font-size: 1.2rem !important;
    font-weight: 500 !important;
}
</style>
""", unsafe_allow_html=True)

st.title('ChatGPT Wrapped ')


st.markdown(
        '1. On chatgpt.com click on your 👤 User Icon and click on ⚙️ Settings \n'
        '2. Click on Data and Controls and "Export data" and confirm export \n'
        '3. Wait for the Email from OpenAI and Download the data export \n'
        '4. Unzip the file and drag the conversations.json file below'
    )

uploaded_file = st.file_uploader('Upload conversations.json', type=['json'])

if uploaded_file is None:
    st.info('Upload the conversations file to begin.')
    st.stop()

# ────────────────────────  Load & normalize  ────────────────────
raw = json.load(uploaded_file)

# Handle the new export format - list of conversations with mapping
if isinstance(raw, list):
    convos = raw
else:
    # Fallback for old format
    convos = raw['conversations'] if isinstance(raw, dict) and 'conversations' in raw else raw



# Create progress bar
progress_bar = st.progress(0)
status_text = st.empty()
status_text.text("📊 Parsing conversations and calculating statistics...")

rows: list[dict] = []
total_convos = len(convos)

for i, convo in enumerate(convos):
    # Update progress bar
    progress = (i + 1) / total_convos
    progress_bar.progress(progress)
    status_text.text(f"📊 Processing conversation {i + 1} of {total_convos}...")
    
    convo_id = convo.get('id') or convo.get('conversation_id')
    
    # Handle the new mapping structure
    if 'mapping' in convo and isinstance(convo['mapping'], dict):
        messages = []
        for node_id, node in convo['mapping'].items():
            if node.get('message') and isinstance(node['message'], dict):
                messages.append(node['message'])
    else:
        # Fallback for old format
        messages = (
            convo.get('mapping', {}).values() if 'mapping' in convo else convo.get('messages', [])
        )
    
    for m in messages:
        if not isinstance(m, dict):
            continue
            
        role = (
            m.get('author', {}).get('role') if 'author' in m else m.get('role', '')
        )
        
        # More robust content extraction for new format
        content = ''
        if m.get('content') and isinstance(m.get('content'), dict):
            content_obj = m.get('content', {})
            if content_obj.get('content_type') == 'text' and content_obj.get('parts'):
                content = content_obj.get('parts', [''])[0] or ''
            elif isinstance(content_obj.get('text'), str):
                content = content_obj.get('text', '')
        elif m.get('text'):
            content = m.get('text')
        elif m.get('message') and isinstance(m.get('message'), dict):
            message_content = m.get('message', {}).get('content', {})
            if isinstance(message_content, dict) and message_content.get('parts'):
                content = message_content.get('parts', [''])[0] or ''
            elif isinstance(message_content, str):
                content = message_content
        elif isinstance(m.get('content'), str):
            content = m.get('content', '')
        
        ts = m.get('create_time') or m.get('timestamp')
        if ts is None:
            continue
        rows.append(
            {
                'conversation_id': convo_id,
                'role': role,
                'content': content,
                'timestamp': float(ts),
            }
        )

# Update progress for final calculations
status_text.text("📊 Creating DataFrame and calculating statistics...")
progress_bar.progress(0.9)

if not rows:
    st.error('Could not find any messages in the uploaded file – check the export.')
    st.stop()

# DataFrame & quick derives
df = pd.DataFrame(rows)
df['dt'] = pd.to_datetime(df['timestamp'], unit='s')
user_df = df[df['role'] == 'user'].copy()
user_df['date'] = user_df['dt'].dt.date
user_df['word_count'] = user_df['content'].str.split().str.len()

# Add more derived columns for additional metrics
user_df['day_of_week'] = user_df['dt'].dt.day_name()
user_df['hour'] = user_df['dt'].dt.hour
user_df['month'] = user_df['dt'].dt.month_name()
user_df['is_weekend'] = user_df['dt'].dt.weekday >= 5

# ────────────────────────  Descriptive stats  ───────────────────
if user_df.empty:
    st.error('No user messages were detected.')
    st.stop()

daily_counts = user_df.groupby('date').size()
conv_lengths = user_df.groupby('conversation_id').size()
total_words = user_df['word_count'].sum()

# Complete the progress bar
progress_bar.progress(1.0)
status_text.empty()  # Clear the status text

st.header('📊 Quick Stats')
col1, col2, col3 = st.columns(3)
col1.metric('Total requests', len(user_df))
col2.metric('Total conversations', len(convos))
col3.metric('Avg. requests / day', f'{daily_counts.mean():.1f}')

col1, col2, col3 = st.columns(3)
col1.metric('Avg. words / request', f'{user_df.word_count.mean():.1f}')
col2.metric('Total words written', f'{total_words:,}')
col3.metric('Max requests in a day', int(daily_counts.max()))

col1, col2, col3 = st.columns(3)
col1.metric('Avg. conversation length', f'{conv_lengths.mean():.1f} user msgs')
col2.write('')  # Empty space for spacing
col3.write('')  # Empty space for spacing

# ────────────────────────  Additional Fun Metrics  ───────────────────
st.header('📈 Usage Patterns')

# Time-based metrics
col1, col2, col3 = st.columns(3)

most_active_day = user_df['day_of_week'].value_counts().index[0]
col1.metric('Most active day', most_active_day)

most_active_hour = user_df['hour'].value_counts().index[0]
col2.metric('Peak hour', f'{most_active_hour}:00')

busiest_month = user_df['month'].value_counts().index[0]
col3.metric('Busiest month', busiest_month)


# Daily requests chart
st.subheader('Requests per Day')
st.bar_chart(daily_counts)

# Day of week distribution
st.subheader('Activity by Day of Week')
day_counts = user_df['day_of_week'].value_counts()
st.bar_chart(day_counts)

# Hour distribution
st.subheader('Activity by Hour of Day')
hour_counts = user_df['hour'].value_counts().sort_index()
st.bar_chart(hour_counts)

# ────────────────────────  LLM‑powered insights  ────────────────
st.header('🤖 AI-Powered Insights')

# Extract the user messages from the df and join them into a new string, seperated by a line break between each message and two line breaks between each conversation
# Also truncate the messages to 70 words
messages_string = ''
conversation_id = user_df['conversation_id'].iloc[0]
for i in range(len(user_df)):
    if user_df['conversation_id'].iloc[i] != conversation_id:
        messages_string += '\n\n'
        conversation_id = user_df['conversation_id'].iloc[i]
    
    content = user_df['content'].iloc[i]
    words = content.split()
    if len(words) > 100:
        # Truncate to 70 words and join back
        truncated_content = ' '.join(words[:100])
        messages_string += truncated_content + '\n'
    else:
        messages_string += content + '\n'

# Check if Gemini API key is available
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    st.warning('⚠️ Gemini API key not found. To enable AI insights, set the GEMINI_API_KEY environment variable.')
else:
    # Initialize variables
    summary = ""
    topics = []
    
    # Automatically generate AI insights
    with st.spinner('🤖 Analyzing your chat history...'):
        try:
            import google.generativeai as genai
            
            # Configure the API key
            genai.configure(api_key=gemini_api_key)
            
            # Create the model with system instruction
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for more deterministic output
                ),
                system_instruction="""
                    You are a helpful assistant that is worldclass at parsing large amounts of data and deriving insights from them. 
                    You are going to be given a string of data that contains all the messages from a user's chat history with ChatGPT.
                    You're task is to write a 4 sentence summary of the user based on the chat history and provide 10 the most prominent topics in the total chat history.
                    Do not overemphasize recent topics, focus on the overall usage patterns and trends.
                    
                    CRITICAL: You must respond with ONLY valid JSON in exactly this format, with no additional text, markdown, or formatting:
                    {
                        "summary": "Your 4 sentence summary here",
                        "topics": ["topic1", "topic2", "topic3", "topic4", "topic5", "topic6", "topic7", "topic8", "topic9", "topic10"]
                    }
                    
                    IMPORTANT RULES:
                    1. Start your response with { and end with }
                    2. Use double quotes for all strings and keys
                    3. Do not include any text before or after the JSON
                    4. Do not use markdown formatting like ```json
                    5. Ensure all strings are properly escaped
                    6. The summary should be exactly 4 sentences
                    7. The topics array should contain exactly 10 topics
                    8. Do not include any comments or explanations
                    9. Make sure all quotes are properly closed
                    10. Use simple, clear topic names (1-3 words each)
                    
                    Example of valid response:
                    {"summary": "This user frequently asks for help with programming and technical questions. They seem to be working on various software projects and learning new technologies. The user often requests code examples and explanations for complex concepts. They appear to be a developer or student interested in improving their technical skills.", "topics": ["programming", "code examples", "technical questions", "software development", "learning", "debugging", "algorithms", "web development", "data structures", "best practices"]}
                    
                    Do not include any other text, explanations, or formatting. Only the JSON object.
                    """
            )
            
            # Generate insights based on the user's data
            response = model.generate_content(f"{messages_string}")
            
            # Parse JSON response with automatic fallback handling (errors logged to console only)
            response_data = None
            
            if not response or not hasattr(response, 'text'):
                print("Console: No response received from Gemini API")
                response_data = None
            else:
                response_text = response.text.strip()
                
                if not response_text:
                    print("Console: Empty response received from Gemini API")
                    response_data = None
                else:
                    import re
                    
                    def try_parse_json(text):
                        """Try to parse JSON with multiple strategies"""
                        strategies = [
                            # Strategy 1: Direct parsing
                            lambda t: json.loads(t),
                            
                            # Strategy 2: Remove markdown code blocks
                            lambda t: json.loads(re.sub(r'```json\s*|```\s*', '', t).strip()),
                            
                            # Strategy 3: Extract JSON with regex and clean
                            lambda t: json.loads(re.search(r'\{.*\}', t, re.DOTALL).group(0).strip()),
                            
                            # Strategy 4: Fix quotes and try again
                            lambda t: json.loads(re.sub(r'```json\s*|```\s*', '', t).strip().replace("'", '"')),
                            
                            # Strategy 5: More aggressive cleaning
                            lambda t: json.loads(re.sub(r'```json\s*|```\s*|^[^{]*|[^}]*$', '', t, flags=re.MULTILINE).strip()),
                        ]
                        
                        for i, strategy in enumerate(strategies):
                            try:
                                result = strategy(text)
                                print(f"Console: JSON parsed successfully using strategy {i+1}")
                                return result
                            except Exception as e:
                                print(f"Console: Strategy {i+1} failed: {str(e)}")
                                continue
                        
                        print("Console: All JSON parsing strategies failed")
                        return None
                    
                    response_data = try_parse_json(response_text)
            
            # Always display insights in a clean, user-friendly way
            if response_data:
                # AI-generated insights
                topics = response_data.get('topics', [])
                summary = response_data.get('summary', '')
            else:
                # Fallback to data-driven insights
                print("Console: Using fallback analysis due to parsing failure")
                
                # Generate basic insights from the data
                total_messages = len(user_df)
                avg_words = user_df['word_count'].mean()
                most_active_hour = user_df['hour'].value_counts().index[0]
                most_active_day = user_df['day_of_week'].value_counts().index[0]
                
                summary = f"This user has sent {total_messages} messages to ChatGPT with an average of {avg_words:.1f} words per message. They are most active during {most_active_hour}:00 and prefer {most_active_day}s for their conversations. The user appears to be engaged in regular communication with the AI assistant."
                
                # Extract potential topics from message content
                all_words = ' '.join(user_df['content'].astype(str)).lower()
                common_words = pd.Series(all_words.split()).value_counts().head(20)
                
                # Filter out common stop words
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'his', 'hers', 'ours', 'theirs'}
                topics = [word for word in common_words.index if word not in stop_words and len(word) > 3][:10]

        except Exception as e:
            print(f"Console: Error generating AI insights: {str(e)}")
            # Fallback to basic data analysis if API completely fails
            summary = f"You've sent {len(user_df)} messages with an average of {user_df['word_count'].mean():.1f} words per message. You're most active at {user_df['hour'].value_counts().index[0]}:00 on {user_df['day_of_week'].value_counts().index[0]}s."
            topics = []

    # Display user summary with nice formatting (outside spinner)
    if summary:
        st.subheader('📝 Your ChatGPT Usage Profile')
        st.markdown(f"*{summary}*")
    
    # Display topics with nice formatting (outside spinner)  
    if topics:
        st.subheader('🔍 Your Main Discussion Topics')
        
        # Create a nice grid layout for topics
        cols = st.columns(2)
        for i, topic in enumerate(topics[:10]):
            with cols[i % 2]:
                st.markdown(f"• **{topic.title()}**")
    
    # Generate AI portrait if available (separate spinner)
    if summary:
        api_token = os.environ.get("HF_API_TOKEN")
        if api_token:
            from huggingface_hub import InferenceClient
            from PIL import Image

            MODEL_ID = "black-forest-labs/FLUX.1-dev"
            IMG_PATH = "output.png"

            with st.spinner('🎨 Generating your AI portrait…'):
                try:
                    client = InferenceClient(model=MODEL_ID, token=api_token, timeout=180)
                    
                    # Enhanced prompt for better results with Flux
                    enhanced_prompt = f"Generate a drawning of a male in a setting that showcases the man's personality, interests by sourounding him with objects that refelct his interestsbased based on the following description and the following interests: {summary}, {topics}"

                    img = client.text_to_image(
                        prompt=enhanced_prompt,
                        guidance_scale=3.5,
                        num_inference_steps=28,
                        height=1024,
                        width=1024,
                    )
                    img.save(IMG_PATH)
                    st.subheader("🎨 Your AI‑Generated Drawing")
                    st.image(IMG_PATH)
                except Exception as e:
                    print(f"Console: Image generation error: {e}")
                    st.info("Image generation is temporarily unavailable.")
        else:
            st.info("Set the HF_API_TOKEN environment variable to enable image generation.")

# ────────────────────────  Footer  ──────────────────────────────
st.markdown("---")
st.caption('🔒 **Privacy Notice**: Your data is processed locally. When using AI insights, message content is sent to Google Gemini API. Data sent to Google is subject to their [Privacy Policy](https://policies.google.com/privacy). No data is stored on our servers.')
