# Linux Whisperer

An open-source voice dictation and command tool for Linux, inspired by Wispr Flow.

## Features (Planned)

- Real-time speech-to-text transcription using OpenAI's Whisper
- Voice commands for system control
- Application-aware context for improved accuracy
- Whispering mode for quiet environments
- Support for multiple languages
- System tray integration
- Customizable commands and shortcuts

## Installation

### Prerequisites

- Python 3.8 or higher
- FFmpeg
- PortAudio (for PyAudio)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/linux-whisperer.git
cd linux-whisperer

# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### System Dependencies

On Ubuntu/Debian:

```bash
sudo apt update && sudo apt install ffmpeg portaudio19-dev python3-dev
```

On Arch Linux:

```bash
sudo pacman -S ffmpeg portaudio
```

On Fedora:

```bash
sudo dnf install ffmpeg portaudio-devel
```

## Usage

```bash
# Run the application
python src/main.py
```

## Development

```bash
# Run tests
python -m pytest
```

## NixOS

Under `/shells` there's `flake.nix` file with all environment prepared. (might need to adjust the base dir)

```bash
cd /shells
nix develop
```

## License

MIT

## Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) for the speech recognition engine
