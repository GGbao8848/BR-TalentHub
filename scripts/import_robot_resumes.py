"""批量导入「机器人调试工程师」简历到系统。

简历文件来自 /tmp/resumes_import/简历/，从文件名提取姓名。
归属：北京大学（学校 id=1）/ 机器人调试工程师（岗位 id=30）。
"""
import io
import re
import uuid
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:18540/api/resumes/upload"
SRC = Path("/tmp/resumes_import/简历")
POSITION = "机器人调试工程师"
SCHOOL = "北京大学"


def extract_name(filename: str) -> str:
    # 序号01-范泽青_35岁.pdf / 序号14-方先生_35岁.pdf / 序号16-刘迪_应届生.pdf
    m = re.search(r"序号\d+[-_](.+?)(?:_\d+岁|_应届生|\.\w+$)", filename)
    if m:
        return m.group(1).strip()
    # 兜底：去掉序号前缀和后缀
    name = re.sub(r"^序号\d+[-_]", "", filename)
    name = re.sub(r"\.\w+$", "", name)
    return name.strip()


def upload(filename: str, data: bytes, name: str, phone: str):
    boundary = uuid.uuid4().hex
    body = io.BytesIO()
    fields = {"name": name, "phone": phone, "position": POSITION, "school": SCHOOL}
    for k, v in fields.items():
        body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    body.write(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        f"Content-Type: application/octet-stream\r\n\r\n".encode()
    )
    body.write(data)
    body.write(f"\r\n--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        API, data=body.getvalue(),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        out = resp.read().decode()
        return True, out
    except urllib.error.HTTPError as e:
        return False, f"{e.code} {e.read().decode()[:120]}"


def main():
    files = sorted(SRC.glob("*"))
    print(f"发现 {len(files)} 个文件")
    ok = fail = 0
    for i, f in enumerate(files, 1):
        name = extract_name(f.name)
        phone = f"138{8000000 + i:07d}"  # 13880000001 起，递增
        ok_flag, msg = upload(f.name, f.read_bytes(), name, phone)
        if ok_flag:
            ok += 1
            print(f"  ✓ {f.name} → {name} / {phone}")
        else:
            fail += 1
            print(f"  ✗ {f.name} → {msg}")
    print(f"\n导入完成：成功 {ok}，失败 {fail}")


if __name__ == "__main__":
    main()
