# Finet - Personal Finance Tracker 💰

**Finet** is a modern, cross-platform personal finance tracker built with Python and Flet. It helps you organize your finances, track income and expenses across multiple currencies, set budgets, and visualize your spending—all locally on your device with complete data privacy.

---

## ✨ Features

Finet offers a comprehensive set of tools to manage your personal finances effectively:

* **📊 Insightful Dashboard:** Get a quick overview of your financial health with key metrics (Income, Expense, Net), charts visualizing income vs. expense trends, category breakdowns, daily spending patterns, and budget utilization.
* **💸 Transaction Management:** Easily add, edit, and delete income and expense transactions. Include details like date, amount, category, account, currency, and notes.
* **🌍 Multi-Currency Support:**
  * Track balances and transactions in various currencies (USD, EUR, GBP, JPY, CHF, CAD, UAH supported by default) [provided in previous turns].
  * Set a **base currency** for unified analytics and reporting [provided in previous turns].
  * Manually configure exchange rates or **fetch the latest rates** automatically from the internet [provided in previous turns].
  * Transactions store both original and **historically accurate converted amounts**, ensuring analytics remain correct even if rates change [provided in previous turns].
  * Optionally **recalculate historical data** using updated exchange rates [provided in previous turns].
* **🏦 Account Management:**
  * Manage multiple accounts (Cash, Bank, Credit Card).
  * Track balances in different currencies for each account.
  * Transfer funds between accounts.
  * Set **low balance alert thresholds** per currency for each account.
* **🎯 Budgeting:**
  * Set budgets for specific categories (e.g., Food, Transport) over different periods (Monthly, Weekly, Custom).
  * Monitor budget progress visually with clear indicators for spending status (On Track, Warning, Exceeded).
  * Budget amounts are set in your base currency for easy comparison [provided in previous turns].
* **🔄 Recurring Transactions & Planning:**
  * Set up recurring income or expenses (Daily, Weekly, Monthly, Yearly, Custom Interval).
  * Schedule **one-time planned expenses** for future dates (e.g., upcoming bills) [provided in previous turns].
  * View upcoming bills and subscriptions directly on the dashboard.
* **🏷️ Category Management:**
  * Create, edit, and delete custom categories.
  * Assign icons for better visual identification.
  * Explicitly mark categories as 'Income' or 'Expense' for accurate calculations [provided in previous turns].
* **⚠️ Notifications:**
  * See **Low Balance Alerts** prominently on the dashboard when an account drops below its threshold.
  * View **Upcoming Bills & Subscriptions** reminders on the dashboard.
* **💾 Data Management:**
  * **Local-First:** All data is stored locally in a `finet.db` SQLite file. You own your data.
  * **Import/Export:** Easily import transactions from or export them to CSV files.
  * **Backup & Restore:** Create backups of your database, with an option for strong **passphrase-based encryption** (AES-256) [provided in previous turns].
* **🖥️ Cross-Platform:** Runs on Windows, macOS, and Linux thanks to Flet.

---

## 🚀 Running Finet (Choose one method)

### Method 1: Using Docker (Recommended for ease of use)

This is the simplest way to run Finet without installing Python or dependencies manually.

1. **Install Docker:** Get Docker Desktop for your OS from [docker.com](https://www.docker.com/products/docker-desktop/).
2. **Run the Finet Image:** Open your terminal or command prompt and run the following command. Replace `your-github-username` with your actual GitHub username and `latest` or a specific version tag (e.g., `1.0.0`):

    ```bash
    docker run -d --name finet-app -p 8550:8550 -v finet_data:/app/app/db ghcr.io/your-github-username/finet:latest
    ```

    * `-d`: Run in detached mode.
    * `--name finet-app`: Assign a container name.
    * `-p 8550:8550`: Map your machine's port 8550 to the container's port 8550.
    * `-v finet_data:/app/app/db`: **Crucial:** Mounts a Docker volume named `finet_data` to store your `finet.db` file persistently outside the container.
    * `ghcr.io/your-github-username/finet:latest`: The Docker image path.

3. **Access the App:** Open your web browser and navigate to `http://localhost:8550`.

**Docker Management Commands:**

* Stop: `docker stop finet-app`
* Start: `docker start finet-app`
* View Logs: `docker logs finet-app`
* Update: Stop (`stop`), remove (`rm finet-app`), pull the new image (`pull`), and re-run the `docker run` command.

### Method 2: Install Locally

**Install Locally (For Development):**

 ```bash
    git clone [https://github.com/your-github-username/Finet.git](https://github.com/your-github-username/Finet.git)
    cd Finet
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -e .
    finet # Run the app from the project directory
   ```

---

## 🔒 Security & Backup

Finet prioritizes local data storage using a SQLite database file (`finet.db`). The exact location depends on how you run the app:

* **Docker:** Managed within the `finet_data` Docker volume. Use Docker commands/tools to manage or back up this volume.
* **pip install:** Typically within your Python environment's `site-packages` or user data directory.
* **Local Development:** In the `app/db/` directory relative to where you run `finet`.

### In-App Backup/Restore

Use the **Settings** tab to create manual backups (`.db` or encrypted `.enc` files) and restore from them. Remember that restoring **overwrites** your current live database.

### Security Notes

* The live `finet.db` file **is not encrypted at rest**. Secure the file/volume location appropriately.
* Unencrypted backups (`.db`) are plain copies and also not secure.
* Encrypted backups (`.enc`) use AES-256 and rely on your passphrase. **If you lose the passphrase, the backup is unusable.**
* **You are responsible** for securing your database file and managing your backups.

---

## 📸 Screenshots

## 📄 License
