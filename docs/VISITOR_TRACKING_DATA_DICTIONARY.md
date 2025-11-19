# Galerly Visitor Tracking - Data Dictionary for UX Analysis

**Purpose**: This document explains every field in the `galerly-visitor-tracking` DynamoDB table to help data scientists analyze user behavior and improve UX.

**Table**: `galerly-visitor-tracking` (DynamoDB, AWS us-east-1)  
**Update Frequency**: Real-time (events written immediately)  
**Data Retention**: All historical data (implement TTL for cleanup as needed)

---

## Table of Contents
1. [Event Types](#event-types)
2. [Core Fields](#core-fields)
3. [Page View Event Fields](#page-view-event-fields)
4. [Custom Event Fields](#custom-event-fields)
5. [Session End Event Fields](#session-end-event-fields)
6. [Data Types & Formats](#data-types--formats)
7. [Analysis Examples](#analysis-examples)
8. [Querying the Data](#querying-the-data)

---

## Event Types

Every record has an `event_type` field that determines what happened:

| Event Type | Description | Frequency | Key Fields |
|------------|-------------|-----------|------------|
| `page_view` | User loads a page | Every page load | `page_url`, `duration_seconds`, `scroll_depth`, `clicks` |
| `page_engagement` | Periodic engagement update | Every 30 seconds while on page | `metadata.duration_seconds`, `metadata.scroll_depth_percent`, `metadata.total_clicks` |
| `page_exit` | User leaves a page | When navigating away | `metadata.duration_seconds`, `metadata.scroll_depth_percent`, `metadata.total_clicks`, `metadata.is_final: true` |
| `scroll_milestone` | User reaches scroll milestone | At 25%, 50%, 75%, 100% | `event_label` (e.g., "Scrolled 50%"), `event_value` (50) |
| `click_link` | User clicks a link | Every link click | `metadata.href`, `metadata.text`, `metadata.is_external` |
| `click_button` | User clicks a button | Every button click | `metadata.text`, `metadata.type`, `metadata.class` |
| `form_start` | User begins filling a form | First field interaction | `event_label` (form ID) |
| `form_complete` | User submits a form | On form submission | `event_value` (completion time in seconds), `metadata.fields_count` |
| `visibility_change` | User switches tabs | Tab hidden/visible | `event_label` ("page_hidden" or "page_visible") |
| `javascript_error` | JavaScript error occurs | On error | `metadata.error`, `metadata.stack`, `metadata.source` |
| `session_end` | User closes browser/tab | On page unload | `total_duration`, `total_pages_viewed`, `final_scroll_depth`, `final_clicks` |

---

## Core Fields

**These fields appear in EVERY event type:**

### `id` (String, HASH Key)
- **Type**: UUID v4
- **Example**: `"b49ff2fa-9f72-4793-8671-cf6432784d25"`
- **Purpose**: Unique identifier for this event record
- **Analysis Use**: Primary key for deduplication; not used for analysis

### `session_id` (String, Indexed)
- **Type**: UUID v4
- **Example**: `"abc12345-6789-4def-ghij-klmnopqrstuv"`
- **Purpose**: Groups all events from a single browser session (30-min timeout)
- **Analysis Use**: 
  - Track user journey through site
  - Calculate session duration
  - Identify drop-off points
  - Analyze multi-page behavior
- **Index**: `SessionIdIndex` (HASH: session_id, RANGE: timestamp)

### `visitor_id` (String, Optional)
- **Type**: UUID v4
- **Example**: `"def98765-4321-4fed-jihg-vutsrqponmlk"`
- **Purpose**: Persists across sessions to identify returning visitors
- **Storage**: Browser localStorage
- **Lifetime**: Until user clears browser data
- **Analysis Use**:
  - Count unique visitors vs. sessions
  - Track returning visitors
  - Analyze behavior changes over time
  - Cohort analysis
- **Note**: **Not** personally identifiable; resets if user clears data

### `event_type` (String, Indexed)
- **Type**: Enum (see Event Types table above)
- **Example**: `"page_view"`, `"click_button"`, `"session_end"`
- **Purpose**: Categorizes what type of event occurred
- **Analysis Use**:
  - Filter by event type
  - Count events by type
  - Build conversion funnels
- **Index**: `EventTypeIndex` (HASH: event_type, RANGE: timestamp)

### `timestamp` (String, ISO 8601)
- **Type**: ISO 8601 UTC timestamp
- **Example**: `"2025-11-16T14:32:45.123456Z"`
- **Purpose**: When the event occurred
- **Analysis Use**:
  - Time series analysis
  - Peak usage hours
  - Day of week patterns
  - Session timeline reconstruction
- **Note**: Always UTC; convert to local timezone for regional analysis

### `created_at` (String, ISO 8601)
- **Type**: ISO 8601 UTC timestamp
- **Example**: `"2025-11-16T14:32:45.123456Z"`
- **Purpose**: When the record was written to DynamoDB
- **Analysis Use**: Data quality checks (should match `timestamp` within seconds)

---

## Page View Event Fields

**Event Type**: `page_view`  
**Triggered**: When user loads a page  
**Purpose**: Initial page load data

### Page Information

#### `page_url` (String, Indexed)
- **Example**: `"https://galerly.com/pricing"`
- **Purpose**: Full URL of the page visited
- **Analysis Use**:
  - Most visited pages
  - Entry/exit pages
  - User flow analysis
  - Conversion funnel tracking
- **Index**: `PageUrlIndex` (HASH: page_url, RANGE: timestamp)
- **Best Practice**: Group by path (remove query params) for aggregation

#### `referrer` (String)
- **Example**: `"https://google.com/search?q=photography+platform"` or `""` (empty if direct)
- **Purpose**: Where user came from (previous page or external site)
- **Analysis Use**:
  - Traffic sources (organic, direct, referral)
  - Internal navigation patterns
  - Campaign tracking
  - Empty string = direct traffic or first page in session

### Device Information

#### `device_type` (String)
- **Type**: Enum
- **Values**: `"desktop"`, `"mobile"`, `"tablet"`
- **Example**: `"mobile"`
- **Purpose**: What type of device the user is on
- **Analysis Use**:
  - Device distribution
  - Mobile vs. desktop UX differences
  - Responsive design priorities
- **Detection**: Based on user agent string

#### `browser` (String)
- **Values**: `"Chrome"`, `"Firefox"`, `"Safari"`, `"Edge"`, `"unknown"`
- **Example**: `"Chrome"`
- **Purpose**: Which browser the user is using
- **Analysis Use**:
  - Browser compatibility issues
  - Feature support decisions
  - Testing priorities

#### `os` (String)
- **Values**: `"Windows"`, `"MacOS"`, `"Linux"`, `"Android"`, `"iOS"`, `"unknown"`
- **Example**: `"MacOS"`
- **Purpose**: User's operating system
- **Analysis Use**:
  - OS-specific bugs
  - Platform prioritization
  - Cross-platform UX consistency

#### `screen_resolution` (String)
- **Format**: `"width x height"`
- **Example**: `"1920x1080"`, `"390x844"` (iPhone 14)
- **Purpose**: Physical screen size in pixels
- **Analysis Use**:
  - Common screen sizes
  - Layout optimization
  - Responsive breakpoints

#### `viewport_size` (String)
- **Format**: `"width x height"`
- **Example**: `"1200x800"` (browser window size)
- **Purpose**: Actual browser window size (less than screen_resolution)
- **Analysis Use**:
  - Actual visible area
  - Scroll behavior analysis
  - Content visibility

#### `pixel_ratio` (Number, Decimal)
- **Example**: `2.0` (Retina), `1.0` (standard)
- **Purpose**: Device pixel density
- **Analysis Use**:
  - Image quality needs
  - High-DPI device usage
- **Values**: `1.0` (standard), `2.0` (Retina), `3.0` (high-end mobile)

#### `touch_support` (Boolean)
- **Values**: `true`, `false`
- **Example**: `true` (mobile/tablet), `false` (desktop)
- **Purpose**: Whether device supports touch
- **Analysis Use**:
  - Touch vs. mouse interaction design
  - Button size requirements

#### `user_agent` (String)
- **Example**: `"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36..."`
- **Purpose**: Full browser user agent string
- **Analysis Use**:
  - Detailed browser/device parsing
  - Bot detection
  - Technical debugging
- **Note**: Long string; use for advanced parsing only

### Location Information

**IMPORTANT**: All location data is IP-based geolocation, NOT GPS. Accuracy varies by ISP and region.

#### `location_accuracy` (String)
- **Values**: `"ip-based"`, `"timezone-only"`
- **Example**: `"ip-based"`
- **Purpose**: Indicates how location was determined (ALWAYS from IP, never GPS)
- **Analysis Use**:
  - Data quality indicator
  - Understand location precision limitations
- **IMPORTANT NOTES**:
  - `"ip-based"` = Location from IP geolocation service (ipapi.co or ip-api.com)
  - `"timezone-only"` = Geolocation services failed, only browser timezone available
  - **NO GPS**: We never collect GPS coordinates, only IP-based approximation
  - **Accuracy Range**: 50-200km (city-level, not street-level)
- **Privacy**: IP geolocation is anonymous and does not identify individuals

#### `country` (String)
- **Example**: `"United States"`, `"France"`, `"Japan"`
- **Purpose**: Visitor's country name
- **Analysis Use**:
  - Geographic distribution
  - Regional UX differences
  - Localization priorities
- **Source**: IP geolocation (ipapi.co)

#### `country_code` (String)
- **Format**: ISO 3166-1 alpha-2
- **Example**: `"US"`, `"FR"`, `"JP"`
- **Purpose**: Two-letter country code
- **Analysis Use**: Easier aggregation and mapping than country names

#### `city` (String)
- **Example**: `"New York"`, `"Paris"`, `"Tokyo"`, `""` (empty if unavailable)
- **Purpose**: Visitor's city (approximate, IP-based)
- **Analysis Use**:
  - City-level targeting
  - Regional campaigns
- **IMPORTANT NOTES**:
  - **Accuracy**: ~50-200km radius (not precise)
  - **May be wrong**: ISP routing can cause city mismatch (e.g., ISP in different city)
  - **Empty string possible**: If geolocation service fails
  - **Use with caution**: Good for general trends, NOT for precise targeting
- **Example Issue**: User in Geneva may show as "Carouge" (ISP location) or vice versa

#### `region` (String)
- **Example**: `"California"`, `"Île-de-France"`, `"Kanto"`
- **Purpose**: State/province/region
- **Analysis Use**: Regional analysis

#### `latitude` (Number, Decimal)
- **Example**: `40.7128` (NYC), `48.8566` (Paris), `0` (if unavailable)
- **Purpose**: Approximate latitude (IP-based, NOT GPS)
- **Analysis Use**:
  - Mapping visitors (general trends only)
  - Geographic clustering (regional level)
- **IMPORTANT NOTES**:
  - **Accuracy**: Typically rounded to city center or ISP location
  - **NOT GPS**: This is NOT real-time location, just IP lookup
  - **May be 50-200km off**: Depends on ISP routing and geolocation service
  - **Empty/0 possible**: If geolocation service fails
  - **Use for regions, not individuals**: Good for country/region analysis, NOT precise targeting

#### `longitude` (Number, Decimal)
- **Example**: `-74.0060` (NYC), `2.3522` (Paris), `0` (if unavailable)
- **Purpose**: Approximate longitude (IP-based, NOT GPS)
- **Analysis Use**: Geographic mapping (regional trends only)
- **IMPORTANT NOTES**: Same limitations as `latitude` above

#### `timezone` (String)
- **Example**: `"America/New_York"`, `"Europe/Paris"`, `"Asia/Tokyo"`
- **Purpose**: User's timezone (IANA format)
- **Analysis Use**:
  - Local time conversion
  - Peak hours by region
  - Time-of-day patterns

#### `ip_address` (String)
- **Example**: `"203.0.113.42"` (IPv4) or `"2001:db8::1"` (IPv6)
- **Purpose**: Visitor's IP address
- **Analysis Use**:
  - Abuse detection
  - Bot filtering
  - Advanced geolocation
- **Privacy**: Store only for legitimate purposes; consider anonymizing after processing

### Performance Metrics

#### `page_load_time` (Number, Decimal, milliseconds)
- **Example**: `2350.5` (2.35 seconds)
- **Purpose**: Total page load time (navigation start to load complete)
- **Analysis Use**:
  - Slow pages identification
  - Performance optimization priorities
  - User experience impact
- **Good**: <2000ms, **Acceptable**: 2000-4000ms, **Poor**: >4000ms

#### `dom_content_loaded` (Number, Decimal, milliseconds)
- **Example**: `1200.3`
- **Purpose**: Time until DOM is parsed and ready
- **Analysis Use**:
  - HTML parsing speed
  - Script loading impact

#### `dom_complete` (Number, Decimal, milliseconds)
- **Example**: `2100.7`
- **Purpose**: Time until DOM is fully built (including images)
- **Analysis Use**: Complete page rendering time

#### `first_paint` (Number, Decimal, milliseconds)
- **Example**: `450.2`
- **Purpose**: When browser first renders pixels
- **Analysis Use**:
  - Perceived speed
  - Above-the-fold optimization
- **Target**: <1000ms

#### `first_contentful_paint` (Number, Decimal, milliseconds)
- **Example**: `650.8`
- **Purpose**: When first text/image is rendered
- **Analysis Use**:
  - User engagement speed
  - Critical rendering path optimization
- **Target**: <1500ms (good), <2500ms (acceptable)

#### `connection_type` (String)
- **Values**: `"wifi"`, `"cellular"`, `"ethernet"`, `"bluetooth"`, `"4g"`, `"3g"`, `"2g"`, `"slow-2g"`, `"unknown"`
- **Example**: `"wifi"` (Chrome/Edge), `"4g"` (Chrome/Edge on mobile), `"unknown"` (Safari)
- **Purpose**: User's network connection type (REAL DATA ONLY - no fallbacks)
- **Analysis Use**:
  - Network performance by connection type
  - Mobile vs WiFi user behavior
  - Connection quality impact on UX
- **Detection**: Browser API only (navigator.connection.type or effectiveType)
- **Browser Support**:
  - ✅ **Chrome/Edge**: Reports actual type (`wifi`, `cellular`, `ethernet`) or effective type (`4g`, `3g`, `2g`)
  - ❌ **Safari (all platforms)**: Always `"unknown"` (no API support)
  - ❌ **Firefox (desktop)**: Usually `"unknown"` (limited API support)
  - ⚠️ **Firefox (Android)**: Sometimes reports effective type (`4g`, `3g`)
- **IMPORTANT NOTES**:
  - `"unknown"` = Browser doesn't support navigator.connection API (NOT a detection failure)
  - **NO FALLBACKS**: We never estimate or infer connection type. If the browser doesn't provide it, we leave it as `"unknown"`
  - **NO FAKE DATA**: Empty/unknown values are better than inaccurate estimations
- **Data Analysis**:
  - Filter by `connection_type != "unknown"` for network speed analysis
  - Cross-reference with `browser` field to understand `"unknown"` distribution
  - Safari users will always be `"unknown"` - segment them separately for analysis

#### `connection_downlink_mbps` (Number, Decimal, Mbps)
- **Values**: `0` (not available) or actual downlink speed in megabits per second
- **Example**: `10.5` (10.5 Mbps), `0` (Safari)
- **Purpose**: Measured network download speed (REAL DATA ONLY - no estimations)
- **Analysis Use**:
  - Actual network speed measurements
  - Performance correlations
  - Speed distribution analysis
- **IMPORTANT NOTES**:
  - `0` = Browser doesn't support navigator.connection API (Safari, old Firefox)
  - **NO FALLBACKS**: If browser doesn't provide it, value stays `0`
  - Only available when `connection_type != "unknown"`
  - Value is **measured** by browser, not estimated
- **Browser Support**:
  - ✅ Chrome/Edge: Real measured downlink speed
  - ❌ Safari: Always `0`
  - ⚠️ Firefox: Sometimes available on Android

#### `connection_rtt_ms` (Number, Decimal, milliseconds)
- **Values**: `0` (not available) or actual round-trip time in milliseconds
- **Example**: `50` (50ms latency), `0` (Safari)
- **Purpose**: Measured network latency (REAL DATA ONLY - no estimations)
- **Analysis Use**:
  - Network latency measurements
  - Connection quality analysis
  - Performance impact assessment
- **IMPORTANT NOTES**:
  - `0` = Browser doesn't support navigator.connection API (Safari, old Firefox)
  - **NO FALLBACKS**: If browser doesn't provide it, value stays `0`
  - Only available when `connection_type != "unknown"`
  - Lower is better (<100ms = good, 100-300ms = acceptable, >300ms = slow)
- **Browser Support**:
  - ✅ Chrome/Edge: Real measured RTT
  - ❌ Safari: Always `0`
  - ⚠️ Firefox: Sometimes available on Android

### Interaction Data

#### `duration_seconds` (Number, Decimal, seconds)
- **Example**: `45.23` (45.23 seconds)
- **Purpose**: Time spent on previous page (0 for first page)
- **Analysis Use**:
  - Engagement time
  - Content effectiveness
  - Page abandonment timing
- **Note**: For initial `page_view`, this is 0; use `page_engagement` and `page_exit` events for actual duration

#### `scroll_depth` (Number, Decimal, percentage)
- **Example**: `0` (initial), updated in `page_engagement` events
- **Purpose**: How far down the page user scrolled (0-100%)
- **Analysis Use**:
  - Content visibility
  - Fold optimization
  - Engagement depth
- **Interpretation**:
  - `0-25%`: Top of page only
  - `25-50%`: Read first section
  - `50-75%`: Engaged with most content
  - `75-100%`: Scrolled to bottom (high engagement)

#### `clicks` (Number, Integer)
- **Example**: `0` (initial), updated in `page_engagement` events
- **Purpose**: Number of clicks on this page
- **Analysis Use**:
  - Interaction level
  - Call-to-action effectiveness
  - Navigation patterns

#### `session_pages_viewed` (Number, Integer)
- **Example**: `1` (first page), `5` (fifth page in session)
- **Purpose**: How many pages user has viewed in this session
- **Analysis Use**:
  - Session depth
  - User engagement level
  - Bounce rate calculation (if = 1 at session_end)

---

## Custom Event Fields

**Event Types**: `click_link`, `click_button`, `form_start`, `form_complete`, `scroll_milestone`, `page_engagement`, `page_exit`, `visibility_change`, `javascript_error`

### `event_category` (String)
- **Values**: `"navigation"`, `"interaction"`, `"conversion"`, `"engagement"`, `"error"`
- **Example**: `"interaction"`
- **Purpose**: High-level categorization of event
- **Analysis Use**:
  - Group similar events
  - Conversion tracking
  - Error monitoring

### `event_label` (String)
- **Example**: 
  - `"link:https://galerly.com/pricing"` (click_link)
  - `"button:Get Started"` (click_button)
  - `"Scrolled 50%"` (scroll_milestone)
  - `"page_hidden"` (visibility_change)
- **Purpose**: Descriptive label for the event
- **Analysis Use**:
  - Detailed event breakdown
  - Specific action tracking
  - User intent understanding

### `event_value` (Number, Decimal)
- **Example**:
  - `50` (scroll_milestone at 50%)
  - `23.5` (form completion time in seconds)
  - `1` (click count)
- **Purpose**: Numeric value associated with event
- **Analysis Use**:
  - Quantitative metrics
  - Value aggregation
  - Performance measurement

### `metadata` (Map/Object)
- **Type**: JSON object with event-specific fields
- **Purpose**: Additional event context
- **Analysis Use**: Event-specific deep dive

#### Metadata for `click_link`:
```json
{
  "href": "https://galerly.com/pricing",
  "text": "See Pricing",
  "is_external": false
}
```

#### Metadata for `click_button`:
```json
{
  "text": "Get Started",
  "type": "submit",
  "class": "logo-18 grid-4 hero-11"
}
```

#### Metadata for `form_start`:
```json
{
  // No additional metadata
}
```

#### Metadata for `form_complete`:
```json
{
  "duration_seconds": 45.67,
  "fields_count": 3
}
```

#### Metadata for `page_engagement` / `page_exit`:
```json
{
  "duration_seconds": 32.5,
  "scroll_depth_percent": 78.5,
  "total_clicks": 3,
  "is_final": true  // only for page_exit
}
```

#### Metadata for `javascript_error`:
```json
{
  "error": "TypeError: Cannot read property 'value' of null",
  "stack": "at handleSubmit (auth.js:45:12)...",
  "source": "window.onerror",
  "url": "https://galerly.com/auth"
}
```

---

## Session End Event Fields

**Event Type**: `session_end`  
**Triggered**: When user closes browser/tab or navigates away from site  
**Purpose**: Session summary

### `total_duration` (Number, Decimal, seconds)
- **Example**: `245.67` (4 minutes 5 seconds)
- **Purpose**: Total time from session start to end
- **Analysis Use**:
  - Average session duration
  - Engagement level
  - User retention

### `page_duration` (Number, Decimal, seconds)
- **Example**: `45.23`
- **Purpose**: Time spent on the last page before exit
- **Analysis Use**: Exit page engagement

### `total_pages_viewed` (Number, Integer)
- **Example**: `7`
- **Purpose**: How many pages user viewed in session
- **Analysis Use**:
  - Session depth
  - Bounce rate (if = 1)
  - Site exploration level

### `total_interactions` (Number, Integer)
- **Example**: `23`
- **Purpose**: Total clicks/interactions in session
- **Analysis Use**: Overall engagement level

### `final_scroll_depth` (Number, Decimal, percentage)
- **Example**: `92.5`
- **Purpose**: How far user scrolled on last page
- **Analysis Use**: Exit page engagement

### `final_clicks` (Number, Integer)
- **Example**: `5`
- **Purpose**: Clicks on last page before exit
- **Analysis Use**: Exit page interaction

### `exit_page` (String)
- **Example**: `"https://galerly.com/pricing"`
- **Purpose**: Last page user was on before leaving
- **Analysis Use**:
  - Exit page identification
  - Drop-off analysis
  - Conversion barriers

---

## Data Types & Formats

### DynamoDB Type Mapping

| Field Type | DynamoDB Type | Python Type | Example |
|------------|---------------|-------------|---------|
| String | String (S) | str | `"text"` |
| Number | Number (N) stored as Decimal | Decimal | `123.45` |
| Boolean | Boolean (BOOL) | bool | `true` |
| Timestamp | String (S) | str (ISO 8601) | `"2025-11-16T14:32:45.123456Z"` |
| Map/Object | Map (M) | dict | `{"key": "value"}` |

### Important Notes:

1. **Decimals**: All numeric values are stored as DynamoDB `Decimal` to preserve precision
2. **Timestamps**: Always UTC in ISO 8601 format with 'Z' suffix
3. **Empty Strings**: May appear for optional fields (e.g., empty `referrer` for direct traffic)
4. **Missing Fields**: Some fields may not exist in older records (before feature was added)

---

## Analysis Examples

### 1. Calculate Bounce Rate
**Definition**: % of sessions with only 1 page view

```python
# Query all session_end events
session_ends = table.scan(
    FilterExpression='event_type = :type',
    ExpressionAttributeValues={':type': 'session_end'}
)

single_page_sessions = sum(1 for item in session_ends['Items'] if item['total_pages_viewed'] == 1)
total_sessions = len(session_ends['Items'])
bounce_rate = (single_page_sessions / total_sessions) * 100
```

**Expected Range**: 40-60% is normal; >70% indicates issues

### 2. Find Pages Where Users Get Stuck
**Criteria**: Low scroll depth + short duration

```python
# Query page_exit events
exits = table.scan(
    FilterExpression='event_type = :type',
    ExpressionAttributeValues={':type': 'page_exit'}
)

stuck_pages = {}
for item in exits['Items']:
    meta = item.get('metadata', {})
    scroll = float(meta.get('scroll_depth_percent', 0))
    duration = float(meta.get('duration_seconds', 0))
    
    # Stuck = stayed <10s OR scrolled <25%
    if duration < 10 or scroll < 25:
        page = item['page_url']
        stuck_pages[page] = stuck_pages.get(page, 0) + 1

# Sort by frequency
stuck_pages_sorted = sorted(stuck_pages.items(), key=lambda x: x[1], reverse=True)
```

**Action**: Investigate top 5 pages for UX issues

### 3. Identify High-Engagement Content
**Criteria**: High scroll depth + long duration

```python
# Query page_exit events
exits = table.scan(
    FilterExpression='event_type = :type',
    ExpressionAttributeValues={':type': 'page_exit'}
)

engaged_pages = {}
for item in exits['Items']:
    meta = item.get('metadata', {})
    scroll = float(meta.get('scroll_depth_percent', 0))
    duration = float(meta.get('duration_seconds', 0))
    
    # Engaged = stayed >30s AND scrolled >75%
    if duration > 30 and scroll > 75:
        page = item['page_url']
        engaged_pages[page] = engaged_pages.get(page, 0) + 1

# Sort by frequency
engaged_pages_sorted = sorted(engaged_pages.items(), key=lambda x: x[1], reverse=True)
```

**Action**: Replicate successful content patterns

### 4. Device-Specific Performance Issues
**Find slow pages by device**

```python
from statistics import mean

# Query page_view events
page_views = table.scan(
    FilterExpression='event_type = :type',
    ExpressionAttributeValues={':type': 'page_view'}
)

# Group by device and page
perf_by_device = {
    'desktop': {},
    'mobile': {},
    'tablet': {}
}

for item in page_views['Items']:
    device = item['device_type']
    page = item['page_url']
    load_time = float(item['page_load_time'])
    
    if page not in perf_by_device[device]:
        perf_by_device[device][page] = []
    perf_by_device[device][page].append(load_time)

# Calculate averages
for device in perf_by_device:
    for page, times in perf_by_device[device].items():
        avg = mean(times)
        if avg > 3000:  # >3 seconds
            print(f"SLOW: {device} - {page}: {avg:.0f}ms")
```

**Action**: Optimize slow pages for specific devices

### 5. User Journey Analysis (Funnel)
**Track conversion path**

```python
# Define funnel
funnel_pages = [
    'https://galerly.com/',
    'https://galerly.com/pricing',
    'https://galerly.com/auth'
]

# Query sessions that visited all funnel pages
sessions_with_all_pages = {}

# Group events by session
for page in funnel_pages:
    response = table.query(
        IndexName='PageUrlIndex',
        KeyConditionExpression='page_url = :url',
        ExpressionAttributeValues={':url': page}
    )
    
    for item in response['Items']:
        sid = item['session_id']
        if sid not in sessions_with_all_pages:
            sessions_with_all_pages[sid] = set()
        sessions_with_all_pages[sid].add(page)

# Count conversions
completed_funnel = sum(1 for pages in sessions_with_all_pages.values() 
                       if len(pages) == len(funnel_pages))
total_started = len([s for s in sessions_with_all_pages.values() 
                     if funnel_pages[0] in s])

conversion_rate = (completed_funnel / total_started) * 100
```

**Metrics**:
- Funnel completion rate
- Drop-off at each step
- Time between steps

### 6. Error Impact Analysis
**Correlate errors with user behavior**

```python
# Query error events
errors = table.scan(
    FilterExpression='event_type = :type',
    ExpressionAttributeValues={':type': 'javascript_error'}
)

# Group errors by page and type
error_summary = {}
for item in errors['Items']:
    page = item['page_url']
    error_msg = item.get('metadata', {}).get('error', 'unknown')
    
    key = (page, error_msg)
    error_summary[key] = error_summary.get(key, 0) + 1

# Find sessions with errors
error_sessions = set(item['session_id'] for item in errors['Items'])

# Compare bounce rates: sessions with errors vs. without
# ... (query session_end for both groups)
```

**Insight**: Do errors lead to higher bounce rates?

### 7. Mobile vs. Desktop Behavior
**Compare engagement by device**

```python
# Query all page_exit events
exits = table.scan(
    FilterExpression='event_type = :type',
    ExpressionAttributeValues={':type': 'page_exit'}
)

metrics_by_device = {
    'desktop': {'duration': [], 'scroll': [], 'clicks': []},
    'mobile': {'duration': [], 'scroll': [], 'clicks': []},
    'tablet': {'duration': [], 'scroll': [], 'clicks': []}
}

# Get corresponding page_view for device type
for exit in exits['Items']:
    sid = exit['session_id']
    meta = exit.get('metadata', {})
    
    # Query page_view from same session to get device
    page_views = table.query(
        IndexName='SessionIdIndex',
        KeyConditionExpression='session_id = :sid',
        FilterExpression='event_type = :type',
        ExpressionAttributeValues={':sid': sid, ':type': 'page_view'},
        Limit=1
    )
    
    if page_views['Items']:
        device = page_views['Items'][0]['device_type']
        metrics_by_device[device]['duration'].append(float(meta.get('duration_seconds', 0)))
        metrics_by_device[device]['scroll'].append(float(meta.get('scroll_depth_percent', 0)))
        metrics_by_device[device]['clicks'].append(int(meta.get('total_clicks', 0)))

# Calculate averages
for device, metrics in metrics_by_device.items():
    avg_duration = mean(metrics['duration']) if metrics['duration'] else 0
    avg_scroll = mean(metrics['scroll']) if metrics['scroll'] else 0
    avg_clicks = mean(metrics['clicks']) if metrics['clicks'] else 0
    
    print(f"{device.upper()}:")
    print(f"  Avg Duration: {avg_duration:.1f}s")
    print(f"  Avg Scroll: {avg_scroll:.1f}%")
    print(f"  Avg Clicks: {avg_clicks:.1f}")
```

**Insight**: Mobile users typically have lower engagement; adjust UX accordingly

---

## Querying the Data

### Using Python (boto3)

```python
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('galerly-visitor-tracking')

# 1. Get all events for a session
response = table.query(
    IndexName='SessionIdIndex',
    KeyConditionExpression=Key('session_id').eq('your-session-id')
)

# 2. Get all page views
response = table.scan(
    FilterExpression=Attr('event_type').eq('page_view'),
    Limit=1000
)

# 3. Get events for specific page
response = table.query(
    IndexName='PageUrlIndex',
    KeyConditionExpression=Key('page_url').eq('https://galerly.com/pricing')
)

# 4. Get events in time range (requires event_type filter first)
from datetime import datetime, timedelta

start_time = (datetime.utcnow() - timedelta(days=7)).isoformat() + 'Z'
end_time = datetime.utcnow().isoformat() + 'Z'

response = table.query(
    IndexName='EventTypeIndex',
    KeyConditionExpression=Key('event_type').eq('page_view') & Key('timestamp').between(start_time, end_time)
)
```

### Using AWS CLI

```bash
# Scan all records (max 1MB)
aws dynamodb scan --table-name galerly-visitor-tracking --limit 100

# Query by session
aws dynamodb query \
  --table-name galerly-visitor-tracking \
  --index-name SessionIdIndex \
  --key-condition-expression "session_id = :sid" \
  --expression-attribute-values '{":sid":{"S":"abc-123"}}'

# Filter by event type
aws dynamodb scan \
  --table-name galerly-visitor-tracking \
  --filter-expression "event_type = :type" \
  --expression-attribute-values '{":type":{"S":"page_view"}}'
```

### Using AWS Console

1. Go to DynamoDB → Tables → `galerly-visitor-tracking`
2. Click "Explore table items"
3. Use filters:
   - **Scan**: Full table scan (slow, expensive)
   - **Query**: Use indexes (SessionIdIndex, EventTypeIndex, PageUrlIndex)
4. Export to CSV for analysis in Excel/Python

---

## Best Practices for Data Scientists

### Data Quality Checks

1. **Check for duplicates**: Events should have unique `id`
2. **Validate timestamps**: Should be sequential within sessions
3. **Check completeness**: Required fields should not be empty
4. **Outlier detection**: Flag extreme values (e.g., 10-hour page duration)

### Performance Optimization

1. **Use indexes**: Always query via SessionIdIndex, EventTypeIndex, or PageUrlIndex
2. **Limit results**: Start with small samples (Limit=100) for exploratory analysis
3. **Aggregate data**: Store daily/weekly summaries instead of querying raw data repeatedly
4. **Export to analytics tools**: Move to BigQuery, Redshift, or Snowflake for complex analysis

### Privacy Considerations

1. **No PII in analysis**: Never try to identify individual users
2. **Aggregate by cohorts**: Group users by behavior patterns, not individuals
3. **Anonymize IP addresses**: Truncate last octet (e.g., `203.0.113.XXX`)
4. **Respect data retention**: Delete old data per company policy (recommend 90 days)

### Recommended Analysis Tools

- **Python**: pandas, numpy, scipy, matplotlib, seaborn
- **R**: tidyverse, ggplot2, dplyr
- **BI Tools**: Tableau, Power BI, Looker
- **Data Warehouses**: AWS Athena (query DynamoDB export), BigQuery, Snowflake

---

## Common UX Metrics to Calculate

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Bounce Rate** | (Single-page sessions / Total sessions) × 100 | >70% = problem |
| **Avg Session Duration** | Sum(total_duration) / Count(sessions) | >2 min = engaged |
| **Pages per Session** | Sum(total_pages_viewed) / Count(sessions) | >3 = exploring site |
| **Exit Rate** | (Exits from page / Total page views) × 100 | High exit = friction |
| **Scroll Depth (Avg)** | Mean(scroll_depth) for all page_exit events | <50% = content not engaging |
| **Time to Interact** | Timestamp(first_click) - Timestamp(page_view) | <5s = engaging CTA |
| **Form Completion Rate** | (form_complete / form_start) × 100 | <50% = form issues |
| **Error Rate** | (javascript_error events / page_view events) × 100 | >1% = code problems |

---

## Questions?

**Contact**: Data Team  
**DynamoDB Table**: `galerly-visitor-tracking` (us-east-1)  
**Documentation**: `/docs/VISITOR_TRACKING_IMPLEMENTATION.md`  
**Last Updated**: November 16, 2025

---

## Changelog

- **v1.1** (2025-11-16):
  - Removed `page_title` field (not collected)
  - Removed `location_note` field (not collected)
  - Added comprehensive documentation for `connection_type`, `connection_downlink_mbps`, `connection_rtt_ms`
  - **Data Philosophy**: NO FALLBACKS, NO ESTIMATIONS, REAL DATA ONLY
  - Clarified IP-based geolocation accuracy limitations
  - Added `location_accuracy` field documentation
  - Emphasized browser API limitations (Safari always shows `"unknown"` for connection data)
- **v1.0** (2025-11-16): Initial data dictionary with all fields documented

