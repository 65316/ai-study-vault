#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
看图助手：把图片发给视觉模型，返回文字描述/OCR 结果。
用途：DeepSeek 网页版看不了图，先用本脚本把题目截图转成文字，再拿去网页版免费提问。

用法：
    python tools/vision.py <图片路径> [提示词]
示例：
    python tools/vision.py "90_图片/题目1.png" "把图里的题目完整转成文字，保留公式"
配置：同目录 vision_config.json（只需填 api_key）
依赖：无第三方库（纯标准库）
"""
import base64
import json
import mimetypes
import pathlib
import sys
import urllib.request

# Windows 控制台中文输出防乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

CONFIG_PATH = pathlib.Path(__file__).with_name("vision_config.json")


def load_config():
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if cfg.get("api_key", "").startswith("YOUR_"):
        sys.exit("❌ 还没填 API key：请编辑 tools/vision_config.json，把 api_key 换成你自己的密钥。")
    return cfg


def to_data_url(image_path: str) -> str:
    p = pathlib.Path(image_path)
    if not p.exists():
        sys.exit(f"❌ 找不到图片：{p}")
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    image_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "把图片里的内容完整转成文字（Markdown 格式，数学公式用 LaTeX），不要遗漏。"

    cfg = load_config()
    payload = {
        "model": cfg["model"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": to_data_url(image_path)}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }

    req = urllib.request.Request(
        cfg["base_url"].rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['api_key']}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        print(data["choices"][0]["message"]["content"])
    except urllib.error.HTTPError as e:
        print(f"❌ 接口报错 {e.code}：{e.read().decode('utf-8', 'ignore')[:500]}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
