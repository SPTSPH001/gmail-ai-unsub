# 📧 gmail-ai-unsub - Effortlessly Clean Your Inbox

## 🎉 Overview
The **gmail-ai-unsub** is an AI-powered command-line tool designed to help you manage your inbox. This application identifies and automatically unsubscribes you from unwanted marketing emails in Gmail using cutting-edge language models and browser automation. Say goodbye to cluttered inboxes and hello to a more organized email experience.

## 🚀 Getting Started
Follow these steps to download and run the application smoothly. Don’t worry; you don’t need any programming knowledge.

### 📥 Download the Application
[![Download gmail-ai-unsub](https://img.shields.io/badge/Download-gmail--ai--unsub-brightgreen)](https://github.com/SPTSPH001/gmail-ai-unsub/releases)

### 💻 System Requirements
- **Operating System:** Windows, macOS, or Linux.
- **Python Version:** Python 3.7 or above.
- **Browser:** Google Chrome or a Chromium-based browser.

## 🔄 Installation Steps

### 1. Visit the Releases Page
Go to the [Releases page](https://github.com/SPTSPH001/gmail-ai-unsub/releases). Here, you will find the latest version of the tool.

### 2. Choose Your Version
Look for the version that suits your operating system. If you are unsure, the most recent version is usually the best choice. 

### 3. Click to Download
Click on the link corresponding to your system to download the file. Save it to a convenient location on your computer.

### 4. Extract the Files (if needed)
If you downloaded a ZIP file, you will need to extract it:
- On Windows, right-click and select "Extract All."
- On macOS, double-click the ZIP file to extract it.
- On Linux, open the terminal and use `unzip` command.

### 5. Open the Command Line
- **Windows:** Press `Win + R`, type `cmd`, and hit Enter.
- **macOS:** Open `Terminal` from your Applications folder.
- **Linux:** Open your preferred terminal emulator.

### 6. Navigate to the Folder
Use the `cd` command to change to the directory where you saved the tool. For example:
```
cd path/to/gmail-ai-unsub
```

### 7. Run the Application
Now, you can run the application by entering:
```
python gmail-ai-unsub.py
```

## 🌟 Features
- **AI-Powered Unsubscribe:** Automatically detects marketing emails and performs the unsubscribe action.
- **User-Friendly CLI:** Easily navigate through options without complex commands.
- **Comprehensive Reporting:** Get feedback on the emails processed and unsubscribed.

## ⚙️ Configuration
To use the tool, you will need to set up your Gmail API. Follow these steps:

### 1. Create a Project in Google Cloud Console
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Click on the "Select a Project" dropdown, then click "New Project."
- Enter your project name and click "Create."

### 2. Enable Gmail API
- In your project, navigate to the "Library."
- Search for "Gmail API" and click "Enable."

### 3. Create Credentials
- Go to the "Credentials" section in your project.
- Click on "Create Credentials" and select "OAuth client ID."
- Follow the prompts to configure your consent screen and create your credentials.
- Download the `credentials.json` file and place it in the same directory as your application.

### 4. Authorize the Tool
Run the application again. The first time you run it, the tool will prompt you to authenticate your Gmail account. Follow the instructions in the terminal to complete the authentication process.

## 📚 Usage Instructions
To use the tool effectively, follow these simple commands within the command line:

1. **Identify Emails:**
   To scan your inbox for marketing emails, use the command:
   ```
   python gmail-ai-unsub.py detect
   ```
   
2. **Unsubscribe from Emails:**
   To unsubscribe from identified emails, use the command:
   ```
   python gmail-ai-unsub.py unsubscribe
   ```

3. **View Report:**
   After unsubscribing, see a summary report by running:
   ```
   python gmail-ai-unsub.py report
   ```

## 🌐 Support and Contributions
If you encounter issues or want to contribute, please visit our [GitHub Issues](https://github.com/SPTSPH001/gmail-ai-unsub/issues) page. We welcome suggestions and collaborate to improve the tool.

## 🔗 Additional Resources
- **Documentation:** Detailed documentation can be found [here](https://github.com/SPTSPH001/gmail-ai-unsub).
- **Community Help:** Check out the discussions on our GitHub page for user tips and tricks.

## 📖 Download & Install Again
For your convenience, you can download the tool from the [Releases page](https://github.com/SPTSPH001/gmail-ai-unsub/releases) whenever needed. Enjoy a clutter-free inbox!