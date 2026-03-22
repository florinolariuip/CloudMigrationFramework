# 🔄 Restart Backend Server for PDF Feature

## Why Restart?
The PDF report generation endpoint was just added to `backend/app.py`. The backend server needs to be restarted to:
1. Load the new `/api/cmov4/generate-pdf` endpoint
2. Import the `reportlab` library (newly installed)
3. Load the `report_generator.py` module

## How to Restart

### Option 1: Using start.sh (Recommended)
```bash
cd /Users/florinolariu/Downloads/journalimplementationver2\ 3/frontend
bash start.sh
```

This script will:
- Stop any running backend/frontend servers
- Start the backend on port 5055
- Start the frontend on port 8080
- Open the browser automatically

### Option 2: Manual Restart
```bash
# Stop the backend
pkill -f "python.*app.py"

# Start the backend
cd /Users/florinolariu/Downloads/journalimplementationver2\ 3
python3 backend/app.py
```

Then in another terminal:
```bash
# Start the frontend
cd /Users/florinolariu/Downloads/journalimplementationver2\ 3/frontend
python3 -m http.server 8080
```

### Option 3: Check if Backend is Running
```bash
curl http://localhost:5055/health
```

If you get a response, the backend is running.

## After Restart

1. Open http://localhost:8080/cmov4.html
2. Run an optimization (any scenario)
3. Scroll down to the results
4. You should see the "📄 Download PDF Report" button
5. Click it to download the PDF

## Troubleshooting

### Error: "Failed to download PDF report"
- **Solution:** Restart the backend server using one of the options above

### Error: "No module named 'reportlab'"
- **Solution:** Install reportlab:
  ```bash
  pip3 install reportlab
  ```

### Error: "Connection refused"
- **Solution:** Backend is not running. Start it using Option 1 or 2 above

### Error: "500 Internal Server Error"
- **Check logs:** Look at the terminal where backend is running
- **Error details:** Check browser console (F12) for error message
- **Debug:** The error message should show what went wrong

## Verify Installation

Test PDF generation manually:
```bash
cd /Users/florinolariu/Downloads/journalimplementationver2\ 3/backend
python3 test_pdf_generation.py
```

Should output: "✅ Success! PDF report generated: test_cmov4_report.pdf"

---

**Status:** Ready to restart! 🚀
