# Reflection 3

I thought adding an index would speed up the dashboard. SQLite still scanned the order lines. The same date index helped the single-day lookup, though. The median went from 0.978 ms to 0.058 ms. When I wrapped the date column in date(), SQLite went back to a scan. I want to remember to check the plan as well as the time.

I got stuck a few times by pasting SQL at the wrong terminal prompt. That got easier once I understood when I was inside SQLite. The binding demo also made sense to me because I could see how a name with an apostrophe was handled when it was passed as a value.

I used AI to help read the plans. I checked the explanation by comparing the output before and after adding the date index. One thing I'd ask my pod is how many runs we need before a small timing difference is worth talking about.
