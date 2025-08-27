# CSV Data Analyzer - Sales Overtime Report

A comprehensive Flask web application that processes online and offline transaction CSV files to generate detailed hourly sales aggregation reports with advanced comparison and discrepancy detection features.

## 🚀 Features

### **Core Functionality**
- **Flexible CSV Upload**: Upload any combination of online.csv, offline.csv, and report.csv files
- **Smart Data Filtering**:
  - **Online transactions**: Excludes "Pending Store Acceptance", "Cancelled", and "Pending Payment"
  - **Offline transactions**: Includes only "Sale" transactions where `Is_Cancelled = FALSE`
- **Hourly Aggregation**: Groups transactions by hour (0-23) and calculates totals
- **Report Comparison**: Compare calculated totals against report data with discrepancy detection

### **Advanced Features**
- **Difference Analysis**: Shows (Total - Report) calculations with color-coded indicators
- **Dynamic Hour Detection**: Automatically displays data for hours present in report files
- **Visual Discrepancy Highlighting**: Red/bold text for mismatched values
- **Flexible Upload Options**: Upload online-only, offline-only, or both files together
- **Modern Responsive UI**: Clean, professional interface with summary statistics

### **Data Visualization**
- **Summary Cards**: Quick overview of totals with visual indicators
- **Detailed Table**: Hour-by-hour breakdown with comparison data
- **Color Coding**:
  - 🟢 Green for positive differences (Total > Report)
  - 🔴 Red for negative differences (Total < Report)
  - ⚪ Gray for zero differences

## 📁 Project Structure

```
Report_data/
├── app.py                    # Main Flask application with processing logic
├── templates/
│   └── index.html           # Frontend template with modern UI
├── sample_data/             # Sample CSV files for testing
│   ├── online.csv
│   ├── offline.csv
│   └── report.csv
├── uploads/                 # Temporary file storage (auto-created)
├── requirements.txt         # Python dependencies
├── Procfile                # Railway deployment configuration
├── .gitignore              # Git ignore rules
├── test_*.py               # Test scripts for functionality verification
└── README.md               # This comprehensive documentation
```

## 📊 CSV File Requirements

### **Online CSV (online.csv) - Optional**
**Required Columns:**
- `Created Time`: Date/time in various formats:
  - "MM/DD/YYYY HH:MM" (e.g., "08/11/2025 15:53")
  - "YYYY-MM-DD HH:MM:SS"
  - "YYYY-MM-DD HH:MM"
- `Status`: Transaction status
- `Total`: Numeric value for aggregation

**Filtering Logic:**
- ✅ **Includes**: All statuses EXCEPT the excluded ones
- ❌ **Excludes**: "Pending Store Acceptance", "Cancelled", "Pending Payment"

### **Offline CSV (offline.csv) - Optional**
**Required Columns:**
- `Time`: Date/time in format "MM/DD/YYYY HH:MM" (e.g., "07/30/2025 11:03")
- `Transaction Type`: Type of transaction
- `Is_Cancelled`: Boolean value (TRUE/FALSE)
- `Total`: Numeric value for aggregation

**Filtering Logic:**
- ✅ **Includes**: `Transaction Type = "Sale"` AND `Is_Cancelled = FALSE`

### **Report CSV (report.csv) - Optional**
**Required Columns:**
- `Date / Time`: Hour format like "11 AM", "12 PM", "1 PM", "2 PM", etc.
- `Total Sales` (or similar): Numeric value for comparison

**Usage:**
- Used for comparison against calculated totals
- Automatically detects hours with data
- Enables discrepancy detection and highlighting

## 🛠️ Local Development

### **Prerequisites**
- Python 3.8 or higher
- pip package manager

### **Quick Setup**
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Report_data
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the application**:
   - Open your browser to `http://localhost:5000`
   - If port 5000 is in use: `PORT=5001 python app.py`

### **Testing with Sample Data**
1. Use the provided sample files in `sample_data/` folder
2. Upload any combination of files through the web interface
3. Verify the hourly aggregation and comparison results

### **Running Tests**
```bash
# Test basic functionality
python test_app.py

# Test enhanced features
python test_enhanced.py

# Test flexible upload
python test_flexible_upload.py

# Test difference calculations
python test_difference_column.py
```

## 🚀 Deployment Options

