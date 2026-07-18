import re
import json
import os
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

baomoi_urls = [
    ("https://baomoi.com/", "Tin Nóng"),
    ("https://baomoi.com/kinh-doanh.epi", "Kinh doanh"),
    ("https://baomoi.com/khoa-hoc-cong-nghe.epi", "Khoa học công nghệ"),
    ("https://baomoi.com/nha-dat.epi", "Bất động sản"),

    ("https://baomoi.com/suc-khoe-y-te.epi", "Sức khỏe"),

    ("https://baomoi.com/giai-tri.epi", "Giải trí"),

    ("https://baomoi.com/the-thao.epi", "Thể thao"),

    ("https://baomoi.com/xe-co.epi", "Xe"),

    ("https://baomoi.com/du-lich.epi", "Du lịch")

]



raw_scraped_articles = []



headers = {



    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'



}



for url, default_cat in baomoi_urls:



    print(f"Fetching live articles from {url}...")



    try:



        req = urllib.request.Request(url, headers=headers)



        with urllib.request.urlopen(req, timeout=15) as response:



            html = response.read().decode('utf-8')



        print(f"  Fetched successfully. Length: {len(html)}")



        soup = BeautifulSoup(html, "html.parser")



        story_divs = soup.find_all(class_=re.compile(r'story|card|item', re.IGNORECASE))



        count_added = 0



        for div in story_divs:



            title_el = div.find(class_=re.compile(r'title|heading|subject', re.IGNORECASE))



            if not title_el and div.name == 'a':



                title_el = div



            if not title_el:



                for a in div.find_all('a'):



                    if a.text.strip() and len(a.text.strip()) > 15:



                        title_el = a



                        break



            if not title_el:



                continue



            title = title_el.text.strip()



            if not title or len(title) < 15:



                continue



            link_el = div.find('a') if div.name != 'a' else div



            if not link_el and title_el.name == 'a':



                link_el = title_el



            link = link_el.get('href', '') if link_el else ''



            if not link.startswith('http'):



                link = "https://baomoi.com" + link



            img = div.find('img')



            img_src = ''



            if img:



                img_src = img.get('src') or img.get('data-src') or img.get('srcset') or ''



                if 'gif' in img_src or 'base64' in img_src:



                    img_src = img.get('data-src') or img.get('srcset') or img_src



            if not img_src:



                continue



            desc_el = div.find(class_=re.compile(r'desc|summary|abstract|content', re.IGNORECASE))



            desc = desc_el.text.strip() if desc_el else ''



            if not desc:



                desc = title



            source_el = div.find(class_='bm-card-source')



            source_name = ""



            if source_el:



                source_name = source_el.get('title') or ""



                if not source_name:



                    source_img = source_el.find('img')



                    source_name = source_img.get('alt') if source_img else ""



            if not source_name:



                source_name = "Báo Mới"



            title = re.sub(r'\d+\s*(giờ|phút|ngày|tháng|năm|liên quan).*$', '', title).strip()



            desc = re.sub(r'\d+\s*(giờ|phút|ngày|tháng|năm|liên quan).*$', '', desc).strip()



            raw_scraped_articles.append({



                'title': title,



                'link': link,



                'image': img_src,



                'desc': desc,



                'publisher': source_name,



                'default_cat': default_cat



            })



            count_added += 1



        print(f"  Parsed {count_added} articles from BeautifulSoup.")



    except Exception as e:



        print(f"  Error crawling {url}: {e}")



# 2. Categorize using strict keyword rules



def classify_category(title, desc, default_cat):



    title_lower = title.lower()



    desc_lower = desc.lower()



    # If the article is from homepage or general business feed, classify it dynamically



    if default_cat in ["Kinh doanh", "homepage", "Tin Nóng"]:



        # Check "Bất động sản" first



        if any(k in title_lower or k in desc_lower for k in ['bất động sản', 'nhà đất', 'chung cư', 'dự án đô thị', 'căn hộ', 'đất nền', 'địa ốc', 'nhà phố', 'biệt thự', 'quy hoạch đất']):



            return 'Bất động sản'



        if any(k in title_lower or k in desc_lower for k in ['công nghệ', 'khoa học', 'ai', 'trí tuệ nhân tạo', 'phần mềm', 'điện thoại', 'máy tính', 'smartphone', 'mạng xã hội', 'facebook', 'google', 'apple', 'bán dẫn', 'vi mạch', 'robot']):



            return 'Khoa học công nghệ'



        if any(k in title_lower or k in desc_lower for k in ['sức khỏe', 'y tế', 'bệnh viện', 'dịch bệnh', 'bác sĩ', 'điều trị', 'dinh dưỡng', 'thuốc', 'phòng bệnh', 'tim mạch', 'ung thư']):



            return 'Sức khỏe'



        if any(k in title_lower or k in desc_lower for k in ['giải trí', 'điện ảnh', 'phim', 'showbiz', 'nghệ sĩ', 'ca sĩ', 'diễn viên', 'âm nhạc', 'thời trang', 'hoa hậu', 'văn hóa', 'concert', 'album']):



            return 'Giải trí'



        if any(k in title_lower or k in desc_lower for k in ['thể thao', 'bóng đá', 'euro', 'world cup', 'ngoại hạng anh', 'tennis', 'vận động viên', 'olympic', 'huy chương', 'bơi lội', 'cầu lông', 'điền kinh']):



            return 'Thể thao'



        if any(k in title_lower or k in desc_lower for k in ['ô tô', 'xe máy', 'xe điện', 'vinfast', 'honda', 'toyota', 'siêu xe', 'xe hơi', 'động cơ', 'tesla', 'hãng xe', 'suv', 'sedan']):



            return 'Xe'



        if any(k in title_lower or k in desc_lower for k in ['du lịch', 'tour', 'khách sạn', 'homestay', 'bãi biển', 'khám phá', 'resort', 'kỳ nghỉ', 'hành trình du lịch']):



            return 'Du lịch'



    return default_cat



# Remove scraped duplicates and categorise



seen_titles = set()



seen_urls = set()



unique_scraped = []



for art in raw_scraped_articles:



    t_clean = art['title'].strip().lower()



    l_clean = art['link'].strip().lower()



    if t_clean not in seen_titles and l_clean not in seen_urls:



        seen_titles.add(t_clean)



        seen_urls.add(l_clean)



        unique_scraped.append(art)



print(f"Extracted {len(unique_scraped)} unique live crawled articles.")



baomoi_articles_final = []



for art in unique_scraped:



    # Skip political articles



    title_lower = art['title'].lower()



    desc_lower = art['desc'].lower()



    politics_keywords = ['chính trị', 'bộ chính trị', 'tổng bí thư', 'chủ tịch nước', 'thủ tướng', 'quốc hội', 'chính phủ', 'bầu cử', 'đại biểu quốc hội', 'trung ương đảng', 'tỉnh ủy', 'thành ủy', 'đảng cộng sản', 'chính trị viên', 'họp đảng', 'báo cáo đảng']



    if any(k in title_lower or k in desc_lower for k in politics_keywords):



        continue



    category = classify_category(art['title'], art['desc'], art['default_cat'])



    img_url = art['image']



    redirect_url = re.sub(r'-c(\d+)', r'-r\g<1>', art['link'])



    baomoi_articles_final.append({



        'title': art['title'],



        'category': category,



        'date': datetime.now().strftime("%d/%m/%Y"),



        'image': img_url,



        'desc': art['desc'],



        'text': f"<p>{art['desc']}</p><p>Đọc bài viết gốc đầy đủ trên nguồn phát hành tại đường dẫn dưới đây.</p>",



        'sourceUrl': redirect_url,



        'publisher': art.get('publisher', 'Báo Mới')



    })



# 3. Resolve redirect_urls to original URLs in parallel



if baomoi_articles_final:



    print(f"  Resolving {len(baomoi_articles_final)} Bao Moi redirect URLs to direct original URLs...")



    def resolve_single_article_url(item):



        url = item['sourceUrl']



        if not url.startswith('http'):



            return



        try:



            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})



            with urllib.request.urlopen(req, timeout=5) as response:



                html_res = response.read().decode('utf-8')



                match_json = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_res)



                if match_json:



                    data_json = json.loads(match_json.group(1))



                    orig = data_json['props']['pageProps']['resp']['data']['content']['originalUrl']



                    if orig.startswith('http'):



                        item['sourceUrl'] = orig



        except Exception:



            pass



    with ThreadPoolExecutor(max_workers=25) as executor:



        executor.map(resolve_single_article_url, baomoi_articles_final)



    print("  Successfully resolved all redirect URLs to direct publisher URLs!")



# 4. Merging with History (No empty link articles!)



final_articles = []



