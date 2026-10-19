# MAMAEARTH GROWTH AND RETURN PIPELINE

### 

#### PROJECT OVERVIEW

The Mamaearth Returns \& Growth Intelligence Pipeline is a data analytics project designed to investigate order returns, revenue trends, payment-method performance, and data quality in an e-commerce dataset. It is an end-to-end workflow that follows cleaning raw data and statistical analysis along with generating AI powered insights and recommendations.The goal is to transform raw order data into actionable insights that can help an e-commerce business understand return patterns, improve the reliability of revenue reporting, and identify opportunities for operational improvement.



#### Business Objectives



* Analyze order returns and calculate the overall return rate.



* Compare return rates across payment methods and city tiers.



* Identify duplicate records, missing values, and potential data-quality issues.



* Examine monthly revenue trends.



* Investigate the relationship between discounts and order returns.



* Generate a structured business narrative using the Situation–Complication–Resolution (SCR) framework.





#### TOOLS AND TECHNOLOGIES USED

1. SQL / MySQL: Database concepts, data querying, and business reporting.

2. Python: Data processing and analytical workflows.

3. Pandas: Data cleaning and exploratory data analysis.

4. SQLite: Local database storage and querying.

5. Matplotlib: Data visualization.

6. Generative AI: AI-assisted business narrative generation, with an offline fallback.





Project Structure



MamaEarth\_capstone/

│

├── Analysis/

│   ├── clean\_and\_eda.py

│   └── visualize.py

│

├── Data/

│   ├── customer.csv

│   ├── products.csv

│   └── orders.csv

│

├── SQL/

│   ├── schema.sql

│   ├── seed\_data.sql

│   └── reports.sql

│

├── narrator/

│   ├── findings.json

│   ├── generate\_narrative.py

│   ├── narrative.txt

│   └── sample\_output.txt

│

├── Visualizations/

│   ├── return\_rate\_by\_payment.png

│   └── monthly\_revenue\_trend.png

│

├── generate\_seed\_sql.py

├── load\_database.py

├── mamaearth\_capstone.db

└── README.md





#### The Analytical Workflow



* **Data preparation**: Load customer, product, and order data into the project workflow.



* **Database setup**: Define the database schema and prepare data for querying.



* **Data cleaning**: Identify duplicate business records, standardize payment-method labels, and handle missing values.



* **Exploratory data analysis**: Calculate return rates, summarize revenue, and investigate relationships between relevant variables.



* **Business reporting**: Use SQL and Python to analyze payment methods, city tiers, and monthly revenue.



* **Visualization**: Generate charts to communicate important trends.



* **Narrative generation**: Convert analytical findings into Situation, Complication, and Resolution sections using an AI-assisted workflow with an offline fallback.







#### Key Findings





###### Metric \& Finding



**Original orders**



180



**Duplicate business records removed**



5



**Orders after duplicate removal**



175



**Raw revenue**



₹99,860.20



**Cleaned revenue**



₹97,358.30



**Revenue associated with duplicate records**



₹2,501.90



**Returned orders**



44



**Overall return rate**



25.14%

#### 

#### City-Tier Analysis



Among COD orders, Tier 2 recorded the highest observed return rate:



Tier 2: 12 returns out of 22 orders (54.55%).



Tier 1: 12 returns out of 32 orders (37.50%).



These results describe the observed dataset and should not automatically be generalized to all customers or locations.



#### Revenue Trends



The highest monthly revenue in the full cleaned dataset occurred in January 2026, at ₹29,582.10.



After excluding two flagged high-quantity orders for a sensitivity analysis, March 2026 became the highest-revenue month, at ₹20,318.90.



The flagged orders remain in the main cleaned dataset. Their exclusion is limited to the adjusted sensitivity analysis.



Discount and Return Analysis



The Pearson correlation between discount percentage and order returns is approximately -0.088, indicating a negligible linear relationship in this dataset.



This result does not establish a causal relationship between discounts and returns.



#### Data Quality and Cleaning



The analysis identified and addressed the following issues:



Five duplicate business records were removed from the analytical dataset.



Twelve missing discount values were filled with zero.



Fifteen missing product-rating values were filled using the median rating of 3.0.



Payment-method labels were standardized for consistent reporting.



Two high-quantity orders were flagged for further review.



The flagged orders were retained in the primary cleaned dataset and excluded only from the adjusted revenue sensitivity analysis.



#### Visualizations



The project generates the following visualizations:



1. Return Rate by Payment Method: Compares the observed return rates across COD, card, and UPI orders.

2. Monthly Revenue Trend: Shows revenue movement over the analyzed months.



The generated charts are available in the Visualizations/ directory.



#### AI-Assisted Business Narrative



The narrative-generation component uses the Situation–Complication–Resolution (SCR) framework to convert analytical findings into a concise business report.



The report highlights the main business situation, identifies important complications in the data, and proposes evidence-based next steps.



The generator supports an offline fallback when the Gemini API key is unavailable or the API request fails.



The offline generator makes the narrative workflow usable without a live API connection. AI-generated or rule-based recommendations should still be reviewed before being used for business decisions.



#### Business Recommendations



Based on the observed findings:



1. Investigate the COD order journey, including customer confirmation, delivery refusal, and recorded return reasons.

2. Examine differences in COD return rates across city tiers before changing delivery or payment policies.

3. Review the two flagged high-quantity orders to determine whether they represent legitimate bulk purchases or data-quality issues.

4. Continue monitoring duplicate records, missing values, and inconsistent payment-method labels.

5. Track monthly revenue and return rates over time before drawing conclusions about sustained business trends.

6. These recommendations are investigative next steps, not proof that any single factor causes returns.



#### Project Outputs



The project produces:



* Cleaned data and exploratory analysis results.



* SQL database setup and reporting scripts.



* Return-rate and monthly-revenue visualizations.



* A structured findings file.



* An SCR business narrative and sample output.





