# EwayAuto - E-way Bill Automation System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40+-purple.svg)](https://playwright.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, web-based automation system for E-way Bill management using Playwright, FastAPI, and a responsive Bootstrap UI. This application provides automated and semi-automated solutions for extending E-way Bills on the GST portal while maintaining legal compliance.

## 🚀 Features

### Core Functionality
- **Web-Based Dashboard**: Modern, responsive UI with real-time status updates
- **Multi-Mode Operations**: Single bill, CSV bulk processing, and auto-extension capabilities
- **Legal Compliance**: Manual CAPTCHA solving, no automated login credentials storage
- **Session Management**: Persistent browser sessions with automatic timeout handling
- **Real-Time Progress**: WebSocket-based progress updates for long operations

### Extension Modes
1. **Single Extension**: Process individual E-way Bills with manual verification
2. **CSV Bulk Processing**: Upload CSV files for batch processing with detailed reporting
3. **Auto-Extension**: Intelligent extension with configurable rules and filters

### Technical Features
- **Playwright Integration**: Cross-browser automation with Chrome, Firefox, Safari support
- **Async FastAPI Backend**: High-performance API with SQLite database
- **Smart Browser Control**: Headless/headful modes based on debug settings
- **Comprehensive Logging**: Detailed operation logs with error tracking
- **Template System**: Pre-configured CSV templates for easy data entry

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended for bulk operations)
- 1GB disk space
- Internet connection

### Browser Requirements
- Chromium/Chrome (recommended)
- Firefox
- Safari (macOS only)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ewayauto.git
cd ewayauto
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers
```bash
playwright install
```

### 5. Configuration (Optional)
Create a `.env` file in the root directory:
```env
# Application Settings
DEBUG=true
HOST=127.0.0.1
PORT=8000

# Browser Settings
BROWSER_TYPE=chromium
HEADLESS=false
SLOW_MO=100

# Session Settings
SESSION_TIMEOUT_HOURS=8
AUTO_REFRESH_SESSION=true

# Logging
LOG_LEVEL=INFO
```

## 🚀 Quick Start

### 1. Start the Application
```bash
python main.py
```

### 2. Open Web Interface
Navigate to `http://localhost:8000` in your web browser.

### 3. Login Process
1. Click the "Login" button in the navigation bar
2. The system will open a browser window to the E-way Bill portal
3. Manually enter your credentials and solve any CAPTCHAs
4. The system will detect successful login and proceed

### 4. Choose Operation Mode
- **Single Extension**: Use for individual E-way Bills
- **CSV Upload**: Bulk process multiple bills from CSV file
- **Auto Extension**: Automated processing with smart filters

## 📖 User Guide

### Single E-way Bill Extension

1. Click on the "Single Extension" card
2. Enter the E-way Bill number
3. Select extension reason and additional kilometers
4. Click "Start Extension"
5. Monitor progress in real-time

### CSV Bulk Processing

1. Download the CSV template from the "CSV Template" button
2. Fill in your E-way Bill data
3. Upload the completed CSV file
4. Review the data preview
5. Click "Start Batch Processing"

#### CSV Format
```csv
ewb_number,extension_reason,additional_km
123456789012,Natural Calamity,50
123456789013,Law and Order,25
```

### Auto Extension Mode

1. Configure extension rules (minimum days before expiry, maximum extensions, etc.)
2. Set up filters for automatic processing
3. Enable auto-extension mode
4. The system will process eligible bills automatically

## 🔧 API Documentation

### Authentication Endpoints

#### POST `/api/auth/trigger-login`
Triggers the manual login process.
```json
{
  "success": true,
  "message": "Login process initiated"
}
```

#### GET `/api/auth/status`
Checks current authentication status.
```json
{
  "success": true,
  "logged_in": true,
  "session_valid": true,
  "expires_at": "2024-01-20T15:30:00Z"
}
```

#### POST `/api/auth/logout`
Logs out and clears session.

### Extension Endpoints

#### POST `/api/extensions/single`
Process a single E-way Bill extension.
```json
{
  "ewb_number": "123456789012",
  "extension_reason": "Natural Calamity",
  "additional_km": 50
}
```

#### POST `/api/extensions/csv`
Upload CSV file for bulk processing.
- Content-Type: `multipart/form-data`
- Form field: `file`

#### GET `/api/extensions/history`
Retrieve processing history with pagination.

#### GET `/api/extensions/templates/csv`
Download CSV template file.

### Dashboard Endpoints

#### GET `/api/dashboard/stats`
Get dashboard statistics.
```json
{
  "total_eway_bills": 150,
  "pending_extensions": 5,
  "successful_extensions": 140,
  "failed_extensions": 5
}
```

#### GET `/api/dashboard/health`
System health check.

## 🏗️ Architecture