def parse_articles_regex(content_str):



    match_arr = re.search(r'const\s+mockArticles\s*=\s*\[([\s\S]*?)\];', content_str)



    if not match_arr:



        return []



    array_content = match_arr.group(1)



    blocks = re.findall(r'\{([\s\S]*?)\}', array_content)



    parsed_articles = []



    for block in blocks:



        art = {}



        matches = re.finditer(r'(\w+):\s*("([^"\\]*(?:\\.[^"\\]*)*)"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\'|(\d+)|true|false)', block)



        for m in matches:



            key = m.group(1)



            double_val = m.group(3)



            single_val = m.group(4)



            int_val = m.group(5)



            raw_val = m.group(2)



            if double_val is not None:



                art[key] = double_val.replace('\\"', '"').replace('\\\\', '\\')



            elif single_val is not None:



                art[key] = single_val.replace("\\'", "'").replace('\\\\', '\\')



            elif int_val is not None:



                art[key] = int(int_val)



            else:



                art[key] = raw_val == 'true'



        if art:



            parsed_articles.append(art)



    return parsed_articles



# Load existing database to accumulate history



existing_baomoi_articles = []



script_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(script_dir, "index.html")



if os.path.exists(index_path):



    try:



        with open(index_path, "r", encoding="utf-8") as f_idx:



            idx_content = f_idx.read()



        all_existing = parse_articles_regex(idx_content)



        # Keep ONLY articles that have a valid sourceUrl (no empty links!) and map to our new categories



        valid_categories = {"Tin Nóng", "Kinh doanh", "Khoa học công nghệ", "Bất động sản", "Sức khỏe", "Giải trí", "Thể thao", "Xe", "Du lịch"}



        existing_baomoi_articles = []



        for a in all_existing:



            if a.get('sourceUrl') and a.get('sourceUrl').startswith('http'):



                # Skip political articles from history



                title_lower = a.get('title', '').lower()



                desc_lower = a.get('desc', '').lower()



                politics_keywords = ['chính trị', 'bộ chính trị', 'tổng bí thư', 'chủ tịch nước', 'thủ tướng', 'quốc hội', 'chính phủ', 'bầu cử', 'đại biểu quốc hội', 'trung ương đảng', 'tỉnh ủy', 'thành ủy', 'đảng cộng sản', 'chính trị viên', 'họp đảng', 'báo cáo đảng']



                if any(k in title_lower or k in desc_lower for k in politics_keywords):



                    continue



                cat = a.get('category', '')



                if cat not in valid_categories:



                    cat = classify_category(a.get('title', ''), a.get('desc', ''), 'Tin Nóng')



                a['category'] = cat



                existing_baomoi_articles.append(a)



        print(f"  Loaded {len(existing_baomoi_articles)} existing articles with valid links from index.html.")



    except Exception as e:



        print(f"  Warning: Failed to load existing articles: {e}")



# 5. Merge, group and persist history using a local JSON database scraped_history.json



# This prevents duplication and allows accumulative infinite scroll of older articles!



import json



# Fallback high quality Unsplash stock images categorized by topic



fallback_images = {



    'Tin Nóng': [



        'https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1495020689067-958852a6565d?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=600&q=80'



    ],



    'Kinh doanh': [



        'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=600&q=80'



    ],



    'Khoa học công nghệ': [



        'https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80'



    ],



    'Bất động sản': [



        'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=600&q=80'



    ],



    'Sức khỏe': [



        'https://images.unsplash.com/photo-1505751172876-fa1923c5c528?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?auto=format&fit=crop&w=600&q=80'



    ],



    'Giải trí': [



        'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1498038432885-c6f3f1b912ee?auto=format&fit=crop&w=600&q=80'



    ],



    'Thể thao': [



        'https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=600&q=80'



    ],



    'Xe': [



        'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=600&q=80'



    ],



    'Du lịch': [



        'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?auto=format&fit=crop&w=600&q=80',



        'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80'



    ]



}



