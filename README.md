# Smart File Organizer

Intelligent file organization system using offline AI classification with MediaPipe, TensorFlow Lite, and sentence-transformers.

## Features

- 🤖 Offline AI Classification - 100% privacy-preserving
- 📁 Smart Organization - Auto-categorizes files into folders
- 👀 Real-time Monitoring - Watch folders for new files
- 🔍 Fast Search - SQLite-based file indexing
- 🎯 Multi-format Support - Images, videos, documents, audio, code

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/smart-file-organizer.git
cd smart-file-organizer
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download AI models:
```bash
# Create models directory
mkdir -p models

# Download MediaPipe EfficientNet-Lite0 model
wget https://storage.googleapis.com/mediapipe-models/image_classifier/efficientnet_lite0/float32/1/efficientnet_lite0.tflite -P models/
```

## Configuration

Edit `config.yaml` to customize:

```
watch_directory: "/home/ruthvik/Downloads"
organized_directory: "/home/ruthvik/Documents/Organized"
use_ai: true
confidence_threshold: 0.5
```

## Usage

### One-time Organization
```bash
python scripts/organize.py
```

### Auto-watch Mode
```bash
python scripts/watch.py
```

### Search Files
```bash
python scripts/search.py "invoice"
```

## Project Structure

```
Documents/
  ├── invoice/
  ├── resume/
  └── report/
Images/
  ├── cat/
  ├── dog/
  └── landscape/
Videos/
Audio/
Code/
```

## License

MIT License
