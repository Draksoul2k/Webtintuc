import urllib.request
from bs4 import BeautifulSoup
import re
import json

# 1. Fetch baomoi.com
url = "https://baomoi.com/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print("Fetching live articles from baomoi.com...")
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        html = response.read().decode('utf-8')
    print("Fetched successfully. Length:", len(html))
except Exception as e:
    print(f"Error fetching: {e}")
    html = ""

# 2. Parse articles
parsed_articles = []
if html:
    soup = BeautifulSoup(html, "html.parser")
    story_divs = soup.find_all(class_=re.compile(r'story|card|item', re.IGNORECASE))
    
    for div in story_divs:
        # Extract title
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
            
        # Get link
        link_el = div.find('a') if div.name != 'a' else div
        if not link_el and title_el.name == 'a':
            link_el = title_el
        link = link_el.get('href', '') if link_el else ''
        if not link.startswith('http'):
            link = "https://baomoi.com" + link
            
        # Get image
        img = div.find('img')
        img_src = ''
        if img:
            img_src = img.get('src') or img.get('data-src') or img.get('srcset') or ''
            if 'gif' in img_src or 'base64' in img_src:
                img_src = img.get('data-src') or img.get('srcset') or img_src
        
        if not img_src:
            continue  # Skip articles without images to satisfy "nhiều bài viết có ảnh"
            
        # Get description
        desc_el = div.find(class_=re.compile(r'desc|summary|abstract|content', re.IGNORECASE))
        desc = desc_el.text.strip() if desc_el else ''
        if not desc:
            desc = title
            
        # Clean title & desc
        title = re.sub(r'\d+\s*(giờ|phút|ngày|tháng|năm|liên quan).*$', '', title).strip()
        desc = re.sub(r'\d+\s*(giờ|phút|ngày|tháng|năm|liên quan).*$', '', desc).strip()
        
        parsed_articles.append({
            'title': title,
            'link': link,
            'image': img_src,
            'desc': desc
        })

# Remove duplicates
seen_titles = set()
unique_baomoi = []
for art in parsed_articles:
    if art['title'] not in seen_titles:
        seen_titles.add(art['title'])
        unique_baomoi.append(art)

print(f"Extracted {len(unique_baomoi)} unique articles with images.")

# 3. Choose the top 20 Báo Mới articles and categorize them dynamically
baomoi_articles_final = []
categories_pool = ["Giải trí", "Sức khỏe", "Photo", "Video", "Infographic", "Longform"]
for idx, art in enumerate(unique_baomoi[:20]):
    title_lower = art['title'].lower()
    
    # Classify based on keyword or index
    category = "Giải trí"
    if "sức khỏe" in title_lower or "y học" in title_lower or "bệnh" in title_lower or "thuốc" in title_lower or "dịch" in title_lower:
        category = "Sức khỏe"
    elif "ảnh" in title_lower or "chùm ảnh" in title_lower:
        category = "Photo"
    elif "video" in title_lower or "clip" in title_lower:
        category = "Video"
    elif "infographic" in title_lower:
        category = "Infographic"
    elif "chuyên sâu" in title_lower or "longform" in title_lower or len(art['title']) > 55:
        category = "Longform"
    else:
        # Distribute remaining articles across the categories
        category = categories_pool[idx % len(categories_pool)]
        
    baomoi_articles_final.append({
        'title': art['title'],
        'category': category,
        'date': "11/07/2026",
        'image': art['image'],
        'desc': art['desc'],
        'text': f"<p>{art['desc']}</p><p>Đọc bài viết gốc đầy đủ trên Báo Mới tại đường dẫn dưới đây.</p>",
        'sourceUrl': art['link']
    })

