#! /opt/mambaforge/bin/python

import boto3
import json
import argparse
import os
import sys
from datetime import datetime
import mimetypes

# === 读取配置 ===
def load_config(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件未找到: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# === 提取包含 m5 的行 ===
def extract_m5(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            if "m5" in line:
                print(f"[{filepath}] 找到包含 'm5' 的行：{line.strip()}")
                return line.strip()
    print(f"[{filepath}] 未找到包含 'm5' 的行")
    return None

# === 上传到 S3 ===
def upload_to_s3(file_path, bucket, key, aws_config):
    base_url = config.get('base_url')
        # 自动识别 MIME 类型
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = "application/octet-stream"
        
    s3 = boto3.client('s3',
        aws_access_key_id=aws_config.get('aws_access_key_id'),
        aws_secret_access_key=aws_config.get('aws_secret_access_key'),
        region_name=aws_config.get('aws_region')
    )
    try:
        s3.upload_file(
            Filename=file_path,
            Bucket=bucket,
            Key=key,
            ExtraArgs={'ContentType': content_type}
        )
        print(f"{base_url}/{key}")
    except Exception as e:
        print(f"[{file_path}] 上传失败：{e}")

# === 构建 object_key 路径 ===
def build_object_key(template, file_path):
    now = datetime.now()
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    ext = ext.lstrip('.')
    # md5 = extract_m5(file_path)

    substitutions = {
        "filename": filename,
        "name": name,
        "ext": ext,
        "timestamp": str(int(now.timestamp())),
        "date": now.strftime("%Y-%m-%d"),
        "datetime": now.strftime("%Y%m%d_%H%M%S"),
        # "md5": md5
    }

    for key, value in substitutions.items():
        template = template.replace(f"{{{key}}}", value)

    return template

# === 主程序 ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量上传文件到 S3（提取包含 m5 的内容）")
    parser.add_argument('--config', default='config.json', help='配置文件路径（默认：config.json）')
    parser.add_argument('files', nargs='+', help='要上传的文件路径列表')
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        bucket_name = config.get("bucket_name")
        object_key_template = config.get("object_key", "uploads/{filename}")

        for file_path in args.files:
            if not os.path.isfile(file_path):
                print(f"[{file_path}] 跳过，文件不存在")
                continue

            filename = os.path.basename(file_path)
            object_key = build_object_key(object_key_template, file_path)
            upload_to_s3(file_path, bucket_name, object_key, config)

    except Exception as e:
        print(f"程序出错：{e}")
