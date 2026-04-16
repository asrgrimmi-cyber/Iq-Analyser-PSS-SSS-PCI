# 📡 LTE IQ Analyzer — PSS/SSS/PCI Engine

A high-performance LTE signal analysis dashboard. This tool allows users to upload raw IQ data (`.bin` files), perform resampling, and extract critical LTE cell parameters including **PSS (Primary Synchronization Signal)**, **SSS (Secondary Synchronization Signal)**, and **PCI (Physical Cell ID)**.

The interface is built with a premium, **Spotify-inspired dark theme** for a modern analysis experience.

---

## 🚀 What We Can Do with This
- **LTE Cell Search**: Automatically detect PSS and SSS in raw IQ samples.
- **PCI Detection**: Instantly identify the Physical Cell ID (0-503).
- **Signal Analysis**:
    - **Frequency Spectrum**: View the signal in the frequency domain.
    - **Resource Grid**: Visualize LTE resource blocks.
    - **Equalization**: View constellations before and after 1-tap equalization.
    - **RSRP Calculation**: Measure Reference Signal Received Power.
- **C++ Acceleration**: Uses a custom-built C++ engine for 100x faster FFT and correlation processing compared to pure Python.

---

## 🛠️ How to Run the Code

### Prerequisites
1.  **Python 3.8+**: Ensure Python is installed and added to your PATH.
2.  **C++ Build Tools (Optional)**: For maximum speed, install **CMake** and **Visual Studio** (Windows) or **GCC** (Linux/Mac).

### Quick Start (Windows)
Simply double-click the included automation script:
```bash
start.bat
```
This script will:
- Check for Python.
- Install all required libraries from `req.txt`.
- Attempt to build the C++ engine.
- Launch the web dashboard at `http://localhost:5000`.

### Manual Setup (All Platforms)
1.  **Install Dependencies**:
    ```bash
    pip install -r req.txt
    ```
2.  **Run the Server**:
    ```bash
    python app.py
    ```
3.  **Access the Dashboard**: Open your browser and go to `http://localhost:5000`.

---

## 📖 How to Use
1.  **Upload**: Click the "Upload IQ Data" button and select your `.bin` file.
2.  **Process**: The engine will resample the data and search for synchronization signals.
3.  **Analyze**: Review the generated plots (Spectrum, Resource Grid, Constellations) in the scrollable dashboard.
4.  **Download**: (Optional) View the raw PCI and RSRP values in the results header.

---

## 📤 How to Upload/Push to GitHub (Steps)

If you want to push updates to your GitHub repository, follow these standard steps:

### Step 1: Initialize Git (If not already done)
```bash
git init
```

### Step 2: Add Files
```bash
git add .
```

### Step 3: Commit Changes
```bash
git commit -m "Update project: Added README and optimized engine"
```

### Step 4: Link to GitHub (If not already linked)
```bash
git remote add origin https://github.com/asrgrimmi-cyber/Iq-Analyser-PSS-SSS-PCI.git
```

### Step 5: Push to GitHub
```bash
git push -u origin main
```

*(Note: If you are updating an existing repo, you only need to run Step 2, 3, and 5.)*

---

## 📁 Project Structure
- `app.py`: Flask web server & API.
- `iq_engine.py`: Main processing logic and PSS/SSS correlation.
- `cpp/`: Source code for the high-performance C++ engine.
- `static/`: Frontend assets (CSS, JS, and generated plots).
- `templates/`: HTML interface.
- `start.bat`: One-click setup and launch script.
