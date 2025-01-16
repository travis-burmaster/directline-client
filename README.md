# Direct Line API Integration

This project provides a secure and efficient integration with Microsoft's Direct Line API, featuring a robust client implementation and agent-based interaction capabilities.

## Prerequisites

- Python 3.8+
- Git
- Access to Direct Line API
- Hugging Face API access
- Valid Azure AD configuration

## Environment Setup

1. Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the following variables:
```env
DIRECT_LINE_SECRET=your_direct_line_secret
HUGGINGFACE_API_TOKEN=your_huggingface_token
BotIdentifier=your_bot_id
USER_TOKEN=your_user_token
```

## Project Structure

```
.
├── README.md
├── requirements.txt
├── .gitignore
├── .env
└── src/
    └── directline_client.py
```

## Usage

1. Ensure your virtual environment is activated
2. Configure your environment variables
3. Run the main script:

```bash
python src/directline_client.py
```

## Security Considerations

- Keep your `.env` file secure and never commit it to version control
- Regularly rotate your API tokens
- Monitor API usage for unusual patterns
- Implement rate limiting in production environments

## Development

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License