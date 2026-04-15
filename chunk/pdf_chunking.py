import fitz
import getpass
import re


def open_pdf_with_password(pdf_path):
    doc = fitz.open(pdf_path)

    # 如果 PDF 有加密
    if doc.needs_pass:
        print("PDF 需要密碼")

        for _ in range(3):  # 最多試 3 次
            password = getpass.getpass("請輸入 PDF 密碼: ")

            if doc.authenticate(password):
                print("密碼正確")
                return doc
            else:
                print("密碼錯誤")

        raise ValueError("密碼錯誤次數過多，停止處理")

    return doc



# ----------------------------
# 清理文字
# ----------------------------
def clean_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]

    cleaned = []
    prev_empty = False

    for line in lines:
        if line == "":
            if prev_empty:
                continue
            prev_empty = True
        else:
            prev_empty = False
        cleaned.append(line)

    text = "\n".join(cleaned)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


# ----------------------------
# 判斷標題（核心）
# ----------------------------
def is_heading(line):
    line = line.strip()

    if not line:
        return False

    if len(line) > 120:
        return False

    # 編號標題
    if re.match(r"^\d+(\.\d+)*[\s\-:：]+", line):
        return True

    # function / API 名稱
    #if re.match(r"^[A-Za-z_][A-Za-z0-9_]{2,}\s*(\(|$)", line):
    #    return True

    # HTTP API
    #if re.match(r"^(GET|POST|PUT|DELETE)\s+\/", line):
    #    return True

    # 全大寫
    #if line.isupper() and len(line) < 50:
    #    return True

    # 短句
    #if len(line) < 40 and not line.endswith("."):
    #    return True

    return False


# ----------------------------
# chunk
# ----------------------------
def chunk_text(text, chunk_size=800, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


# ----------------------------
# 主流程
# ----------------------------
def process_pdf(pdf_path):
    doc = open_pdf_with_password(pdf_path)

    sections = []
    current = {
        "title": "UNKNOWN",
        "content": [],
        "page": None
    }

    # ---------- Step 1: PDF → sections ----------
    for page_index, page in enumerate(doc):
        if page_index < 11:
          continue
        page_num = page_index + 1
        text = clean_text(page.get_text())

        if not text:
            continue

        lines = text.split("\n")

        for line in lines:
            if is_heading(line):
                # 存前一段
                if current["content"]:
                    sections.append({
                        "title": current["title"],
                        "content": "\n".join(current["content"]),
                        "page": current["page"]
                    })

                # 新 section
                current = {
                    "title": line.strip(),
                    "content": [],
                    "page": page_num
                }

            else:
                current["content"].append(line)
                if current["page"] is None:
                    current["page"] = page_num

    # 最後一段
    if current["content"]:
        sections.append({
            "title": current["title"],
            "content": "\n".join(current["content"]),
            "page": current["page"]
        })

    doc.close()

    # ---------- Step 2: section → chunks ----------
    all_chunks = []
    for sec in sections:
        text = f"[Section: {sec['title']}]\n\n{sec['content']}"
        chunks = chunk_text(text)

        for chunk in chunks:
            all_chunks.append({
                "page": sec["page"],
                "text": chunk
            })

    # ---------- Step 3: print ----------
    for idx, chunk in enumerate(all_chunks, start=1):
        preview = chunk["text"][:500]

        print(f"\n=== Chunk {idx} ===")
        print(f"Page: {chunk['page']}")
        print(preview)


# ----------------------------
# 執行
# ----------------------------
if __name__ == "__main__":
    process_pdf("test2.pdf")