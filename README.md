# 🚌 College Bus Fare Management System

This project is a web-based prototype for a **Data-Driven Bus Fare Management System** designed for **Velalar College of Engineering and Technology**.

It replaces an inefficient, flat-fee system with a fair and transparent **Student-Kilometer (pkm) pricing model**. The system ensures students only pay for the distance they travel and provides administrators with powerful tools for cost management and analytics.

---

## 🚀 Key Features

### 👨‍💼 Admin Dashboard (`/`)
A password-protected (in production) portal for administrators with four main modules:

* **💰 Fare Calculator:** Calculates fair semester fees for all students on a route.
    * Inputs: Daily operational costs (fuel, salary, maintenance), bus mileage, and student counts per zone.
    * Logic: Automatically fetches the latest fuel price and calculates the total semester cost.
    * Output: Distributes the cost fairly using the Student-Kilometer model and saves the new fares to the database.
* **🚌 Merge Calculator:** A tool to calculate the cost savings of merging two under-capacity buses into one for a semester.
* **🔧 Digital Logs:** A complete logging system where admins can add, view, and track all vehicle-related events, including:
    * Maintenance
    * Fuel Consumption
    * Driver Performance
    * Trip History
* **📊 Analytics:** A dashboard that queries the live database to generate:
    * A **line chart** of historical diesel prices.
    * A **pie chart** breaking down all logged expenses by category (e.g., "Fuel" vs. "Maintenance").

### 👩‍🎓 Student Dashboard (`/student`)
A simple, public-facing portal where students can check their fees.

* **Fee Lookup:** Students select their boarding zone (e.g., "Pallipalayam") from a dropdown.
* **Full Transparency:** The dashboard displays not just the final fee, but a complete breakdown of *how* that fee was calculated:
    1.  The total operating cost for the semester (Fuel, Salary, etc.).
    2.  The "Cost per Student-Kilometer" logic.
    3.  The final calculation: `(Your_Distance_KM * Cost_per_Student_KM) = Your_Fare`.

---

## ⚙️ How the Fare Logic Works

This system is built on a "Student-Kilometer" (or "Usage Unit") model to ensure fairness.

1.  **Calculate Total Semester Cost:** The admin inputs daily costs (e.g., `Fuel/Day` + `Salary/Day`) and the number of days. The system calculates the `Total Semester Cost`.
2.  **Calculate Total Usage:** The system looks at all students on the route and calculates the total "Usage Units" for the semester.
    * *e.g., (10 students * 8km) + (15 students * 19km) + (20 students * 24km) = 845 Total Usage Units*
3.  **Find Cost per Unit:** The system divides the total cost by the total usage.
    * *e.g., `₹500,000 / 845 Units = ₹591.70 per "Usage Unit"`*
4.  **Calculate Student Fare:** Each student's fare is simply their distance multiplied by this rate.
    * *Student at 8km:* `8 * ₹591.70 = ₹4,733`
    * *Student at 24km:* `24 * ₹591.70 = ₹14,200`

---

## 🛠️ Technology Stack

* **Backend:** **Python** with **Flask**
* **Database:** **SQLite** (for all fares, logs, and fuel prices)
* **Frontend:** **HTML5**, **Bootstrap 5**
* **Visualizations:** **Chart.js**

---

## 🏁 How to Run

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up the database:**
    * Run the setup script **once** to create `transport.db` and populate it.
    * (Make sure `Diesel dataset.txt` is in the same folder).
    ```bash
    python setup_db.py
    ```

4.  **Run the application:**
    ```bash
    python app.py
    ```

5.  **Access the dashboards in your browser:**
    * **Admin Dashboard:** `http://127.0.0.1:5000/`
    * **Student Dashboard:** `http://127.0.0.1:5000/student`
