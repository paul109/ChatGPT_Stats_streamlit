# ChatGPT Wrapped

A Streamlit app that analyzes your ChatGPT conversation history and provides insights about your usage patterns, powered by Google's Gemini AI.

## Features

- 📊 **Usage Statistics**: Total requests, conversations, words written, and more
- 📈 **Usage Patterns**: Activity by day of week, hour of day, and month
- 🤖 **AI-Powered Insights**: Personalized insights about your ChatGPT usage using Gemini AI


## Setup

### Prerequisites

- Python 3.8+
- A Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey) (required for AI insights)
- A Hugging Face API token from [Hugging Face](https://huggingface.co/settings/tokens) (optional, for AI portrait generation)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ChatGPT_Stats_streamlit
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API keys**
   
   Copy the example environment file and add your actual API keys:
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file:
   ```bash
   # .env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   HF_API_TOKEN=your_actual_hugging_face_token_here
   REQUEST_LIMIT=500
   ```
   
   **Get your API keys:**
   - **Gemini API Key**: Go to [Google AI Studio](https://makersuite.google.com/app/apikey), create a new API key
   - **Hugging Face Token** (optional): Go to [Hugging Face Tokens](https://huggingface.co/settings/tokens), create a new token with "Read" access

4. **Run the app locally**
   ```bash
   streamlit run streamlit_app.py
   ```

5. **Use the app**
   - Follow the instructions in the app to export your ChatGPT data
   - Upload the `conversations.json` file
   - View your personalized insights!

### Deployment

#### Option 1: Streamlit Community Cloud (Recommended - Free)

**Step 1: Prepare your repository**
```bash
# Make sure .env is not committed (check .gitignore)
git add .
git commit -m "Ready for deployment"
git push origin main
```

**Step 2: Deploy on Streamlit Cloud**
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set main file path: `streamlit_app.py`
6. Click "Advanced settings..."
7. Add your **secrets** (environment variables):
   ```toml
   # Secrets format in Streamlit Cloud
   GEMINI_API_KEY = "your_actual_gemini_api_key_here"
   HF_API_TOKEN = "your_actual_hugging_face_token_here"
   REQUEST_LIMIT = "500"
   ```
8. Click "Deploy!"

**Important Security Notes:**
- ✅ **Never commit your `.env` file** - it's already in `.gitignore`
- ✅ **Use Streamlit's secrets management** - your API keys are encrypted
- ✅ **Only you can see your secrets** - they're not visible to users

#### Option 2: Railway

1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Add environment variables:
   - `GEMINI_API_KEY`: Your Gemini API key
   - `HF_API_TOKEN`: Your Hugging Face token
   - `REQUEST_LIMIT`: 500
4. Deploy with one click

#### Option 3: Render

1. Go to [render.com](https://render.com)
2. Create a new Web Service
3. Connect your GitHub repository
4. Add environment variables in the dashboard
5. Deploy

#### Option 4: Heroku

1. Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Create a Heroku app:
   ```bash
   heroku create your-app-name
   ```
3. Set environment variables:
   ```bash
   heroku config:set GEMINI_API_KEY=your_key
   heroku config:set HF_API_TOKEN=your_token
   heroku config:set REQUEST_LIMIT=500
   ```
4. Deploy:
   ```bash
   git push heroku main
   ```

#### Cost Comparison
- **Streamlit Cloud**: Free (with usage limits)
- **Railway**: Free tier available, then pay-as-you-go
- **Render**: Free tier available
- **Heroku**: Free tier discontinued, paid plans start at $5/month

## How to Export ChatGPT Data

1. Go to [chatgpt.com](https://chatgpt.com)
2. Click on your 👤 User Icon
3. Click on ⚙️ Settings
4. Click on "Data and Controls"
5. Click "Export data" and confirm
6. Wait for the email from OpenAI
7. Download and unzip the export
8. Upload the `conversations.json` file to the app

## Privacy & Security

### Data Processing
- ✅ **Local Analysis**: Basic statistics and usage patterns are calculated locally in your browser
- ✅ **No Local Storage**: We don't store your conversations or personal data on our servers
- ✅ **Open Source**: You can review all the code to understand exactly what happens to your data

### AI-Powered Insights (Optional)
- ⚠️ **Google Gemini API**: When using AI insights, your message content is sent to Google's Gemini API
- 📝 **Data Minimization**: Only message content is sent (truncated to 100 words per message)
- 🚫 **No PII**: No personal identifiers, timestamps, or conversation IDs are sent to Google
- 🔄 **One-time Processing**: Data is sent once for analysis and not stored locally

### Data Sent to Third Parties
- **Google Gemini API**: Message content for AI analysis (only if GEMINI_API_KEY is set)
- **Hugging Face**: AI-generated summary for portrait generation (only if HF_API_TOKEN is set)

### Privacy Options
- **Skip AI Features**: Don't set the `GEMINI_API_KEY` to avoid sending data to Google
- **Local Only**: The app works without AI features for basic statistics
- **Review Policies**: Check [Google's Privacy Policy](https://policies.google.com/privacy) and [Gemini API Terms](https://ai.google.dev/terms) for current data handling practices

### Important Notes
- Data sent to Google is subject to their privacy policy and data retention practices
- While Google states they don't store API data for training, they may log usage for abuse prevention
- You control your own API keys and can revoke access at any time

## Cost & API Usage

### Your API Keys, Your Control
- **You pay**: Only for your own API usage when people use your deployed app
- **Typical costs**: Very low - Gemini API costs ~$0.001-0.01 per request depending on usage
- **No hidden fees**: You control your own API keys and can monitor usage in your Google/HF dashboards
- **Usage monitoring**: Set up billing alerts in Google Cloud Console to track costs

### Protecting Your API Keys
When you deploy, your API keys are:
- ✅ **Encrypted** on the deployment platform
- ✅ **Not visible** to app users 
- ✅ **Not committed** to your GitHub repository
- ✅ **Yours to control** - revoke or rotate anytime

### Optional: User-Provided Keys
If you prefer users to use their own API keys, you can modify the app to:
1. Accept API keys through Streamlit's `st.text_input()` 
2. Remove the environment variable loading
3. Use user-provided keys for API calls

This way users pay for their own usage, but requires more setup for each user.

## Troubleshooting

### "Gemini API key not found"
- Make sure you've created a `.env` file with your API key
- Check that the key is correct and active
- For deployment, verify the environment variable is set correctly

### "Error generating AI insights"
- Check your Gemini API quota and billing
- Verify your API key is valid
- Try refreshing the page

### "Could not find any messages"
- Make sure you're uploading the correct `conversations.json` file
- Check that the export completed successfully
- Try re-exporting your data from ChatGPT

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - feel free to use this code for your own projects. 