### Project Structure
```
ewayauto/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── app/
│   ├── api/               # API routes and endpoints
│   │   └── routes/        # Route modules
│   │       ├── auth.py    # Authentication routes
│   │       ├── automation.py  # Automation control
│   │       ├── dashboard.py   # Dashboard data
│   │       └── extensions.py  # Extension operations
│   ├── automation/        # Core automation logic
│   │   └── eway_automation.py  # Playwright automation
│   ├── core/             # Core configuration and utilities
│   │   ├── config.py     # Application settings
│   │   ├── credentials.py # Credential management
│   │   └── logging.py    # Logging configuration
│   ├── models/           # Data models and database
│   │   ├── database.py   # Database configuration
│   │   └── schemas.py    # Pydantic models
│   ├── static/           # Static web assets
│   │   ├── css/         # Stylesheets
│   │   ├── js/          # JavaScript files
│   │   └── screenshots/ # Operation screenshots
│   └── templates/        # HTML templates
│       └── components/   # Reusable components
├── data/                 # Application data
│   └── ewayauto.db      # SQLite database
└── logs/                 # Application logs
```

### Technology Stack

#### Backend
- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **Playwright**: Browser automation
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

#### Frontend
- **Bootstrap 5**: Responsive CSS framework
- **jQuery**: JavaScript library
- **WebSockets**: Real-time communication
- **Jinja2**: Template engine

#### Database
- **SQLite**: Lightweight database for local storage
- **Async SQLAlchemy**: Asynchronous database operations

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `HOST` | `127.0.0.1` | Server host |
| `PORT` | `8000` | Server port |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/ewayauto.db` | Database connection |
| `BROWSER_TYPE` | `chromium` | Browser for automation |
| `HEADLESS` | `true` | Browser headless mode |
| `SESSION_TIMEOUT_HOURS` | `8` | Session timeout |
| `LOG_LEVEL` | `INFO` | Logging level |

### Legal Compliance Settings

The application enforces legal compliance through these permanently disabled features:
- `auto_login: false` - No automated login
- `save_credentials_on_success: false` - No credential storage
- `automated_form_filling: false` - Manual form completion required
- `legal_compliance_mode: true` - Compliance mode enforced

## 🔍 Troubleshooting

### Common Issues

#### Browser Not Opening
- Ensure Playwright browsers are installed: `playwright install`
- Check if the selected browser is available on your system
- Try switching browser type in configuration

#### Login Issues
- Verify your GST portal credentials are correct
- Check if your account has E-way Bill permissions
- Ensure CAPTCHA is solved correctly
- Clear browser data and try again

#### CSV Processing Failures
- Verify CSV format matches the template
- Check for invalid E-way Bill numbers
- Ensure all required columns are present
- Review error logs for specific issues

#### Session Timeouts
- Default session timeout is 8 hours
- Sessions automatically refresh if `AUTO_REFRESH_SESSION` is enabled
- Manual re-login required after extended inactivity

### Log Files

Application logs are stored in the `logs/` directory:
- `ewayauto.log`: General application logs
- `errors.log`: Error-specific logs

### Debug Mode

Enable debug mode for detailed logging:
1. Set `DEBUG=true` in `.env` file
2. Restart the application
3. Check logs for detailed information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
pytest
```

3. Format code:
```bash
black app/
isort app/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Legal Disclaimer

This software is provided for educational and automation purposes. Users are responsible for:
- Ensuring compliance with GST portal terms of service
- Manually verifying all automated actions
- Maintaining data security and privacy
- Following all applicable laws and regulations

The developers are not responsible for any misuse of this software or any consequences arising from its use.

## 🆘 Support

For support, please:
1. Check the troubleshooting section above
2. Review the logs for error details
3. Open an issue on GitHub with:
   - System information
   - Steps to reproduce
   - Error logs
   - Screenshots (if applicable)

## 📊 Changelog

### Version 2.0.0 (Current)
- Complete UI overhaul with Bootstrap 5
- Navbar-based authentication
- Real-time progress tracking
- Enhanced error handling
- Legal compliance improvements

### Version 1.0.0
- Initial release
- Basic automation functionality
- Command-line interface

## 🔮 Roadmap

- [ ] Multi-user support
- [ ] Advanced reporting and analytics
- [ ] Mobile-responsive improvements
- [ ] API rate limiting
- [ ] Automated backup system
- [ ] Integration with external ERP systems

## ⚖️ Legal & Compliance

**🚨 IMPORTANT: Read before using this software**

- **[Terms of Service](TERMS_OF_SERVICE.md)** - Complete legal disclaimers and user responsibilities
- **[Legal Notice](LEGAL_NOTICE.md)** - Compliance requirements and warnings
- **[License](LICENSE)** - MIT License for code usage

**By using this software, you accept all terms and take full responsibility for legal compliance.**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Disclaimer**: The MIT License applies to the code only. Users are solely responsible for compliance with all applicable laws and regulations when using this software.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

**Contributors must agree to the terms of service and ensure all contributions are legal and ethical.**

## 📞 Support

- **Technical Issues**: Open an issue on GitHub
- **Legal Questions**: Consult with your legal team
- **Security Reports**: Follow responsible disclosure practices

---

**Made with ❤️ for the GST community | USE AT YOUR OWN RISK**