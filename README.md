# 🐕 Dog Influencer Collector

A simple Python tool to collect, organize, and track dog-related social media influencers across Instagram and TikTok.

---

## 🎯 Goal

* Build a database of **dog influencers** with key details like followers, engagement, niche, and contact info.
* Quickly grow your collection to **200 profiles in Week 1**.
* Combine **manual entry** and **automatic scraping**.

---

## 📦 Features

1. **Manual Entry**

   * Enter influencer details directly via an interactive menu.
   * Supports all major fields: name, platform, handle, followers, engagement, niche, style, bio, email, location, and post count.

2. **Instagram Scraper**

   * Scrapes public Instagram profiles using `Instaloader`.
   * Collects followers, engagement, bio snippet, post count, verification status, and recent posts.

3. **TikTok Scraper**

   * Scrapes public TikTok profiles using `Playwright`.
   * Collects followers, bio snippet, and contact info (where available).

4. **Batch Import**

   * Import a list of handles from a text file to scrape in bulk.

5. **Stats & Reporting**

   * Shows total profiles, breakdown by platform and source, and collection progress.

6. **CSV Database**

   * All influencer data is stored in `dog_influencers.csv`.
   * Organized with enhanced headers for easy filtering and analysis.

---

## 🛠 Setup

1. **Clone the repo**

```bash
git clone <repo-url>
cd <repo-folder>
```

2. **Create a virtual environment**

```bash
python -m venv .venv
```

3. **Activate the virtual environment**

* **Windows:**

```bash
.venv\Scripts\activate
```

* **Mac/Linux:**

```bash
source .venv/bin/activate
```

4. **Install dependencies**

```bash
pip install -r requirements.txt
```

5. **Run the collector**

```bash
python main.py
```

---

## 📝 Notes

* This tool is designed for **publicly available information only**.
* TikTok scraping may be slower due to page restrictions.
* CSV can be opened in Excel, Google Sheets, or any data tool for analysis.
* The project is **actively evolving**, so fields and scraping logic may change.

---

## ⚡ Quick Start

1. Start the program: `python main.py`
2. Choose **Manual Entry** or **Scrape Instagram/TikTok**
3. Add influencers and watch the CSV grow!
4. Check stats anytime from the menu.

---

## 📂 CSV Structure

| Field          | Description                                 |
| -------------- | ------------------------------------------- |
| id             | Unique number                               |
| name           | Influencer’s full name                      |
| platform       | Instagram or TikTok                         |
| handle         | Social media handle                         |
| followers      | Number of followers                         |
| avg_engagement | Average engagement rate                     |
| primary_niche  | Main dog-related niche                      |
| content_style  | Style of content (Funny, Educational, etc.) |
| bio_snippet    | Short version of bio                        |
| email          | Contact email if found                      |
| location       | General location if available               |
| post_count     | Total number of posts                       |
| date_added     | Date added to CSV                           |
| source_tag     | How the data was collected                  |
| verified       | Profile verification status                 |
| last_post_date | Most recent post date                       |

---

This README gives a clear overview without diving too deep into the code, while still being informative for collaborators or users.