# 4. Mix with Hưng Yên local articles (20 articles)
hungyen_articles = [
    {
        "title": "Lễ hội văn hóa dân gian Phố Hiến: Nét đẹp di sản tâm linh xứ nhãn Hưng Yên",
        "category": "Di tích",
        "date": "10/07/2026",
        "image": "https://images.unsplash.com/photo-1590001155093-a3c66ab0c3ff?auto=format&fit=crop&w=800&q=80",
        "desc": "Lễ hội dân gian Phố Hiến tôn vinh những giá trị lịch sử độc đáo từ thời kỳ thương cảng sầm uất đệ nhị danh lam kinh kỳ Bắc Bộ.",
        "text": "<p><strong>Phố Hiến</strong> từng được mệnh danh là thương cảng sầm uất bậc nhất nước ta vào thế kỷ XVI-XVII... (xem chi tiết ở bản đồ văn hóa Hưng Yên)</p>",
        "sourceUrl": ""
    },
    {
        "title": "Nhãn lồng tiến vua Hưng Yên: Tinh hoa đặc sản ngọt ngào nổi tiếng gần xa",
        "category": "Đặc sản",
        "date": "09/07/2026",
        "image": "https://images.unsplash.com/photo-1619890831007-aa154f36df27?auto=format&fit=crop&w=800&q=80",
        "desc": "Mùa nhãn chín rộ khắp các nhà vườn Hưng Yên, mang lại quả nhãn lồng cùi dày ngọt lịm danh bất hư truyền.",
        "text": "<p>Nói đến Hưng Yên không thể không nhắc đến nhãn lồng tiến vua...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Chùa Chuông Hưng Yên: Mệnh danh đệ nhất danh lam cổ kính xứ Bắc",
        "category": "Di tích",
        "date": "08/07/2026",
        "image": "https://images.unsplash.com/photo-1590001155093-a3c66ab0c3ff?auto=format&fit=crop&w=800&q=80",
        "desc": "Chùa Chuông cổ kính mang vẻ tĩnh lặng uy nghiêm cùng hệ thống tượng Phật điêu khắc cực kỳ đặc sắc.",
        "text": "<p>Tọa lạc tại phường Hiến Nam, Chùa Chuông là đệ nhất danh lam của xứ Bắc...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Đặc sản tương Bần Hưng Yên: Tinh hoa ẩm thực hồn quê Việt",
        "category": "Đặc sản",
        "date": "07/07/2026",
        "image": "https://images.unsplash.com/photo-1596797038530-2c107229654b?auto=format&fit=crop&w=800&q=80",
        "desc": "Tương Bần Hưng Yên ngọt đậm, thơm bùi, là loại gia vị truyền thống chấm gì cũng ngon nổi tiếng từ xưa.",
        "text": "<p>Tương Bần Mỹ Hào được chế biến rất công phu và là niềm tự hào ẩm thực...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Làng nghề làm hương trầm Thôn Cao nhộn nhịp những ngày giáp Tết",
        "category": "Làng nghề",
        "date": "06/07/2026",
        "image": "https://images.unsplash.com/photo-1508807526345-15e98834cca0?auto=format&fit=crop&w=800&q=80",
        "desc": "Làng nghề làm hương trầm Thôn Cao rực rỡ sắc đỏ vàng của các bó hương phơi nắng chuẩn bị cho vụ Tết.",
        "text": "<p>Hương trầm Thôn Cao nổi tiếng thơm thanh khiết tự nhiên và an toàn sức khỏe...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Danh nhân y học Hải Thượng Lãn Ông Lê Hữu Trác và dấu ấn tại Hưng Yên",
        "category": "Danh nhân",
        "date": "05/07/2026",
        "image": "https://images.unsplash.com/photo-1590001155093-a3c66ab0c3ff?auto=format&fit=crop&w=800&q=80",
        "desc": "Cuộc đời và sự nghiệp y đức cả của đại danh y Hải Thượng Lãn Ông Lê Hữu Trác gắn liền với quê hương Hưng Yên.",
        "text": "<p>Lê Hữu Trác sinh tại huyện Yên Mỹ, là ông tổ của đông y học cổ truyền Việt Nam...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Khai mạc Lễ hội văn hóa truyền thống Phố Hiến năm 2026",
        "category": "Di tích",
        "date": "04/07/2026",
        "image": "https://images.unsplash.com/photo-1590001155093-a3c66ab0c3ff?auto=format&fit=crop&w=800&q=80",
        "desc": "Lễ hội tái hiện không gian văn hóa cảng thị sầm uất xưa với nhiều trò chơi dân gian hấp dẫn.",
        "text": "<p>Tái hiện lại thương cảng sầm uất Phố Hiến cổ kính thời nhà Lê...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Hưng Yên đẩy mạnh chuyển đổi số trong phát triển vườn nhãn lồng đặc sản",
        "category": "Sức khỏe",
        "date": "03/07/2026",
        "image": "https://images.unsplash.com/photo-1619890831007-aa154f36df27?auto=format&fit=crop&w=800&q=80",
        "desc": "Ứng dụng quét mã QR truy xuất nguồn gốc và bán hàng thương mại điện tử giúp nhãn lồng nâng cao giá trị.",
        "text": "<p>Bà con Khoái Châu nhiệt liệt ứng dụng mã QR cho cây nhãn lồng...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Chùm ảnh: Cánh đồng hoa cải Văn Giang rực rỡ sắc vàng mê đắm",
        "category": "Photo",
        "date": "02/07/2026",
        "image": "https://images.unsplash.com/photo-1536257130722-ea1c983d7365?auto=format&fit=crop&w=800&q=80",
        "desc": "Cánh đồng hoa cải vàng rực bên bờ sông Hồng trở thành địa điểm check-in lý tưởng hút hồn giới trẻ du lịch.",
        "text": "<p>Mỗi dịp đông về, cải vàng nở rực rỡ cả triền đê Văn Giang thơ mộng...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Khám phá vẻ đẹp yên bình của Đền Mẫu Hưng Yên bên hồ Bán Nguyệt",
        "category": "Di tích",
        "date": "01/07/2026",
        "image": "https://images.unsplash.com/photo-1590001155093-a3c66ab0c3ff?auto=format&fit=crop&w=800&q=80",
        "desc": "Đền Mẫu Hưng Yên nổi tiếng linh thiêng sơn thủy hữu tình giữa lòng thành phố Hưng Yên cổ kính.",
        "text": "<p>Đền Mẫu thờ Dương Quý Phi, toạ lạc cạnh hồ Bán Nguyệt lộng gió...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Lễ dâng hương tưởng niệm các vị khoa bảng tại Văn Miếu Xích Đằng",
        "category": "Di tích",
        "date": "30/06/2026",
        "image": "https://images.unsplash.com/photo-1590001155093-a3c66ab0c3ff?auto=format&fit=crop&w=800&q=80",
        "desc": "Hoạt động ý nghĩa nhằm tôn vinh truyền thống hiếu học và khoa bảng vẻ vang của quê hương Hưng Yên.",
        "text": "<p>Tôn vinh 9 bia tiến sĩ khoa bảng lừng lẫy tại Văn Miếu Xích Đằng...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Cách làm long nhãn sấy khô truyền thống của người dân Phố Hiến",
        "category": "Đặc sản",
        "date": "29/06/2026",
        "image": "https://images.unsplash.com/photo-1619890831007-aa154f36df27?auto=format&fit=crop&w=800&q=80",
        "desc": "Bí quyết lựa chọn trái nhãn tươi, tách cùi sấy khô bằng lửa củi để giữ hương thơm đặc trưng.",
        "text": "<p>Sấy long nhãn bằng lửa củi giúp hương thơm giữ được bền lâu dịu nhẹ...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Thưởng thức món ếch om Phượng Tường - Đặc sản tiến vua độc đáo",
        "category": "Đặc sản",
        "date": "28/06/2026",
        "image": "https://images.unsplash.com/photo-1619890831007-aa154f36df27?auto=format&fit=crop&w=800&q=80",
        "desc": "Hương vị béo ngọt của thịt ếch đồng hòa quyện với nước dùng sánh đặc kiểu truyền thống độc nhất vô nhị.",
        "text": "<p>Món ăn tiến vua trứ danh vùng Phượng Tường Khoái Châu...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Chả gà Tiểu Quan - Món ăn truyền thống nức tiếng vùng đất Hưng Yên",
        "category": "Đặc sản",
        "date": "27/06/2026",
        "image": "https://images.unsplash.com/photo-1619890831007-aa154f36df27?auto=format&fit=crop&w=800&q=80",
        "desc": "Chả gà giã tay nướng bằng than hoa thơm lừng, dai giòn đậm đà, món ăn không thể thiếu trên mâm cỗ.",
        "text": "<p>Chả gà Tiểu Quan nướng than hoa thơm nức mũi ngày Tết đoàn viên...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Làng nghề đúc đồng Lộng Thượng giữ lửa nghề truyền thống trăm năm",
        "category": "Làng nghề",
        "date": "26/06/2026",
        "image": "https://images.unsplash.com/photo-1508807526345-15e98834cca0?auto=format&fit=crop&w=800&q=80",
        "desc": "Các nghệ nhân làng nghề đúc đồng Lộng Thượng tỉ mẩn thổi hồn vào từng sản phẩm đồng mỹ nghệ tinh xảo.",
        "text": "<p>Nghề đúc đồng cổ truyền gìn giữ tinh hoa rèn đúc hàng trăm năm qua...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Khai trương tuyến phố đi bộ Phố Hiến phục vụ người dân và du khách",
        "category": "Di tích",
        "date": "25/06/2026",
        "image": "https://images.unsplash.com/photo-1528605248644-14dd04022da1?auto=format&fit=crop&w=800&q=80",
        "desc": "Không gian đi bộ mới tại Phố Cổ Hiến Nam mang lại nhiều hoạt động vui chơi giải trí lành mạnh dịp cuối tuần.",
        "text": "<p>Mở tuyến phố đi bộ giúp tăng thêm hoạt động kinh doanh mua bán địa phương...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Bánh răng bừa Thiên Phiến: Thức quà quê giản dị nức lòng người xứ Nhãn",
        "category": "Đặc sản",
        "date": "24/06/2026",
        "image": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80",
        "desc": "Chiếc bánh lá tẻ mộc mạc thơm dẻo mùi bột tẻ cùng nhân thịt mộc nhĩ giòn bùi làm say đắm lòng thực khách.",
        "text": "<p>Bánh răng bừa bột gạo tẻ gói lá dong thơm ngon nổi tiếng...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Làng nghề làm nón lá Nghĩa Trụ nhộn nhịp quanh năm giữ gìn nét duyên Việt",
        "category": "Làng nghề",
        "date": "23/06/2026",
        "image": "https://images.unsplash.com/photo-1508807526345-15e98834cca0?auto=format&fit=crop&w=800&q=80",
        "desc": "Làng Nghĩa Trụ, Văn Giang lưu giữ nghề làm nón lá truyền thống hàng trăm năm, tôn vinh chiếc nón duyên dáng Việt Nam.",
        "text": "<p>Khâu nón lá Nghĩa Trụ che nắng che mưa mộc mạc duyên dáng...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Tác dụng bảo vệ tim mạch và bổ máu bất ngờ từ đặc sản hạt sen Hưng Yên",
        "category": "Sức khỏe",
        "date": "22/06/2026",
        "image": "https://images.unsplash.com/photo-1619890831007-aa154f36df27?auto=format&fit=crop&w=800&q=80",
        "desc": "Nghiên cứu y học cho thấy hạt sen khô đất nhãn giàu chất chống oxy hóa, hỗ trợ giấc ngủ và bảo vệ tim mạch rất tốt.",
        "text": "<p>Hạt sen bổ khí huyết, an thần ngủ cực ngon bùi mát bổ dưỡng...</p>",
        "sourceUrl": ""
    },
    {
        "title": "Vẻ đẹp thanh bình của làng cổ Đông Hòa những ngày nắng đẹp",
        "category": "Photo",
        "date": "21/06/2026",
        "image": "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?auto=format&fit=crop&w=800&q=80",
        "desc": "Mái ngói rêu phong, con đường gạch đỏ xưa cũ và giếng nước gốc đa bình yên của làng quê Hưng Yên.",
        "text": "<p>Nhịp sống thanh bình làng quê cổ Kinh Bắc xưa cũ...</p>",
        "sourceUrl": ""
    }
]

