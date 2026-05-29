import re
import requests
import time


def fetch_raw_m3u(url):
    print("fetch raw m3u from " + url)
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def test_m3u8_speed(url, timeout=10):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout, stream=True)
        first_byte_time = time.time()

        if response.status_code != 200:
            return float('inf')  # 不合格

        # 读取一小块数据确保链接有效
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                break

        return (first_byte_time - start_time) * 1000  # TTFB 毫秒
    except:
        return float('inf')


def extract_entries(m3u_text, keywords):
    # 提取匹配关键字的频道
    entries = []
    lines = m3u_text.strip().splitlines()
    for i in range(len(lines)):
        if lines[i].startswith('#EXTINF') and any(k in lines[i] for k in keywords):
            if i + 1 < len(lines) and not lines[i + 1].startswith('#'):
                entries.append(lines[i])
                entries.append(lines[i + 1])
    return entries


def parse_channel_name(extinf_line):
    """从 #EXTINF 行中提取频道名称"""
    try:
        # 格式: #EXTINF:-1 tvg-id="..." tvg-name="..." group-title="...",频道名
        if ',' in extinf_line:
            channel_name = extinf_line.split(',')[-1].strip()
            return channel_name if channel_name else "未知频道"
    except:
        pass
    return "未知频道"


def extract_channels_info(lines):
    """解析 M3U 行列表，返回 [(频道名, URL), ...] 格式"""
    channels = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('#EXTINF'):
            # 提取频道名
            channel_name = parse_channel_name(line)
            
            # 获取下一行的 URL
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith('#'):
                    channels.append((channel_name, next_line))
                    i += 2
                    continue
        i += 1
    
    return channels


if __name__ == '__main__':
    # 1. 获取完整的 ipv6.m3u
    url_full = 'https://raw.githubusercontent.com/fanmingming/live/refs/heads/main/tv/m3u/ipv6.m3u'
    full_m3u = fetch_raw_m3u(url_full)
    combined_entries = full_m3u.strip().splitlines()

    # 2. 提取 BBC
    url_bbc = 'https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/Global.m3u'
    bbc_m3u = fetch_raw_m3u(url_bbc)
    bbc_entries = extract_entries(bbc_m3u, ['BBC'])

    # 3. 提取指定频道
    url_zh = 'https://raw.githubusercontent.com/suxuang/myIPTV/refs/heads/main/ipv6.m3u'
    zh_m3u = fetch_raw_m3u(url_zh)
    zh_keywords = ['台视新闻', '中天新闻', '香港卫视', '民视新闻台']
    zh_entries = extract_entries(zh_m3u, zh_keywords)

    # 4. 合并所有条目
    combined_entries += bbc_entries + zh_entries

    # 5. 解析频道信息（频道名 + URL）
    channels_info = extract_channels_info(combined_entries)

    # 6. 保存为 M3U 格式
    with open('simple.m3u', 'w', encoding='utf-8') as f:
        # 写入 M3U 文件头
        f.write('#EXTM3U\n')
        for channel_name, url in channels_info:
            f.write(f'#EXTINF:-1,{channel_name}\n')
            f.write(f'{url}\n')

    # 7. 保存为 TXT 格式
    with open('simple.txt', 'w', encoding='utf-8') as f:
        for channel_name, url in channels_info:
            f.write(f'{channel_name},{url}\n')

    print(f"✅ 生成完成！")
    print(f"   📄 simple.m3u - {len(channels_info)} 个频道")
    print(f"   📄 simple.txt  - {len(channels_info)} 个频道")
