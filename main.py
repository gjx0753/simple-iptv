import re
import requests

def fetch_raw_m3u(url):
    print(f"Fetching: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def extract_entries(m3u_text, keywords):
    """提取匹配关键字的频道行"""
    entries = []
    if not m3u_text:
        return entries
    lines = m3u_text.strip().splitlines()
    for i in range(len(lines)):
        line = lines[i].strip()
        # 匹配关键字
        if line.startswith('#EXTINF') and any(k in line for k in keywords):
            if i + 1 < len(lines):
                url_line = lines[i + 1].strip()
                if url_line and not url_line.startswith('#'):
                    entries.append(line)
                    entries.append(url_line)
    return entries

def get_auto_group(channel_name):
    """根据频道名自动推断分组"""
    name = channel_name.lower()
    if "cctv" in name or "央视" in name or "cgtn" in name:
        return "央视频道"
    elif "卫视" in name:
        return "卫视频道"
    elif "bbc" in name or "cnn" in name or "nhk" in name:
        return "国际频道"
    elif "新闻" in name:
        return "新闻频道"
    elif "体育" in name:
        return "体育频道"
    elif "影视" in name or "电影" in name:
        return "影视频道"
    elif "翡翠" in name or "本港" in name or "明珠" in name:
        return "港澳频道"
    elif "台视" in name or "中天" in name or "民视" in name or "三立" in name or "tvbs" in name:
        return "台湾频道"
    else:
        return "其他频道"

def parse_m3u_to_struct(lines):
    """
    将 M3U 文本行解析为结构化列表
    返回: [{"name": "频道名", "url": "地址", "group": "分组名"}, ...]
    """
    channels = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('#EXTINF'):
            # 1. 提取频道名 (逗号后面的内容)
            channel_name = "未知频道"
            if ',' in line:
                channel_name = line.split(',')[-1].strip()
            
            # 2. 尝试提取 group-title (双引号内的内容)
            group_name = None
            match = re.search(r'group-title="([^"]*)"', line)
            if match:
                group_name = match.group(1)
            
            # 3. 获取 URL
            url = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith('#'):
                    url = next_line
            
            if url:
                # 如果没有提取到 group-title，则根据频道名自动推断
                final_group = group_name if group_name else get_auto_group(channel_name)
                channels.append({
                    "name": channel_name,
                    "url": url,
                    "group": final_group
                })
                i += 2 # 跳过 URL 行
                continue
        i += 1
    
    return channels

if __name__ == '__main__':
    # 1. 获取完整源
    url_full = 'https://raw.githubusercontent.com/fanmingming/live/refs/heads/main/tv/m3u/ipv6.m3u'
    full_m3u = fetch_raw_m3u(url_full)
    # 将所有行合并
    combined_entries = full_m3u.strip().splitlines() if full_m3u else []

    # 2. 提取 BBC
    url_bbc = 'https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/Global.m3u'
    bbc_m3u = fetch_raw_m3u(url_bbc)
    combined_entries += extract_entries(bbc_m3u, ['BBC'])

    # 3. 提取指定频道
    url_zh = 'https://raw.githubusercontent.com/suxuang/myIPTV/refs/heads/main/ipv6.m3u'
    zh_m3u = fetch_raw_m3u(url_zh)
    zh_keywords = ['台视新闻', '中天新闻', '香港卫视', '民视新闻台']
    combined_entries += extract_entries(zh_m3u, zh_keywords)

    # 4. 解析所有数据为结构化对象
    channels_data = parse_m3u_to_struct(combined_entries)

    # 5. 按分组名称排序
    channels_data.sort(key=lambda x: x['group'])

    # 6. 生成 M3U 文件 (带分组)
    with open('simple.m3u', 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for ch in channels_data:
            # 写入 group-title
            f.write(f'#EXTINF:-1 group-title="{ch["group"]}",{ch["name"]}\n')
            f.write(f'{ch["url"]}\n')

    # 7. 生成 TXT 文件 (带分组)
    with open('simple.txt', 'w', encoding='utf-8') as f:
        current_group = None
        for ch in channels_data:
            # 如果分组变化，写入分组头
            if ch["group"] != current_group:
                f.write(f'{ch["group"]},#genre#\n')
                current_group = ch["group"]
            f.write(f'{ch["name"]},{ch["url"]}\n')

    print(f"✅ 生成完成！共 {len(channels_data)} 个频道，已按分组排序。")
