# AI Data Analysis Platform

An intelligent data analysis platform powered by 
Google Gemini AI with 22 domain modules and 
international statistical standards.

## What It Does

Upload any dataset — the platform automatically:
- Detects which domain the data belongs to
- Applies international statistical standards
- Generates professional charts and visualizations  
- Produces AI-powered written analysis
- Exports complete text and Excel reports
- Delivers results via Telegram or web dashboard

## Supported Domains

| Domain | Standards |
|--------|-----------|
| Education | UNESCO / OECD / PISA |
| Healthcare | WHO / HIMSS |
| Finance | IFRS / CFA |
| Sales | Salesforce / HubSpot |
| HR | SHRM / ISO 30414 |
| Manufacturing | ISO 22400 / OEE |
| Logistics | CSCMP |
| Sports | Opta / FIFA |
| Marketing | Google / HubSpot |
| Real Estate | NAR / RICS |
| Retail | NRF |
| Energy | IEA / IRENA |
| Agriculture | FAO / USDA |
| Government | OECD / World Bank |
| Insurance | IAIS / Swiss Re |
| IT/DevOps | DORA / ITIL |
| Social Media | Sprout Social |
| Cybersecurity | NIST / ISO 27001 |
| E-Commerce | Shopify / Baymard |
| Supply Chain | SCOR / Gartner |
| Hospitality | STR |
| Telecommunications | ITU / GSMA |

## Technology Stack

- **AI**: Google Gemini 3.5 Flash with model fallback
- **Data**: Pandas, NumPy, SciPy
- **Charts**: Matplotlib, Seaborn
- **Dashboard**: Streamlit
- **Bot**: Python Telegram Bot
- **Reports**: Text + Excel (openpyxl)

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/Engr-umer-mohammed/ai-data-analysis-platform.git
cd ai-data-analysis-platform
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 4. Run terminal interface
```bash
python main.py
```

### 5. Run web dashboard
```bash
streamlit run dashboard.py
```

### 6. Run Telegram bot
```bash
python telegram_bot.py
```

## Project Structure

## Project Structure
ai-data-analysis-platform/
├─ data_agent.py              # Main orchestration
├── data_loader.py             # Universal file reader
├── statistical_analyzer.py    # Statistical engine
├── visualizer.py              # Chart generation
├── report_generator.py        # Report writing
├── dashboard.py               # Streamlit dashboard
├── main.py                    # Terminal interface
└── customization/
├── domain_registry.py     # Auto-routing
├── base_domain.py         # Base class
└── domains/               # 22 domain modules

## Developer

**Umer Mohammed**  
Senior Electrical Power Engineer | AI Systems Engineer  
LinkedIn: linkedin.com/in/engr-umer-mohammed  
Email: umermohammed62@gmail.com

## License

MIT License — free to use and modify