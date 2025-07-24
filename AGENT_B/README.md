# 🤖 Agent_B - Intelligent Browser Automation Agent

Agent_B is an advanced browser automation agent that can perform complex web tasks using natural language instructions. Built with a clean, modern interface and powered by state-of-the-art language models.

## ✨ Features

### 🎯 **Simplified Interface**
- **Clean Design**: Minimalist UI focused on essential controls
- **Agent Branding**: Prominent Agent_B icon and name
- **Intuitive Layout**: Task input → Model selection → Run/Stop controls

### 🧠 **Smart AI Integration**
- **Google Models Default**: Optimized for Google's Gemini models
- **Multi-Provider Support**: OpenAI, Anthropic, Google, Ollama, Azure, DeepSeek, Mistral
- **Advanced Models**: Support for latest Gemini 2.0, GPT-4, Claude 3, and more

### 🌐 **Live Browser Process**
- **Embedded Browser**: Browser runs directly in the UI
- **Real-time Screenshots**: Live view of browser actions
- **Process Monitoring**: Watch the agent work in real-time
- **Smart Configuration**: Optimized browser settings for automation

### 🚀 **Enhanced User Experience**
- **One-Click Launch**: Simple batch script to start everything
- **Setup Validation**: Automatic testing of dependencies and configuration
- **Status Updates**: Clear feedback on agent progress
- **Error Handling**: Comprehensive error reporting and recovery

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Chrome/Chromium browser
- **Windows**: Batch scripts included
- **Linux**: See [LINUX_SETUP.md](LINUX_SETUP.md) for detailed instructions

### Quick Start

1. **Clone or download** the project to your local machine

2. **Install dependencies** using the turboo virtual environment:
   ```bash
   # Activate virtual environment
   turboo\Scripts\activate.bat
   
   # Install requirements
   cd AGENT_B
   pip install -r requirements.txt
   ```

3. **Configure API Keys** in `.env` file:
   ```env
   # At minimum, configure one of these:
   GOOGLE_API_KEY=your_google_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

4. **Launch Agent_B**:
   
   **Windows**:
   ```bash
   # Easy way - double-click:
   launch_agent_b.bat
   
   # Or manually:
   python webui.py
   ```
   
   **Linux**:
   ```bash
   # With display:
   python webui.py
   
   # Headless (no display):
   ./run_headless.sh
   ```

5. **Access the interface** at: http://127.0.0.1:7788

## 🎮 How to Use

### Basic Workflow

1. **Enter Task**: Describe what you want the agent to do in natural language
   - Example: "Go to Google and search for 'Python automation'"
   - Example: "Navigate to Amazon and find the best-selling books"

2. **Configure Model** (Optional): 
   - Click "🧠 LLM & Model Selection" to adjust settings
   - Default: Google Gemini 2.0 Flash Exp (recommended)

3. **Run Agent**: Click "🚀 Run Agent" to start the automation

4. **Monitor Progress**: 
   - Watch live browser screenshots
   - Read agent thoughts and actions in real-time
   - Check status updates

5. **Stop if Needed**: Click "⏹️ Stop" to halt the agent safely

### Advanced Features

- **Temperature Control**: Adjust model creativity (0.0 = focused, 1.0 = creative)
- **Max Steps**: Limit the number of actions the agent can take
- **Live Screenshots**: Real-time browser view updates every 3 seconds
- **Error Recovery**: Automatic handling of common browser issues

## 🔧 Configuration

### Environment Variables

The `.env` file supports various configuration options:

```env
# LLM API Keys
GOOGLE_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Browser Settings (automatically configured)
CHROME_PATH=
CHROME_USER_DATA=
RESOLUTION_WIDTH=1280
RESOLUTION_HEIGHT=720

# Logging
BROWSER_USE_LOGGING_LEVEL=info
```

### Supported Models

#### Google (Default)
- `gemini-2.0-flash-exp` (Recommended)
- `gemini-2.0-flash`
- `gemini-1.5-pro`
- `gemini-1.5-flash`

#### OpenAI
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-4-turbo`

#### Anthropic
- `claude-3-opus`
- `claude-3-sonnet`
- `claude-3-haiku`

## 🧪 Testing

Run the setup test to verify everything is working:

```bash
cd AGENT_B
python test_setup.py
```

This will check:
- ✅ All dependencies are installed
- ✅ Environment variables are configured
- ✅ WebUI can be created
- ✅ Custom modules can be imported

## 🚨 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Make sure you're in the turboo virtual environment
   - Run: `pip install -r requirements.txt`

2. **"No API key configured"**
   - Check your `.env` file
   - Ensure at least one API key is set and valid

3. **Browser won't start**
   - Check if Chrome/Chromium is installed
   - Try running as administrator

4. **WebUI won't load**
   - Check if port 7788 is available
   - Try a different port: `python webui.py --port 8080`

### Getting Help

- Check the console output for detailed error messages
- Run `python test_setup.py` to diagnose issues
- Ensure all files in the `src/` directory are present

## 🎯 Example Tasks

Here are some example tasks you can try with Agent_B:

### Web Research
```
"Search for the latest news about artificial intelligence and summarize the top 3 articles"
```

### E-commerce
```
"Go to Amazon and find the best-rated wireless headphones under $100"
```

### Social Media
```
"Navigate to Twitter and check the trending topics"
```

### Data Collection
```
"Visit Wikipedia and get information about the population of the top 5 largest cities"
```

### Form Filling
```
"Go to this contact form [URL] and fill it out with test data"
```

## 🔄 Updates & Improvements

Agent_B includes several improvements over the original ONLYAGENT:

1. **Simplified UI**: Removed complex configuration options
2. **Google Default**: Optimized for Google's powerful models
3. **Live Browser**: Embedded browser with real-time screenshots
4. **Better UX**: Cleaner layout and improved user experience
5. **Smart Defaults**: Pre-configured settings for optimal performance

## 📝 License

This project is based on the ONLYAGENT framework and includes custom improvements for enhanced usability and performance.

---

**Happy Automating! 🚀**

For questions or issues, please check the troubleshooting section or run the test script for diagnostics. 