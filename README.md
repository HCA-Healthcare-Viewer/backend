# UAInnovate25 Backend

This backend service handles the parsing, processing, and deidentification of HL7 healthcare messages. It ensures patient privacy by securely removing and replacing protected health information (PHI).

## Features

- **HL7 Parsing:** Efficiently parse HL7 messages into structured JSON.
- **Deidentification:** Replace PHI with consistent, anonymized values.
- **Message Cleaning:** Remove redundant and null fields to streamline data.
- **Datetime Adjustment:** Standardize and adjust datetime fields for consistency.

## Getting Started

### Prerequisites

- Python 3.11+
- `pip`

### Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/UAInnovate25/backend.git
cd backend
pip install -r requirements.txt
```

### Usage

To parse and deidentify HL7 messages, use:

```bash
python app/src/parsing.py
```

Deidentified data will be output to:

- `app/data/messages_deidentified.txt` (HL7 formatted)
- `app/data/messages_deidentified.json` (JSON formatted)


