ExpiryWise
ExpiryWise is a Python web application that helps users avoid food and
product wastage. It records items with their expiry dates, reads label
text from product images using OCR, reminds the user before items
expire, and suggests recipes that use items close to expiry.
Project status: Phase 2 complete (about 70% of the project).
Features
Store product details and expiry dates in a database
Scan product images and extract text with OCR (`ocr.py`)
Reminders for items that are expired or close to expiry (`reminders.py`)
Recommendations on which items to use first (`recommendation.py`)
Recipe suggestions based on items nearing expiry (`recipes.py`)
Barcode validation: an invalid barcode is discarded (set to `None`)
Web pages for the home view and the scanner (`templates/`)
Automated tests with pytest and GitHub Actions
Project structure
```
Expirywise/
|-- app.py                 Main application and routes
|-- ocr.py                 OCR text extraction
|-- reminders.py           Expiry reminder logic
|-- recommendation.py      Use-first recommendations
|-- recipes.py             Recipe suggestions
|-- templates/             HTML pages (index.html, scanner.html)
|-- tests/
|   `-- test_expirywise.py Automated tests
|-- .github/workflows/
|   `-- tests.yml          CI pipeline
|-- requirements.txt       Python dependencies
|-- .gitignore
`-- README.md
```
Installation
Clone the repository:
```
   git clone https://github.com/prasanthika2008-lgtm/ExpiryWise.git
   cd ExpiryWise
   ```
Create and activate a virtual environment (Windows PowerShell):
```
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
Install the dependencies:
```
   pip install -r requirements.txt
   ```
Run the application
```
python app.py
```
Then open the address shown in the terminal in your browser.
Run the tests
```
pytest -v
```
Latest verified result before the final Phase 2 fixes:
27 passed, 1 skipped, 0 failed.
Screenshots
Add your screenshots here, for example:
```
![Home page](screenshots/home.png)
![Scanner page](screenshots/scanner.png)
```
Remaining work (Phase 3)
Improve OCR accuracy for different date formats
Improve the user interface and expiry colour indicators
Add reminder delivery (email or notifications)
Add more tests
Final deployment
Author
Prasanthika M, B.E. Computer Science and Engineering (II Year)