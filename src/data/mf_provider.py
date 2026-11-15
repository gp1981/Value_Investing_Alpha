import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from src.utils.auth_handler import get_credentials

class MagicFormulaProvider:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.magicformulainvesting.com"
        self.login_url = f"{self.base_url}/Account/LogOn"
        self.screen_url = f"{self.base_url}/Screening/StockScreening"
        
    def login(self):
        username, password = get_credentials("MF")
        if not username or not password:
            raise ValueError("Credentials not found")
        
        # Get login form tokens
        res = self.session.get(self.login_url)
        soup = BeautifulSoup(res.text, 'html.parser')
        form = soup.find('form')
        
        # Prepare form data
        data = {
            "Email": username,
            "Password": password
        }
        # Include hidden request verification token if present
        token = soup.find('input', {'name': '__RequestVerificationToken'})
        if token:
            data['__RequestVerificationToken'] = token['value']
            
        self.session.post(self.login_url, data=data)
        
        # Verify login
        res = self.session.get(self.screen_url)
        if "StockScreening" not in res.url:
            raise Exception("Login failed")
        print("Login successful")

    def fetch_screen(self, market_cap, select30=True):
        res = self.session.get(self.screen_url)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        data = {
            "Select30": "true" if select30 else "false",
            "MinimumMarketCap": market_cap,
            "__RequestVerificationToken": soup.find('input', {'name': '__RequestVerificationToken'})['value']
        }
        
        res = self.session.post(self.screen_url, data=data)
        return self._parse_table(res.text, market_cap, "Top30" if select30 else "Top50")

    def _parse_table(self, html, market_cap, label):
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {'class': 'screeningdata'})
        if not table:
            return pd.DataFrame()
            
        rows = table.find('tbody').find_all('tr')
        data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 5: continue
            data.append({
                "Company_Name": cols[0].text.strip(),
                "Ticker": cols[1].text.strip(),
                "Market_Cap_Millions": cols[2].text.strip().replace(',', ''),
                "Price_From": cols[3].text.strip(),
                "Most_Recent_Quarter_Data": cols[4].text.strip(),
                "threshold_marketCap": market_cap,
                "TopGreenblatt": label
            })
        return pd.DataFrame(data)

    def run(self, thresholds=list(range(100, 2000, 100))):
        self.login()
        all_data = []
        for cap in thresholds:
            print(f"Processing market cap: {cap}")
            top30 = self.fetch_screen(cap, select30=True)
            top50 = self.fetch_screen(cap, select30=False)
            # Combine current threshold data; keep duplicates if they appear in different thresholds
            df = pd.concat([top30, top50])
            all_data.append(df)
            time.sleep(0.5)
        
        return pd.concat(all_data)

if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--thresholds", type=int, nargs="+", default=list(range(100, 2000, 100)))
    args = parser.parse_args()
    
    provider = MagicFormulaProvider()
    df = provider.run(thresholds=args.thresholds)
    output_path = os.path.join("output", "benchmark_mf.csv")
    df.to_csv(output_path, index=False)
    print(f"Benchmark data updated and saved to {output_path}")
