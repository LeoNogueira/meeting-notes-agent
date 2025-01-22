# Meeting Notes Action Extractor

A Python application that extracts action items from meeting notes in markdown files and posts them to Slack channels.

## Features

- Extracts actions and todos from markdown meeting notes
- Identifies owners, due dates, and status
- Posts formatted action items to Slack
- Configurable input/output paths
- Detailed logging

## Components

### Action Extractor
- Processes markdown files using LangChain
- Extracts structured action items
- Outputs to JSON format

### Slack Notifier
- Reads actions from JSON file
- Posts formatted messages to Slack
- Supports markdown formatting

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt