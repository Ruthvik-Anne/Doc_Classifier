from setuptools import setup, find_packages

setup(
    name="smart-file-organizer",
    version="1.0.0",
    description="Intelligent file organization using offline AI",
    packages=find_packages(),
    install_requires=[
        "mediapipe",
        "sentence-transformers",
        "openai-whisper",
        "python-magic",
        "pymupdf",
        "python-docx",
        "watchdog",
        "pyyaml",
        "click",
        "tqdm",
        "tabulate",
        "opencv-python",
        "Pillow",
        "scikit-learn",
        "torch",
        "torchvision",
        "torchaudio",
    ],
    entry_points={
        'console_scripts': [
            'smart-organize=scripts.organize:main',
            'smart-watch=scripts.watch:main',
            'smart-search=scripts.search:main',
        ],
    },
    python_requires='>=3.8',
)