### **Option 1: Railway (Recommended)**

#### **GitHub Integration Method:**
1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial deployment"
   git branch -M main
   git remote add origin https://github.com/yourusername/csv-sales-analyzer.git
   git push -u origin main
   ```

2. **Deploy on Railway**:
   - Visit [Railway.app](https://railway.app)
   - Sign up/login with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway automatically detects Flask and deploys

#### **Railway CLI Method:**
1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Deploy**:
   ```bash
   railway login
   railway init
   railway up
   ```

### **Option 2: Other Platforms**
The application is compatible with:
- **Heroku**: Use the included Procfile
- **Vercel**: Add vercel.json configuration
- **DigitalOcean App Platform**: Direct deployment support
- **AWS Elastic Beanstalk**: ZIP deployment ready

## ⚙️ Configuration

### **Environment Variables**
```bash
PORT=5000                    # Server port (default: 5000)
FLASK_ENV=production        # Environment mode
MAX_CONTENT_LENGTH=16777216 # Max file size (16MB)
```

### **File Upload Settings**
- **Maximum file size**: 16MB per file
- **Supported formats**: .csv only
- **Concurrent uploads**: Up to 3 files (online, offline, report)
- **Auto-cleanup**: Files deleted after processing

## 🔧 API Reference

### **Endpoints**
- `GET /`: Display upload form and results
- `POST /`: Process uploaded CSV files and return aggregated data

### **Request Format**
```
POST /
Content-Type: multipart/form-data

Fields:
- online_csv: File (optional)
- offline_csv: File (optional)
- report_csv: File (optional)
```

### **Response Format**
HTML page with:
- Summary statistics cards
- Detailed hourly breakdown table
- Discrepancy highlighting
- Difference calculations

## 🛡️ Security Features

- **File Type Validation**: Only .csv files accepted
- **Secure Filename Handling**: Prevents directory traversal
- **Automatic File Cleanup**: Temporary files removed after processing
- **Input Sanitization**: All user inputs properly escaped
- **CSRF Protection**: Built-in Flask security features
- **File Size Limits**: Prevents large file attacks

## 📱 Browser Compatibility

- **Chrome**: 60+ ✅
- **Firefox**: 55+ ✅
- **Safari**: 12+ ✅
- **Edge**: 79+ ✅
- **Mobile browsers**: Responsive design supports mobile devices

## 🧪 Testing

### **Automated Tests**
Run the test suite to verify functionality:
```bash
python test_app.py           # Basic functionality
python test_enhanced.py      # Advanced features
python test_flexible_upload.py  # Upload combinations
python test_difference_column.py # Difference calculations
```

### **Manual Testing Scenarios**
1. **Upload online.csv only** → Verify online totals, offline shows $0.00
2. **Upload offline.csv only** → Verify offline totals, online shows $0.00
3. **Upload both files** → Verify combined totals
4. **Add report.csv** → Verify comparison and discrepancy detection
5. **Test with different time formats** → Verify parsing flexibility

## 🔍 Troubleshooting

### **Common Issues**

**Port 5000 already in use (macOS):**
```bash
# Solution 1: Use different port
PORT=5001 python app.py

# Solution 2: Disable AirPlay Receiver
# System Preferences → Sharing → Uncheck AirPlay Receiver
```

**CSV parsing errors:**
- Verify column names match requirements
- Check date/time format consistency
- Ensure numeric values in Total columns

**No data showing:**
- Check filtering criteria (Status values, Transaction Types)
- Verify date/time parsing with debug output
- Review server logs for processing details

### **Debug Mode**
Enable detailed logging:
```bash
FLASK_ENV=development python app.py
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with proper testing
4. **Commit changes**: `git commit -m 'Add amazing feature'`
5. **Push to branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### **Development Guidelines**
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation for changes
- Ensure backward compatibility

## 📄 License

This project is open source and available under the **MIT License**.

```
MIT License

Copyright (c) 2025 CSV Data Analyzer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 📞 Support

For questions, issues, or feature requests:
- **GitHub Issues**: [Create an issue](https://github.com/yourusername/csv-sales-analyzer/issues)
- **Documentation**: This README and inline code comments
- **Testing**: Use provided test scripts to verify functionality

---

**Built with ❤️ using Flask, Pandas, and modern web technologies.**