# 5. Merge databases into exactly 40 articles
final_articles = []
for idx, art in enumerate(baomoi_articles_final + hungyen_articles):
    final_articles.append({
        'id': idx + 1,
        'title': art['title'],
        'category': art['category'],
        'date': art['date'],
        'image': art['image'],
        'desc': art['desc'],
        'text': art['text'],
        'isHot': idx == 0,
        'views': 5000 + (idx * 250),
        'sourceUrl': art['sourceUrl']
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
    js_array_content += f"        sourceUrl: {json.dumps(art['sourceUrl'], ensure_ascii=False)}\n"
    js_array_content += f"      }},\n"
js_array_content = js_array_content.rstrip(",\n") + "\n    ];"

# 6. Apply to all 4 HTML files
files = [
    r"d:\Xây web\hungyen_24h\main.html",
    r"d:\Xây web\hungyen_24h\home.html",
    r"d:\Xây web\hungyen_24h\index.html",
    r"d:\Xây web\hungyen_24h\baomoi.html"
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
        old_view_details = """    viewArticleDetails = function(id) {
      const art = mockArticles.find(a => a.id === id);
      if (!art) return;

      const body = document.getElementById('modal-article-body');"""

        new_view_details = """    viewArticleDetails = function(id) {
      const art = mockArticles.find(a => a.id === id);
      if (!art) return;

      // If the article has a live external source URL from Báo Mới, open it in a new tab
      if (art.sourceUrl && art.sourceUrl.startsWith('http')) {
        window.open(art.sourceUrl, '_blank');
        return;
      }

      const body = document.getElementById('modal-article-body');"""

        if old_view_details in content:
            content = content.replace(old_view_details, new_view_details)
            print("  Updated viewArticleDetails event listener for external tabs!")
        else:
            # Try matching with regex
            pattern_view = r'viewArticleDetails\s*=\s*function\s*\(\s*id\s*\)\s*\{\s*const\s*art\s*=\s*mockArticles\.find\(\s*a\s*=>\s*a\.id\s*===\s*id\s*\);\s*if\s*\(\s*!art\s*\)\s*return;\s*const\s*body\s*='
            replacement_view = """viewArticleDetails = function(id) {
      const art = mockArticles.find(a => a.id === id);
      if (!art) return;

      // If the article has a live external source URL from Báo Mới, open it in a new tab
      if (art.sourceUrl && art.sourceUrl.startsWith('http')) {
        window.open(art.sourceUrl, '_blank');
        return;
      }

      const body = """
            content, count_view = re.subn(pattern_view, replacement_view, content)
            print(f"  Regex viewArticleDetails update: {count_view}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("  Saved successfully.")
    except Exception as e:
        print(f"  Error on {file_path}: {e}")

print("All done!")
