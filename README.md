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

## Usage

### One-time Organization
```bash
python scripts/organize.py
```
Enter Folder path

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
