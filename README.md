# Commit Review Assistant



An AI-powered Git commit review tool that automatically analyzes your repository's commits and provides intelligent feedback on code quality, commit message effectiveness, and best practices.

## Features

- 🔍 **AI-Powered Code Reviews**: Uses Ollama's LLM to provide meaningful code reviews
- 🔄 **Automatic Repository Monitoring**: Watches for new commits in real-time
- 📊 **Structured Analysis**: Reviews code quality, commit messages, and potential issues
- 🚀 **User-Friendly Interface**: Clean, modern UI built with CustomTkinter
- ⚙️ **Configurable**: Adjustable monitoring intervals and repository selection

## Prerequisites

- Python 3.7+
- Git
- [Ollama](https://ollama.ai/) with the `llama3.2` model installed

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/commit-review-assistant.git
   cd commit-review-assistant
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

## Usage

1. Start the application
2. Select your Git repository (or it will try to use the current directory if it's a Git repo)
3. The tool will automatically start monitoring for changes
4. Press "Check Now" to manually trigger a review
5. Use "Refresh Repo" if you want to fetch the latest changes without waiting for the auto-check

## Creating an Executable

You can create a standalone executable using the included build script:

```
python build_exe.py
```

The executable will be created in the `build/CommitReviewAssistant` directory.

## Requirements

See `requirements.txt` for a list of dependencies:

- customtkinter
- gitpython
- ollama
- cx_Freeze (for building the executable)

## Project Structure

```
commit-review-assistant/
├── main.py              # Main application code
├── build_exe.py         # Script to create standalone executable
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.