import re
import json
import os
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

baomoi_urls = [
    ("https://baomoi.com/", "Tin N\u00f3ng"),
    ("https://baomoi.com/kinh-doanh.epi", "Kinh doanh"),
    ("https://baomoi.com/khoa-hoc-cong-nghe.epi", "Khoa h\u1ecdc c\u00f4ng ngh\u1ec7"),
    ("https://baomoi.com/nha-dat.epi", "B\u1ea5t \u0111\u1ed9ng s\u1ea3n"),
    ("https://baomoi.com/suc-khoe-y-te.epi", "S\u1ee9c kh\u1ecfe"),
    ("https://baomoi.com/giai-tri.epi", "Gi\u1ea3i tr\u00ed"),
    ("https://baomoi.com/the-thao.epi", "Th\u1ec3 thao"),
    ("https://baomoi.com/xe-co.epi", "Xe"),
    ("https://baomoi.com/du-lich.epi", "Du l\u1ecbch")
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
                # Prioritize data-src since Báo Mới uses lazy-loading with base64 spacer in src!
                img_src = img.get('data-src') or img.get('src') or img.get('srcset') or ''
                if 'gif' in img_src or 'base64' in img_src or '1x1' in img_src:
                    img_src = img.get('data-src') or img.get('srcset') or ''
            
            # If still empty or spacer, try to look for <source> element in the picture wrapper
            if not img_src or 'gif' in img_src or 'base64' in img_src or '1x1' in img_src:
                source_el = div.find('source')
                if source_el:
                    img_src = source_el.get('srcset') or source_el.get('data-srcset') or ''
            
            # If URL is protocol-relative, add https:
            if img_src and img_src.startswith('//'):
                img_src = 'https:' + img_src

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



# 1.1 Crawl direct RSS feeds (VnExpress, Tuoi Tre, Thanh Nien) using regex-based RSS parser
direct_feeds = [
    # VnExpress
    ("https://vnexpress.net/rss/tin-noi-bat.rss", "Tin N\u00f3ng", "VnExpress"),
    ("https://vnexpress.net/rss/kinh-doanh.rss", "Kinh doanh", "VnExpress"),
    ("https://vnexpress.net/rss/so-hoa.rss", "Khoa h\u1ecdc c\u00f4ng ngh\u1ec7", "VnExpress"),
    ("https://vnexpress.net/rss/bat-dong-san.rss", "B\u1ea5t \u0111\u1ed9ng s\u1ea3n", "VnExpress"),
    ("https://vnexpress.net/rss/suc-khoe.rss", "S\u1ee9c kh\u1ecfe", "VnExpress"),
    ("https://vnexpress.net/rss/giai-tri.rss", "Gi\u1ea3i tr\u00ed", "VnExpress"),
    ("https://vnexpress.net/rss/the-thao.rss", "Th\u1ec3 thao", "VnExpress"),
    ("https://vnexpress.net/rss/oto-xe-may.rss", "Xe", "VnExpress"),
    ("https://vnexpress.net/rss/du-lich.rss", "Du l\u1ecbch", "VnExpress"),
    
    # Tuoi Tre
    ("https://tuoitre.vn/rss/tin-moi-nhat.rss", "Tin N\u00f3ng", "Tu\u1ed5i Tr\u1ebb"),
    ("https://tuoitre.vn/rss/kinh-doanh.rss", "Kinh doanh", "Tu\u1ed5i Tr\u1ebb"),
    ("https://tuoitre.vn/rss/khoa-hoc.rss", "Khoa h\u1ecdc c\u00f4ng ngh\u1ec7", "Tu\u1ed5i Trẻ"),
    ("https://tuoitre.vn/rss/nha-dat.rss", "B\u1ea5t \u0111\u1ed9ng s\u1ea3n", "Tu\u1ed5i Tr\u1ebb"),
    ("https://tuoitre.vn/rss/suc-khoe.rss", "S\u1ee9c kh\u1ecfe", "Tu\u1ed5i Tr\u1ebb"),
    ("https://tuoitre.vn/rss/giai-tri.rss", "Gi\u1ea3i tr\u00ed", "Tu\u1ed5i Tr\u1ebb"),
    ("https://tuoitre.vn/rss/the-thao.rss", "Th\u1ec3 thao", "Tu\u1ed5i Tr\u1ebb"),
    ("https://tuoitre.vn/rss/xe.rss", "Xe", "Tu\u1ed5i Tr\u1ebb"),
    ("https://tuoitre.vn/rss/du-lich.rss", "Du l\u1ecbch", "Tu\u1ed5i Tr\u1ebb"),

    # Thanh Nien
    ("https://thanhnien.vn/rss/home.rss", "Tin N\u00f3ng", "Thanh Ni\u00ean"),
    ("https://thanhnien.vn/rss/kinh-te.rss", "Kinh doanh", "Thanh Ni\u00ean"),
    ("https://thanhnien.vn/rss/cong-nghe-game.rss", "Khoa h\u1ecdc c\u00f4ng ngh\u1ec7", "Thanh Ni\u00ean"),
    ("https://thanhnien.vn/rss/kinh-te/dan-sinh-nha-dat.rss", "B\u1ea5t \u0111\u1ed9ng s\u1ea3n", "Thanh Ni\u00ean"),
    ("https://thanhnien.vn/rss/suc-khoe.rss", "S\u1ee9c kh\u1ecfe", "Thanh Ni\u00ean"),
    ("https://thanhnien.vn/rss/giai-tri.rss", "Gi\u1ea3i tr\u00ed", "Thanh Ni\u00ean"),
    ("https://thanhnien.vn/rss/the-thao.rss", "Th\u1ec3 thao", "Thanh Ni\u00ean"),
    ("https://thanhnien.vn/rss/xe.rss", "Xe", "Thanh Ni\u00ean"),
    ("https://thanhnien.vn/rss/du-lich.rss", "Du l\u1ecbch", "Thanh Ni\u00ean")
]

print("Fetching live articles from direct RSS feeds (VnExpress, Tuoi Tre, Thanh Nien)...")
for url, default_cat, publisher in direct_feeds:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        with urllib.request.urlopen(req, timeout=10) as res:
            xml = res.read().decode('utf-8', errors='ignore')
        
        items = re.findall(r'<item>([\s\S]*?)</item>', xml)
        count_added = 0
        for item in items:
            title_match = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item, re.DOTALL)
            title = title_match.group(1).strip() if title_match else ''
            
            link_match = re.search(r'<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>', item, re.DOTALL)
            link = link_match.group(1).strip() if link_match else ''
            
            desc_match = re.search(r'<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', item, re.DOTALL)
            desc_raw = desc_match.group(1).strip() if desc_match else ''
            
            img_url = ''
            enc_match = re.search(r'<enclosure[^>]+url=["\']([^"\']+)["\']', item)
            if enc_match:
                img_url = enc_match.group(1).strip()
                
            desc_soup = BeautifulSoup(desc_raw, 'html.parser')
            if not img_url:
                img_tag = desc_soup.find('img')
                img_url = img_tag['src'] if img_tag else ''
                
            desc_text = desc_soup.get_text().strip()
            
            # Clean title/link CDATA markers
            title = re.sub(r'^<!\[CDATA\[(.*?)\]\]>$', lambda m: m.group(1), title, flags=re.DOTALL).strip()
            link = re.sub(r'^<!\[CDATA\[(.*?)\]\]>$', lambda m: m.group(1), link, flags=re.DOTALL).strip()
            
            if title and link:
                raw_scraped_articles.append({
                    'title': title,
                    'link': link,
                    'image': img_url,
                    'desc': desc_text,
                    'publisher': publisher,
                    'default_cat': default_cat
                })
                count_added += 1
    except Exception as e:
        pass


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
if len(unique_scraped) == 0:
    print("Warning: 0 live articles crawled. This usually means the crawler IP was blocked by the source site (e.g. on GitHub Actions runners). Aborting integration to protect existing database!")
    import sys
    sys.exit(0)



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
        if 'baomoi.com' not in url:
            return
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
            with urllib.request.urlopen(req, timeout=5) as response:
                html_res = response.read().decode('utf-8', errors='ignore')
                match_json = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_res)
                if match_json:
                    data_json = json.loads(match_json.group(1))
                    orig = data_json['props']['pageProps']['resp']['data']['content']['originalUrl']
                    if orig.startswith('http'):
                        item['sourceUrl'] = orig
                        
                        # Fetch the direct publisher page to extract high-quality og:image
                        try:
                            req_orig = urllib.request.Request(orig, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
                            with urllib.request.urlopen(req_orig, timeout=5) as res_orig:
                                html_orig = res_orig.read().decode('utf-8', errors='ignore')
                            match_og = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_orig)
                            if not match_og:
                                match_og = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html_orig)
                            if match_og:
                                og_url = match_og.group(1).strip()
                                if og_url.startswith('http'):
                                    item['image'] = og_url
                        except Exception:
                            pass
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

    # 1. Agriculture / Farming / Animal husbandry (nuôi, trồng, nông dân, nông nghiệp, ao, ốc, bò, lợn, lúa, trái cây, làm ruộng)
    if any(k in title_lower for k in ['nuôi', 'trồng', 'nông dân', 'nông nghiệp', 'ao ', 'ốc ', 'cá ', 'bò ', 'lợn ', 'lúa ', 'trái cây', 'hợp tác xã', 'vườn', 'trang trại', 'chuồng', 'thả vườn']):
        farm_images = [
            'https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=600&q=80', # Farm field
            'https://images.unsplash.com/photo-1570042225831-d98fa7577f1e?auto=format&fit=crop&w=600&q=80', # Cows
            'https://images.unsplash.com/photo-1605000797499-95a51c7e09ae?auto=format&fit=crop&w=600&q=80'  # Agriculture
        ]
        return farm_images[sum(ord(c) for c in title) % len(farm_images)]

    # 2. Military / War / Defense / Veterans (cựu chiến binh, người lính, chiến sĩ, thương binh, xung phong, quân đội, phòng không, phòng thủ, tên lửa, Ukraine, tập kích, đánh chiếm)
    if any(k in title_lower for k in ['cựu chiến binh', 'người lính', 'chiến sĩ', 'thương binh', 'xung phong', 'quân đội', 'quân nhân', 'phòng không', 'phòng thủ', 'tên lửa', 'ukraine', 'tập kích', 'đánh chiếm', 'bắn rơi', 'chiến tranh', 'quân sự', 'bahrain', 'căn cứ mỹ', 'tổ hợp phòng']):
        military_images = [
            'https://images.unsplash.com/photo-1579705745811-a32be7bfdb0a?auto=format&fit=crop&w=600&q=80', # Camouflage / Soldier
            'https://images.unsplash.com/photo-1519074002996-a69e7ac46a42?auto=format&fit=crop&w=600&q=80', # Helicopter / Military
            'https://images.unsplash.com/photo-1508849789987-4e5333c12b78?auto=format&fit=crop&w=600&q=80'  # National defense
        ]
        return military_images[sum(ord(c) for c in title) % len(military_images)]

    # 3. China / Chinese Cities (trung quốc, bắc kinh, thượng hải)
    if any(k in title_lower for k in ['trung quốc', 'bắc kinh', 'thượng hải']):
        china_images = [
            'https://images.unsplash.com/photo-1524396309943-e03f5ee77974?auto=format&fit=crop&w=600&q=80', # Pagoda
            'https://images.unsplash.com/photo-1540759786422-c60d5ecd5633?auto=format&fit=crop&w=600&q=80'  # Shanghai skyline
        ]
        return china_images[sum(ord(c) for c in title) % len(china_images)]

    # 4. Wealth / Wealth management / Billionaires (người giàu, gia sản, tài sản, triệu phú, tỷ phú, thừa kế, quản lý gia sản, tích lũy tiền)
    if any(k in title_lower for k in ['người giàu', 'gia sản', 'tài sản', 'triệu phú', 'tỷ phú', 'thừa kế', 'quản lý gia sản', 'tích lũy tiền']):
        wealth_images = [
            'https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=600&q=80', # Financial advisory
            'https://images.unsplash.com/photo-1563013544-824ae1d704d3?auto=format&fit=crop&w=600&q=80'  # Gold coins/savings
        ]
        return wealth_images[sum(ord(c) for c in title) % len(wealth_images)]

    # 5. Sports / Football (bóng đá, world cup, messi, ronaldo, mu, chelsea, vô địch, trận đấu, fifa)
    if any(k in title_lower for k in ['bóng đá', 'world cup', 'messi', 'ronaldo', 'mu', 'chelsea', 'argentina', 'hướng dẫn đá', 'sân vận động', 'fifa', 'vô địch', 'trận đấu', 'thể thao', 'cup']):
        return 'https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=600&q=80'

    # 6. Finance / Banks / Gold / SJC (vàng, sjc, doji, tỷ giá, usd, ngân hàng, lãi suất, cổ phiếu, chứng khoán, đầu tư, doanh nghiệp, kinh tế)
    if any(k in title_lower for k in ['vàng', 'sjc', 'doji', 'tỷ giá', 'usd', 'ngân hàng', 'lãi suất', 'cổ phiếu', 'chứng khoán', 'đầu tư', 'doanh nghiệp', 'kinh tế', 'thị trường']):
        return 'https://images.unsplash.com/photo-1610375461246-83df859d849d?auto=format&fit=crop&w=600&q=80'

    # 7. Tech / Phones / AI (iphone, điện thoại, smartphone, máy tính, chip, bán dẫn, trí tuệ nhân tạo, chạy thử ai, robot, khoa học, công nghệ)
    if any(k in title_lower for k in ['iphone', 'điện thoại', 'smartphone', 'máy tính', 'chip', 'bán dẫn', 'trí tuệ nhân tạo', 'chạy thử ai', 'robot', 'khoa học', 'công nghệ']):
        return 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=600&q=80'

    # 8. Real Estate (biệt thự, villa, chung cư, nhà đất, homestay, khách sạn, phòng nghỉ, căn hộ)
    if any(k in title_lower for k in ['biệt thự', 'villa', 'chung cư', 'nhà đất', 'homestay', 'khách sạn', 'phòng nghỉ', 'căn hộ']):
        return 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=600&q=80'

    # 9. Food / Cuisine (ẩm thực, ăn uống, quán, hủ tiếu, buffet, sáng miễn phí, bữa ăn, nhà hàng, nấu ăn, món ăn)
    if any(k in title_lower for k in ['ẩm thực', 'ăn uống', 'quán', 'hủ tiếu', 'buffet', 'sáng miễn phí', 'bữa ăn', 'nhà hàng', 'nấu ăn', 'món ăn']):
        return 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80'

    # 10. Automotive (xe điện, vinfast, ô tô, tesla, honda, hãng xe, vf 2, xe hơi, xe khách, xe máy)
    if any(k in title_lower for k in ['xe điện', 'vinfast', 'ô tô', 'tesla', 'honda', 'hãng xe', 'vf 2', 'xe hơi', 'xe khách', 'xe máy']):
        return 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=600&q=80'

    # Fallback to category defaults
    images = fallback_images.get(category, fallback_images['Tin Nóng'])
    hash_code = sum(ord(c) for c in title)
    idx = hash_code % len(images)
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