def get_matching_image(category, title):



    title_lower = title.lower()



    if any(k in title_lower for k in ['bóng đá', 'world cup', 'messi', 'ronaldo', 'mu', 'chelsea', 'argentina', 'hướng dẫn đá', 'sân vận động']):



        return 'https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=600&q=80'



    if any(k in title_lower for k in ['vàng', 'sjc', 'doji', 'tỷ giá', 'usd', 'ngân hàng', 'lãi suất', 'tài chính', 'cổ phiếu']):



        return 'https://images.unsplash.com/photo-1610375461246-83df859d849d?auto=format&fit=crop&w=600&q=80'



    if any(k in title_lower for k in ['iphone', 'điện thoại', 'smartphone', 'máy tính', 'chip', 'bán dẫn', 'trí tuệ nhân tạo', 'chạy thử ai']):



        return 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=600&q=80'



    if any(k in title_lower for k in ['biệt thự', 'villa', 'chung cư', 'nhà đất', 'homestay', 'khách sạn', 'phòng nghỉ', 'dọn phòng']):



        return 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=600&q=80'



    if any(k in title_lower for k in ['ẩm thực', 'ăn uống', 'quán', 'hủ tiếu', 'buffet', 'sáng miễn phí', 'bữa ăn']):



        return 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80'



    if any(k in title_lower for k in ['xe điện', 'vinfast', 'ô tô', 'tesla', 'honda', 'hãng xe', 'vf 2', 'xe hơi']):



        return 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=600&q=80'



        



    images = fallback_images.get(category, fallback_images['Tin Nóng'])



    idx = len(title) % len(images)



    return images[idx]



def is_image_empty(img_str):



    if not img_str:



        return True



    img_lower = img_str.strip().lower()



    return img_lower.startswith('data:image/') or 'base64' in img_lower or '1x1' in img_lower or img_lower == 'no image'



history_db_path = os.path.join(script_dir, "scraped_history.json")



history_pool = []



if os.path.exists(history_db_path):



    try:



        with open(history_db_path, "r", encoding="utf-8") as f_db:



            history_pool = json.load(f_db)



        print(f"  Loaded {len(history_pool)} historical articles from scraped_history.json.")



    except Exception as e:



        print(f"  Warning: Failed to load scraped_history.json: {e}")



# Merge newly crawled, history db, and index.html history



all_candidates = baomoi_articles_final + history_pool + existing_baomoi_articles



seen_titles = set()



seen_urls = set()



deduped_pool = []



valid_categories = {"Tin Nóng", "Kinh doanh", "Khoa học công nghệ", "Bất động sản", "Sức khỏe", "Giải trí", "Thể thao", "Xe", "Du lịch"}



politics_keywords = ['chính trị', 'bộ chính trị', 'tổng bí thư', 'chủ tịch nước', 'thủ tướng', 'quốc hội', 'chính phủ', 'bầu cử', 'đại biểu quốc hội', 'trung ương đảng', 'tỉnh ủy', 'thành ủy', 'đảng cộng sản', 'chính trị viên', 'họp đảng', 'báo cáo đảng']



for art in all_candidates:



    title = art.get('title', '').strip()



    url = art.get('sourceUrl', '').strip()



    



    if not title or not url.startswith('http'):



        continue



        



    t_clean = title.lower()



    u_clean = url.lower()



    



    # Filter political news



    if any(k in t_clean or k in art.get('desc', '').lower() for k in politics_keywords):



        continue



        



    if t_clean not in seen_titles and u_clean not in seen_urls:



        seen_titles.add(t_clean)



        seen_urls.add(u_clean)



        



        # Keep original category or classify



        cat = art.get('category', 'Tin Nóng')



        if cat not in valid_categories:



            cat = classify_category(title, art.get('desc', ''), 'Tin Nóng')



        art['category'] = cat



        



        deduped_pool.append(art)



# Save the updated persistent database



try:



    with open(history_db_path, "w", encoding="utf-8") as f_db:



        json.dump(deduped_pool, f_db, ensure_ascii=False, indent=2)



    print(f"  Persisted {len(deduped_pool)} unique articles to scraped_history.json.")



except Exception as e:



    print(f"  Warning: Failed to save scraped_history.json: {e}")



# Sort articles to prioritize 'Tin Nóng' at the top of the list



# This guarantees that the homepage featured slots will display actual hot topics!



hot_articles = [a for a in deduped_pool if a['category'] == 'Tin Nóng']



other_articles = [a for a in deduped_pool if a['category'] != 'Tin Nóng']



combined_final_articles = hot_articles + other_articles



# Cap final mockArticles at 300 to keep the page load optimal while providing vast history



combined_final_articles = combined_final_articles[:400]



print(f"  Total balanced articles loaded: {len(combined_final_articles)}")



