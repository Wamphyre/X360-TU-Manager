# X360 TU Manager

[![GitHub Repository](https://img.shields.io/badge/GitHub-X360--TU--Manager-blue?logo=github)](https://github.com/Wamphyre/X360-TU-Manager)
[![Python](https://img.shields.io/badge/Python-3.8+-green?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](https://github.com/Wamphyre/X360-TU-Manager/blob/main/LICENSE)

**X360 TU Manager** is a Python GUI tool for **managing and downloading Title Updates (TUs)** for Xbox 360 games from [XboxUnity](https://xboxunity.net), using each game's **MediaID** and **TitleID**.

## ✨ Features

- 🎮 **Automatic game detection** from folders containing Xbox 360 games
- 🔍 **MediaID and TitleID extraction** using XexTool from default.xex files
- 🌐 **XboxUnity integration** with API Key or username/password authentication
- 📥 **Smart TU downloading** with original filenames from XboxUnity servers
- 🎯 **MediaID filtering** - only downloads TUs that match your exact game version
- � ***Organized folder structure** - downloads TUs into game-named folders
- � **QTuick copy functions** for MediaID and TitleID to clipboard
- � ***HTML export** - generate a complete game catalog for inventory control and management
- 💾 **Advanced USB preparation** - automatic TU type detection (Cache vs Content)
- � **Dual eTU support** - handles both uppercase (Cache) and lowercase (Content) formats
- 📊 **Progress tracking** with detailed logs and statistics

## 📸 Screenshot

![X360 TU Manager Interface](screenshot.png)

---

## ☕ Support the Project

If you find X360 TU Manager useful, consider supporting its development:

[![Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/wamphyre94078)

Your support helps maintain and improve this tool for the Xbox 360 community! 🎮

---

## 📦 Requirements

- **Python 3.8+** (tested on 3.10 and 3.11)
- **Wine** (on Linux/macOS, automatically detected - to run `XexTool.exe`)
- **XboxUnity account** or API Key
- Python dependencies:
  ```bash
  pip install requests tkinter
  ```

### 🖥️ Cross-Platform Support
- **Windows**: Runs XexTool.exe natively (no Wine needed)
- **Linux**: Automatically uses Wine to run XexTool.exe
- **macOS**: Automatically uses Wine to run XexTool.exe

---

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Wamphyre/X360-TU-Manager.git
   cd X360-TU-Manager
   ```
2. **Install Python dependencies**:
   ```bash
   pip install requests
   ```
3. **Install Wine** (Linux/macOS only - automatically detected):
   ```bash
   # Ubuntu/Debian
   sudo apt install wine

   # Arch Linux
   sudo pacman -S wine

   # macOS (using Homebrew)
   brew install wine-stable
   ```
4. **Ensure XexTool.exe** is in the `xextool/` folder (included in repository)

---

## 🎯 How to Use

### Step 1: Authentication
1. **Launch the application**:
   ```bash
   python3 main.py
   ```
2. **Choose authentication method**:
   - **Option A**: Enter your XboxUnity **API Key** (recommended)
   - **Option B**: Enter your XboxUnity **username and password**
3. **Click "Login"** to authenticate

### Step 2: Detect Games
1. **Click "Select Games Folder"**
2. **Choose the folder** containing your Xbox 360 games
   - Each game should be in its own subfolder
   - Each game folder must contain a `default.xex` file
3. **Wait for detection** - the tool will automatically:
   - Scan all subfolders for `default.xex` files
   - Extract MediaID and TitleID from each game
   - Display results in the games list

### Step 3: Download Title Updates
1. **Click "Search and Download TUs"**
2. **Select destination folder** where TUs will be saved
3. **Wait for processing** - the tool will:
   - Search XboxUnity for each game's TUs
   - Filter TUs to match your specific MediaID
   - Download TUs into organized folders (one per game)
   - Show progress and detailed logs

### Step 4: Additional Features

#### 📋 Copy Game Information
- **Select any game** from the list
- **Click "Copy MediaID"** or **"Copy TitleID"** to copy to clipboard
- **Right-click** on any game for context menu options

#### 📄 Export Game Catalog
- **Click "Export HTML List"** to generate a complete game catalog
- **Choose save location** for the HTML file
- **Open in browser** to view your complete game inventory with search functionality
- **Perfect for inventory control** - keep track of all your Xbox 360 games in one organized catalog
- **Easy game management** - search, filter, and copy game information as needed

#### 💾 Prepare USB for Xbox 360
1. **Click "Prepare USB"** after downloading TUs
2. **Select the folder** where you downloaded the TUs
3. **Wait for USB structure creation** - automatically detects TU types and creates proper structure:

   **For Content TUs** (lowercase format like `tu00000005_00000000`):
   ```
   USB_Xbox360/
   └── Content/
       └── 0000000000000000/
           └── [TitleID]/
               └── 000B0000/
                   └── tu00000005_00000000
   ```

   **For Cache TUs** (uppercase format like `TU_16L61V6_0000014000000.00000000000O9`):
   ```
   USB_Xbox360/
   └── Cache/
       └── TU_16L61V6_0000014000000.00000000000O9
   ```

4. **Copy both "Content" and "Cache" folders** to the root of your USB drive
5. **Connect USB to Xbox 360** and install TUs from System Settings > Memory or use Aurora

---

## 🔧 Technical Details

### How It Works
1. **Game Detection**: Scans folders for `default.xex` files using XexTool
2. **ID Extraction**: Extracts MediaID and TitleID from XEX headers
3. **XboxUnity API**: Uses real endpoint `TitleUpdateInfo.php` discovered through web analysis
4. **Smart Filtering**: Only downloads TUs matching your exact MediaID to ensure compatibility
5. **Original Filenames**: Downloads TUs with their original names from XboxUnity servers
6. **Automatic TU Classification**: Detects TU type (Cache vs Content) based on filename format
7. **Organized Storage**: Creates game-named folders and proper Xbox 360 directory structure

### Supported Formats
- **Input**: Xbox 360 games with `default.xex` files
- **Output**: Original TU files with proper Xbox 360 naming conventions
  - **Cache TUs**: Uppercase format (e.g., `TU_16L61V6_0000014000000.00000000000O9`)
  - **Content TUs**: Lowercase format (e.g., `tu00000005_00000000`)
- **Export**: HTML game catalog for inventory control and collection management

### MediaID vs TitleID
- **MediaID**: Unique identifier for your specific game disc/version
- **TitleID**: Game identifier (same for all versions of a game)
- **Why MediaID matters**: Ensures TU compatibility with your exact game version

### TU Types and Installation
- **Cache TUs** (uppercase): Go directly in Xbox 360's `Cache/` folder
- **Content TUs** (lowercase): Go in `Content/0000000000000000/[TitleID]/000B0000/` structure
- **Automatic Detection**: Tool automatically determines correct placement based on filename format

---

## 🛠️ Troubleshooting

### Common Issues

**"XexTool.exe not found"**
- Ensure `XexTool.exe` is in the `xextool/` folder
- On Linux, make sure Wine is installed

**"Cannot connect to XboxUnity"**
- Check your internet connection
- Verify your API Key or login credentials
- XboxUnity might be temporarily down

**"No games detected"**
- Ensure each game folder contains a `default.xex` file
- Check that you selected the correct parent folder
- Verify XexTool can read the XEX files

**"No TUs found"**
- Not all games have Title Updates available
- Some games might not be in XboxUnity's database
- Check the logs for detailed information

### Getting XboxUnity API Key
1. **Register** at [XboxUnity.net](https://xboxunity.net)
2. **Go to your profile settings**
3. **Generate an API Key**
4. **Copy and paste** into X360 TU Manager

---

## 📁 Project Structure

```
X360 TU Manager/
├── main.py                 # Main GUI application
├── xboxunity_api.py        # XboxUnity API integration
├── xex_reader.py           # XEX file reading utilities
├── config.json             # User configuration (auto-generated)
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── xextool/                # XEX analysis tools
    └── XexTool.exe
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to:
- **Report bugs or issues** on [GitHub Issues](https://github.com/Wamphyre/X360-TU-Manager/issues)
- **Suggest new features** via feature requests
- **Submit pull requests** to improve the code
- **Improve documentation** and help others

### Development Setup
1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature
4. Make your changes and test thoroughly
5. Submit a pull request with a clear description

---

## ⚖️ Legal Notice

- This tool is for **personal use only**
- Respect XboxUnity's terms of service
- Only download TUs for games you legally own
- XexTool.exe is a third-party tool (credit to original authors)

---

## 🎮 Enjoy Your Updated Games!

X360 TU Manager makes it easy to keep your Xbox 360 games updated with the latest patches and improvements. Happy gaming! 🎯
