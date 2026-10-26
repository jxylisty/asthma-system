# 后处理：1) 删除空 <w:pgNumType/>（WPS 兼容）；2) 页脚 PAGE 域补 \* arabic 格式开关
import re
import shutil
import sys
import zipfile

src = sys.argv[1]
tmp = src + ".tmp"

with zipfile.ZipFile(src, "r") as zin:
    names = zin.namelist()
    contents = {n: zin.read(n) for n in names}

# 1) document.xml：移除空 pgNumType
doc = contents["word/document.xml"].decode("utf-8")
doc = doc.replace("<w:pgNumType/>", "")
contents["word/document.xml"] = doc.encode("utf-8")

# 2) footer*.xml：PAGE -> PAGE \* arabic \* MERGEFORMAT
pat = re.compile(r"(<w:instrText[^>]*>)\s*PAGE\s*(</w:instrText>)")
for n in list(contents):
    if re.match(r"word/footer\d*\.xml$", n):
        xml = contents[n].decode("utf-8")
        xml2 = pat.sub(r"\1 PAGE \\* arabic \\* MERGEFORMAT \2", xml)
        if xml2 != xml:
            print(f"patched {n}")
        contents[n] = xml2.encode("utf-8")

with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for n in names:
        zout.writestr(n, contents[n])
shutil.move(tmp, src)
print("post-process done:", src)