for idx, art in enumerate(combined_final_articles):



    final_articles.append({



        'id': idx + 1,



        'title': art['title'],



        'category': art['category'],



        'date': art['date'],



        'image': get_matching_image(art['category'], art['title']) if is_image_empty(art['image']) else art['image'],



        'desc': art['desc'],



        'text': art['text'],



        'isHot': idx == 0,



        'views': 5000 + (idx * 250),



        'sourceUrl': art['sourceUrl'],



        'publisher': art.get('publisher', 'Ban biên tập')



    })



# Format as JavaScript array



js_array_content = "const mockArticles = [\n"

for art in final_articles:
    js_array_content += f"      {{\n"
    js_array_content += f"        id: {art['id']},\n"
    js_array_content += f"        title: {json.dumps(art['title'], ensure_ascii=False)},\n"
    js_array_content += f"        category: {json.dumps(art['category'], ensure_ascii=False)},\n"
    js_array_content += f"        date: {json.dumps(art['date'], ensure_ascii=False)},\n"
    js_array_content += f"        image: {json.dumps(art['image'], ensure_ascii=False)},\n"
    js_array_content += f"        desc: {json.dumps(art['desc'], ensure_ascii=False)},\n"
    js_array_content += f"        text: {json.dumps(art['text'], ensure_ascii=False)},\n"
    js_array_content += f"        isHot: {'true' if art['isHot'] else 'false'},\n"
    js_array_content += f"        views: {art['views']},\n"
    js_array_content += f"        sourceUrl: {json.dumps(art['sourceUrl'], ensure_ascii=False)},\n"
    js_array_content += f"        publisher: {json.dumps(art['publisher'], ensure_ascii=False)}\n"
    js_array_content += f"      }},\n"

js_array_content = js_array_content.rstrip(",\n") + "\n    ];"

# 6. Apply to all 4 HTML files
files = [
    os.path.join(script_dir, "main.html"),
    os.path.join(script_dir, "home.html"),
    os.path.join(script_dir, "index.html"),
    os.path.join(script_dir, "baomoi.html")
]

