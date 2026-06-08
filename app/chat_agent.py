import json
import re
from urllib import request
from insightops.config import AppSettings, load_app_settings


class ChatAgentCodeGenerator:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings or load_app_settings()

    def generate_code(self, prompt: str, df_columns: list[str]) -> str:
        """Generates Python code based on prompt and DataFrame columns."""
        # Check if OpenRouter is configured
        if self.settings.openrouter_api_key:
            try:
                return self._generate_with_openrouter(prompt, df_columns)
            except Exception as e:
                # Fallback to local template generator on LLM failure
                print(f"OpenRouter code gen failed, falling back: {e}")

        return self._generate_deterministic_template(prompt, df_columns)

    def _generate_with_openrouter(self, prompt: str, df_columns: list[str]) -> str:
        cols_str = ", ".join(df_columns)
        system_instruction = (
            "You are an elite data scientist and Python coder inside a Jupyter sandbox. "
            f"There is a pandas DataFrame already loaded in memory named `df` with columns: [{cols_str}]. "
            "Write the clean Python code to answer the user's prompt. "
            "Do NOT include explanation text, only write code. "
            "Wrap your output in standard ```python ... ``` blocks. "
            "If the user wants a chart, use `matplotlib.pyplot` or `pandas.plot` to draw it. "
            "Do NOT call `plt.show()`, the sandbox will automatically capture and save active figures."
        )

        payload = {
            "model": self.settings.openrouter_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1000,
        }

        api_request = request.Request(
            f"{self.settings.openrouter_base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with request.urlopen(api_request, timeout=25) as response:
            response_body = response.read().decode("utf-8")

        parsed = json.loads(response_body)
        content = parsed["choices"][0]["message"]["content"]

        # Extract code from python blocks
        match = re.search(r"```python\s*(.*?)\s*```", content, re.DOTALL)
        if match:
            return match.group(1).strip()

        return content.strip()

    def _generate_deterministic_template(
        self, prompt: str, df_columns: list[str]
    ) -> str:
        """Deterministic keyword parser creating Python templates."""
        q = prompt.lower()

        # Resolve best columns
        rev_col = (
            "revenue"
            if "revenue" in df_columns
            else ("net_revenue" if "net_revenue" in df_columns else None)
        )
        date_col = "order_date" if "order_date" in df_columns else None

        # Template 1: Data Cleaning & Imputation
        if "clean" in q or "missing" in q or "impute" in q or "duplicate" in q:
            return """# Data Cleaning and Imputation Pipeline
print("--- Initial Integrity Profile ---")
print("Duplicate rows:", df.duplicated().sum())
print("Missing values per column:\\n", df.isna().sum())

# Drop duplicate rows
df = df.drop_duplicates()

# Impute missing numeric columns with their mean averages
for col in df.select_dtypes(include=['number']).columns:
    if df[col].isna().sum() > 0:
         df[col] = df[col].fillna(df[col].mean())

print("\\n--- Post-Cleaning Profile ---")
print("Remaining duplicates:", df.duplicated().sum())
print("Remaining missing values:\\n", df.isna().sum())
"""

        # Template 2: Descriptive & Hypothesis Testing (SciPy stats)
        if "test" in q or "hypothesis" in q or "t-test" in q or "anova" in q:
            col = rev_col or df_columns[-1]
            return f"""# SciPy Hypothesis Validation (T-Test)
import scipy.stats as stats

col_to_test = "{col}"
# 1-Sample T-test evaluating if mean value equals $2,000
t_stat, p_val = stats.ttest_1samp(df[col_to_test].dropna(), popmean=2000.0)

print(f"--- 1-Sample T-Test on '{{col_to_test}}' ---")
print(f"Population Mean Null Hypothesis: $2,000.00")
print(f"Sample Mean:                     ${{df[col_to_test].mean():.2f}}")
print(f"T-Statistic:                    {{t_stat:.4f}}")
print(f"P-Value:                        {{p_val:.6f}}")
print("Significance (alpha = 0.05):    ", "Reject Null (Significant)" if p_val < 0.05 else "Fail to Reject (Not Significant)")
"""

        # Template 3: Correlation Matrix
        if "correlation" in q or "corr" in q or "matrix" in q:
            return """# Correlation Matrix Summary
print("--- Pearson Product-Moment Correlation Matrix ---")
numeric_df = df.select_dtypes(include=['number'])
print(numeric_df.corr())
"""

        # Template 4: Predictive Regression Modeling (Scikit-Learn)
        if "model" in q or "regression" in q or "predict" in q or "fit" in q:
            col = rev_col or df_columns[-1]
            return f"""# Scikit-Learn Predictive Regression Modeling
from sklearn.linear_model import LinearRegression
import numpy as np

# Predict Net Revenue based on Quantity sold
X = df[['quantity']].dropna()
y = df.loc[X.index, '{col}']

model = LinearRegression()
model.fit(X, y)

print("--- Scikit-Learn Linear Regression Model (y = Revenue, x = Quantity) ---")
print(f"Intercept (Beta 0): {{model.intercept_:.2f}}")
print(f"Coefficient (Beta 1): {{model.coef_[0]:.2f}}")
print(f"R-squared Score:     {{model.score(X, y):.4f}}")
"""

        # Template 5: Outliers and Anomalies
        if "anomaly" in q or "anomalies" in q or "outlier" in q or "risk" in q:
            col = rev_col or df_columns[-1]
            return f"""# Statistical Outlier Detection
import numpy as np

col_to_check = "{col}"
print(f"--- Outlier Detection on '{{col_to_check}}' ---")
q1 = df[col_to_check].quantile(0.25)
q3 = df[col_to_check].quantile(0.75)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

outliers = df[(df[col_to_check] < lower_bound) | (df[col_to_check] > upper_bound)]
print(f"IQR Bounds: {{lower_bound:.2f}} to {{upper_bound:.2f}}")
print(f"Detected {{len(outliers)}} outliers:")
print(outliers.head(10))
"""

        # Template 6: Explicit Pie Chart Requests (prevent keyword collision)
        if "pie" in q:
            col = rev_col or df_columns[-1]
            group_col = (
                "region"
                if "region" in q
                else (
                    "product"
                    if "product" in q
                    else ("region" if "region" in df_columns else df_columns[0])
                )
            )
            return f"""# {group_col.capitalize()} Distribution Pie Chart
import matplotlib.pyplot as plt

grouped = df.groupby('{group_col}')['{col}'].sum().sort_values(ascending=False).head(5)
plt.figure(figsize=(6, 6))
grouped.plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=['#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'])
plt.title("Revenue Distribution by {group_col.capitalize()}", fontsize=12, fontweight='bold')
plt.ylabel("")
plt.tight_layout()
"""

        # Template 7: Explicit Bar Chart Requests (prevent keyword collision)
        if "bar" in q:
            col = rev_col or df_columns[-1]
            group_col = (
                "region"
                if "region" in q
                else (
                    "product"
                    if "product" in q
                    else ("region" if "region" in df_columns else df_columns[0])
                )
            )
            return f"""# {group_col.capitalize()} Total Bar Chart
import matplotlib.pyplot as plt

grouped = df.groupby('{group_col}')['{col}'].sum().sort_values(ascending=False)
plt.figure(figsize=(8, 4.5))
colors = ['#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
grouped.plot(kind='bar', color=colors[:len(grouped)])
plt.title("Total {col} by {group_col.capitalize()}", fontsize=12, fontweight='bold')
plt.xlabel("{group_col.capitalize()}", fontsize=10)
plt.ylabel("Revenue ($)" if "rev" in col or "sales" in col else "{col}", fontsize=10)
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.3)
plt.tight_layout()
"""

        # Template 8: Region Charts Default (Implicit Bar)
        if "region" in q:
            col = rev_col or df_columns[-1]
            return f"""# Revenue by Region Bar Chart
import matplotlib.pyplot as plt

grouped = df.groupby('region')['{col}'].sum().sort_values(ascending=False)
plt.figure(figsize=(8, 4.5))
colors = ['#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
grouped.plot(kind='bar', color=colors[:len(grouped)])
plt.title("Total Revenue by Region", fontsize=12, fontweight='bold')
plt.xlabel("Region", fontsize=10)
plt.ylabel("Revenue ($)", fontsize=10)
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.3)
plt.tight_layout()
"""

        # Template 9: Product Charts Default (Implicit Pie)
        if "product" in q:
            col = rev_col or df_columns[-1]
            return f"""# Sales by Product Pie Chart
import matplotlib.pyplot as plt

grouped = df.groupby('product')['{col}'].sum().sort_values(ascending=False).head(5)
plt.figure(figsize=(6, 6))
grouped.plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=['#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'])
plt.title("Top 5 Revenue Generating Products", fontsize=12, fontweight='bold')
plt.ylabel("")
plt.tight_layout()
"""

        # Template 8: Trends and Time Series
        if "trend" in q or "forecast" in q or "monthly" in q or "time" in q:
            col = rev_col or df_columns[-1]
            d_col = date_col or "order_date"
            return f"""# Monthly Net Revenue Trends
import matplotlib.pyplot as plt
import pandas as pd

df['temp_date'] = pd.to_datetime(df['{d_col}'])
monthly = df.groupby(df['temp_date'].dt.to_period('M'))['{col}'].sum()
monthly.index = monthly.index.to_timestamp()

plt.figure(figsize=(9, 4.5))
plt.plot(monthly.index, monthly.values, marker='o', color='#6366f1', linewidth=2.5)
plt.title("Net Sales Revenue Monthly Trend", fontsize=12, fontweight='bold')
plt.ylabel("Revenue ($)", fontsize=10)
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
"""

        # Template 9: Default overview
        return """# Sales Dataset Overview
import pandas as pd
print("--- Sales Dataset Overview ---")
print(f"Total Records: {len(df)}")
print(df.describe())
"""
