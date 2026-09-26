# TravelTrip World — SEO Best Update Instructions
**Date:** 26 September 2026

## যা যা করতে হবে (Step by Step)

### 1. robots.txt আপডেট
- `public/robots.txt` ফাইলটা ডিলিট করে নতুন `robots.txt` আপলোড করো (অথবা রিপ্লেস করো)।

### 2. sitemap.xml আপডেট
- `public/sitemap.xml` ফাইলটা নতুন `sitemap.xml` দিয়ে রিপ্লেস করো।
- Google Search Console-এ গিয়ে **Sitemaps** সেকশনে `https://traveltrip.world/sitemap.xml` সাবমিট/রিফ্রেশ করো।

### 3. index.html এর <head> উন্নত করা
- `public/index.html` খুলে বিদ্যমান `<head>...</head>` অংশটুকু মুছে ফেলো।
- `index-head-seo-improved.html` ফাইলের ভিতরের কোড কপি করে পেস্ট করো।
- তোমার আগের CSS/JS লিংকগুলো ঠিকভাবে রেখে দাও (ফাইলের শেষে নোট আছে)।

### 4. Schema (ঐচ্ছিক কিন্তু খুব ভালো)
- Organization Schema ইতিমধ্যে index-head-এ যোগ করা আছে।
- Country পেজগুলোতে Product Schema যোগ করতে চাইলে বলো, আমি দিয়ে দিব।

### 5. Vercel Deploy
- সব ফাইল `public/` ফোল্ডারে পুশ করার পর Vercel অটো ডিপ্লয় করবে।
- ডিপ্লয় হওয়ার পর Google Search Console-এ **URL Inspection** দিয়ে হোমপেজ টেস্ট করো।

---

## ফাইল লিস্ট
| ফাইল | কোথায় রাখবে |
|------|-------------|
| robots.txt | public/robots.txt |
| sitemap.xml | public/sitemap.xml |
| index-head-seo-improved.html | শুধু রেফারেন্স — কোড কপি করে index.html-এ পেস্ট |
| schema-organization.jsonld | রেফারেন্স |

---

## অতিরিক্ত টিপস (Best Practice)
1. Google Search Console + Bing Webmaster Tools সেটআপ রাখো।
2. প্রতি মাসে sitemap-এর lastmod আপডেট করো।
3. নতুন কান্ট্রি পেজ বানালে sitemap-এ যোগ করো।
4. Core Web Vitals চেক করতে থাকো (PageSpeed Insights)।
5. বাংলা + ইংরেজি কনটেন্ট থাকলে hreflang ট্যাগ পরে যোগ করা যায়।

সব পুশ করার পর আমাকে জানাও — আমি লাইভ সাইট চেক করে আরও সাজেস্ট করব।