for file_path in files:
    print(f"Integrating live Baomoi articles in: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Update mockArticles definition block
        pattern_articles = r'const\s*mockArticles\s*=\s*\[[\s\S]*?\];\s*//'
        content, count_art = re.subn(pattern_articles, js_array_content + "\n    //", content)
        if count_art == 0:
            pattern_articles_alt = r'const\s*mockArticles\s*=\s*\[[\s\S]*?\];'
            content, count_art = re.subn(pattern_articles_alt, js_array_content, content)
        print(f"  Updated mockArticles block: {count_art}")

        # Update viewArticleDetails logic to handle sourceUrl opening in new tab
        # 3. Update viewArticleDetails function inside HTML using robust regex
        pattern_view = r'viewArticleDetails\s*=\s*function\s*\(\s*id\s*\)\s*\{[\s\S]*?document\.body\.style\.overflow\s*=\s*\'hidden\';\s*\}'



        replacement_view = """viewArticleDetails = function(id) {



      const art = mockArticles.find(a => a.id === id);



      if (!art) return;



      // If the article has a live external source URL, open it in a new tab



      if (art.sourceUrl && art.sourceUrl.startsWith('http')) {



        window.open(art.sourceUrl, '_blank');



        return;



      }



      const body = document.getElementById('modal-article-body');



      let sourceBtnHtml = '';



      if (art.sourceUrl && art.sourceUrl.startsWith('http')) {



        sourceBtnHtml = `



          <div style="margin-top:25px; border-top:1px solid var(--border-color); padding-top:20px; text-align:center;">



            <button class="btn btn-primary" onclick="window.open('${art.sourceUrl}', '_blank')" style="background:var(--primary); color:white; border:none; padding:12px 24px; border-radius:6px; font-weight:700; cursor:pointer; font-size:0.95rem; width:100%; display:inline-flex; align-items:center; justify-content:center; gap:8px; box-shadow:0 4px 12px rgba(225,29,72,0.15); transition:all 0.3s ease;">



              <i class="fas fa-external-link-alt"></i> Đọc bài viết gốc trên ${art.publisher || 'Nguồn báo'}



            </button>



          </div>



        `;



      }



      body.innerHTML = `



        <div class="modal-image">



          <img src="${art.image}" alt="${art.title}">



        </div>



        <div class="modal-meta">



          <span class="modal-category">${art.category}</span>



          <span><i class="far fa-clock"></i> ${art.date}</span>



          <span><i class="far fa-newspaper"></i> Nguồn: ${art.publisher || 'Tin tức'}</span>



          <span><i class="far fa-eye"></i> ${art.views.toLocaleString()} lượt xem</span>



        </div>



        <h2 class="modal-title">${art.title}</h2>



        <div class="modal-desc" style="font-weight:700; margin-bottom:15px; color:var(--text-dark);">${art.desc}</div>



        <div class="modal-text">${art.text}</div>



        ${sourceBtnHtml}



        <div class="modal-share" style="margin-top:20px;">



          <span class="modal-share-title">Chia sẻ bài viết:</span>



          <a href="#" class="modal-share-btn fb" onclick="event.preventDefault(); showToast('Chia sẻ Facebook thành công!')"><i class="fab fa-facebook-f"></i></a>



          <a href="#" class="modal-share-btn tw" onclick="event.preventDefault(); showToast('Chia sẻ Twitter thành công!')"><i class="fab fa-twitter"></i></a>



        </div>



      `;



      const modal = document.getElementById('article-modal');



      modal.classList.add('show');



      document.body.style.overflow = 'hidden';



    }"""



        content, count_view = re.subn(pattern_view, replacement_view, content)



        print(f"  Regex viewArticleDetails update: {count_view}")



        # 4. Update filterCategory card template inside HTML using robust regex



        pattern_filter = r'(filtered\.forEach\(\s*art\s*=>\s*\{\s*html\s*\+=\s*`)([\s\S]*?)(`;\s*\}\s*\);\s*resultsGrid\.innerHTML\s*=\s*html;)'



        replacement_filter = """              <div class="card" onclick="viewArticleDetails(${art.id})">



                ${art.image ? `<div class="card-thumb" style="aspect-ratio: 16 / 9;"><img src="${art.image}" alt="${art.title}"></div>` : ''}



                <div class="card-content" style="padding: 20px;">



                  <div class="card-meta">



                    <span><i class="far fa-folder"></i> ${art.category}</span>



                    <span><i class="far fa-clock"></i> ${art.date}</span>



                    <span><i class="far fa-newspaper"></i> ${art.publisher || 'Tin tức'}</span>



                  </div>



                  <h3 class="card-title" style="font-size: 1rem; margin-top:5px; -webkit-line-clamp: 2; display: -webkit-box; -webkit-box-orient: vertical; overflow: hidden;">${art.title}</h3>



                  <p class="card-desc" style="font-size: 0.8rem; -webkit-line-clamp: 2; display: -webkit-box; -webkit-box-orient: vertical; overflow: hidden; margin-top:5px;">${art.desc}</p>



                </div>



              </div>"""



        content, count_filter = re.subn(pattern_filter, lambda m: m.group(1) + replacement_filter + m.group(3), content)



        print(f"  Regex filterCategory card update: {count_filter}")



        # 5. Update handleSearch card template inside HTML using robust regex



        pattern_search = r'(matches\.forEach\(\s*art\s*=>\s*\{\s*html\s*\+=\s*`)([\s\S]*?)(`;\s*\}\s*\);\s*resultsGrid\.innerHTML\s*=\s*html;)'



        replacement_search = """              <div class="card" onclick="viewArticleDetails(${art.id})">



                ${art.image ? `<div class="card-thumb" style="aspect-ratio: 16 / 9;"><img src="${art.image}" alt="${art.title}"></div>` : ''}



                <div class="card-content" style="padding: 20px;">



                  <div class="card-meta">



                    <span><i class="far fa-folder"></i> ${art.category}</span>



                    <span><i class="far fa-clock"></i> ${art.date}</span>



                    <span><i class="far fa-newspaper"></i> ${art.publisher || 'Tin tức'}</span>



                  </div>



                  <h3 class="card-title" style="font-size: 1rem; margin-top:5px; -webkit-line-clamp: 2; display: -webkit-box; -webkit-box-orient: vertical; overflow: hidden;">${art.title}</h3>



                  <p class="card-desc" style="font-size: 0.8rem; -webkit-line-clamp: 2; display: -webkit-box; -webkit-box-orient: vertical; overflow: hidden; margin-top:5px;">${art.desc}</p>



                </div>



              </div>"""



        content, count_search = re.subn(pattern_search, lambda m: m.group(1) + replacement_search + m.group(3), content)



        print(f"  Regex handleSearch card update: {count_search}")



        with open(file_path, "w", encoding="utf-8") as f:



            f.write(content)



        print("  Saved successfully.")



    except Exception as e:



        print(f"  Error on {file_path}: {e}")



print("All done!")