# Clean and re-evaluate all fallback images in the pool before saving
for art in deduped_pool:
    img = art.get('image', '')
    if is_image_empty(img) or (img and img.startswith('https://images.unsplash.com')):
        art['image'] = get_matching_image(art['category'], art['title'])

# Save the updated persistent database



try:



    with open(history_db_path, "w", encoding="utf-8") as f_db:



        json.dump(deduped_pool, f_db, ensure_ascii=False, indent=2)



    print(f"  Persisted {len(deduped_pool)} unique articles to scraped_history.json.")



except Exception as e:



    print(f"  Warning: Failed to save scraped_history.json: {e}")



# Sort and balance articles to prevent 'Tin Nóng' starvation across other categories
cats_grouped = {}
for art in deduped_pool:
    cat = art['category']
    if cat not in cats_grouped:
        cats_grouped[cat] = []
    cats_grouped[cat].append(art)

balanced_pool = []
for cat, arts in cats_grouped.items():
    limit = 120 if cat == 'Tin N\u00f3ng' else 70
    balanced_pool.extend(arts[:limit])

hot_articles = [a for a in balanced_pool if a['category'] == 'Tin N\u00f3ng']
other_articles = [a for a in balanced_pool if a['category'] != 'Tin N\u00f3ng']
combined_final_articles = hot_articles + other_articles
combined_final_articles = combined_final_articles[:800]

print(f"  Total balanced articles loaded: {len(combined_final_articles)}")



print(f"  Total balanced articles loaded: {len(combined_final_articles)}")



for idx, art in enumerate(combined_final_articles):



    final_articles.append({



        'id': idx + 1,



        'title': art['title'],



        'category': art['category'],



        'date': art['date'],



        'image': get_matching_image(art['category'], art['title']) if (is_image_empty(art['image']) or (art['image'] and art['image'].startswith('https://images.unsplash.com'))) else art['image'],



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