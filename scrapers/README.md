# Flight Scraper Documentation

This document logs our development process, architecture, and the exact scraping mechanism used for each OTA and airline site.

## Architecture Update

We have permanently shifted to a **Sequential Architecture (`BATCH_SIZE=1`)** using `undetected_chromedriver` across all 11 spiders. Previously, launching multiple undetected-chromedriver instances concurrently caused `OSError: [WinError 6] The handle is invalid` and `[WinError 183]` exceptions on Windows. The sequential orchestrator entirely eliminated this issue and achieved a 100% success rate across all platforms during execution. 

All scrapers extend a common `UCSpider` base class and utilize CDP (Chrome DevTools Protocol) Network Interception as their primary extraction method, with BeautifulSoup DOM extraction as a fallback.

All scrapers strictly adhere to MoSPI standards: **Economy class**, **1 Adult**, **One-way**, and **Non-stop only**. Flights containing terms like "Premium Economy", "Business", "First Class", "1 Stop", "2 Stop", or "Layover" are explicitly filtered out.

---

## OTA Scrapers (Implemented & Stable)

### 1. MakeMyTrip (MMT)
- **Scraping Mechanism**: `undetected_chromedriver` (UI Automation + CDP / DOM Fallback)
- **Details**: MakeMyTrip uses strong bot protection. Direct URL navigation returns 0 flights. To bypass this, we load the homepage, dismiss modals, and use `ActionChains` to mimic human interaction (entering origin, destination, and selecting the date from the calendar). We attempt to intercept the background API payload via CDP. If CDP interception fails or returns empty, the scraper falls back to an aggressive DOM parsing strategy that repeatedly scrolls the page (virtual scrolling) and extracts flight data (`listingCard`) using BeautifulSoup.

### 2. Goibibo
- **Scraping Mechanism**: `undetected_chromedriver` (UI Automation + CDP / DOM Fallback)
- **Details**: Goibibo uses the exact same backend infrastructure as MakeMyTrip (it's the same parent company). We utilize the exact same UI navigation flow as MakeMyTrip to evade bot blocking, followed by CDP API interception. If CDP fails, we use a similar scroll-based BeautifulSoup DOM parser to extract flights from `srp-card` components.

### 3. Cleartrip
- **Scraping Mechanism**: `undetected_chromedriver` (CDP Network Interception)
- **Details**: We monitor network traffic via CDP for XHR responses. We decode and parse the JSON payload directly. If the API payload fails to be intercepted, we fall back to a BeautifulSoup DOM parser to hunt for exact flight cards.

### 4. EaseMyTrip (EMT)
- **Scraping Mechanism**: `undetected_chromedriver` (CDP Network Interception)
- **Details**: Monitors network traffic and intercepts responses via CDP. The JSON payload contains a list of flights with detailed pricing information which is parsed directly.

### 5. Ixigo
- **Scraping Mechanism**: `undetected_chromedriver` (DOM Parsing)
- **Details**: Ixigo's API endpoints are heavily protected by Akamai Bot Manager and they obfuscate their JSON payloads with anti-bot tokens that are difficult to replicate. Therefore, we load the page fully, wait for the flight cards to render, and parse the HTML using BeautifulSoup to extract flight numbers, departure times, and prices.

### 6. Yatra
- **Scraping Mechanism**: `undetected_chromedriver` (DOM Parsing)
- **Details**: Yatra blocks direct API access and uses heavy bot protection. We load the page and wait for the DOM to render the flight cards (`.flightItem`) and parse the prices using BeautifulSoup.

---

## Direct Airline Scrapers (Implemented & Stable)

The problem statement requires scraping the airlines directly without delegating to OTAs. All 5 required airlines are successfully implemented using `undetected_chromedriver` and CDP interception.

### 7. IndiGo (6E)
- **Scraping Mechanism**: `undetected_chromedriver` (UI Automation + CDP Network Interception)
- **Details**: Direct API access is blocked by Cloudflare. We automate the native UI using `ActionChains` to fill origin, destination, and select the exact date cell from the calendar. We click "Search Flights" and intercept the raw JSON API response payload via CDP to extract the lowest active `totalFareAmount`.

### 8. Air India (AI)
- **Scraping Mechanism**: `undetected_chromedriver` (UI Automation + CDP Network Interception)
- **Details**: We load the homepage, dismiss the cookie banner, input origin/destination, select the date, and trigger the search. We monitor the CDP logs for the `air-bounds` endpoint and extract the JSON payload, picking the `eco` cabin fare.

### 9. SpiceJet (SG)
- **Scraping Mechanism**: `undetected_chromedriver` (UI Automation + CDP Network Interception)
- **Details**: SpiceJet's API requires valid UI interaction tokens. We automate the native UI calendar and search inputs, then intercept the background availability API JSON payload via CDP.

### 10. Akasa Air (QP)
- **Scraping Mechanism**: `undetected_chromedriver` (UI Automation + CDP Network Interception)
- **Details**: Akasa Air is heavily guarded by Akamai Bot Manager (`/markets` and `/flights` API return 401/403 for bots). We automate the UI and trigger the search natively to generate the correct Akamai session cookies, then intercept the JSON response payload. 

### 11. Air India Express (IX)
- **Scraping Mechanism**: `undetected_chromedriver` (UI Automation + CDP / DOM Fallback)
- **Details**: We use native UI automation to fill the origin, destination, and date inputs. We monitor the CDP for the API response. If CDP fails or times out, we use a robust DOM fallback to extract flights directly from the loaded React flight cards.
