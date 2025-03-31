import olefile, re
import zlib
import struct


email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+')
person_pattern = re.compile(r'\d{6}[-]\d{7}\b')
num_pattern = re.compile(r'\b(01[016789]-?\d{4}-?\d{4}|0\d{1,2}-?\d{3}-?\d{4})\b')
addr_pattern = re.compile(r'([가-힣]{2,6}(시|도)\s?[가-힣]{1,4}(군|구|시)\s?[가-힣0-9\-]+(읍|리|로|길)\s?\d{1,4})')
card_pattern = re.compile(r'\b(?:\d{4}-){3}\d{4}\b')


def get_hwp_text(filename):
    f = olefile.OleFileIO(filename)
    dirs = f.listdir()

    # HWP 파일 검증
    if ["FileHeader"] not in dirs or ["\x05HwpSummaryInformation"] not in dirs:
        raise Exception("Not Valid HWP.")

    # 문서 포맷 압축 여부 확인
    header = f.openstream("FileHeader")
    header_data = header.read()
    is_compressed = (header_data[36] & 1) == 1

    # BodyText 섹션 경로 수집
    nums = []
    for d in dirs:
        if d[0] == "BodyText":
            nums.append(int(d[1][len("Section"):]))

    sections = ["BodyText/Section" + str(x) for x in sorted(nums)]

    # 전체 텍스트 추출
    text = ""

    for section in sections:
        bodytext = f.openstream(section)
        data = bodytext.read()
        if is_compressed:
            try:
                unpacked_data = zlib.decompress(data, -15)
            except Exception as e:
                print(f"[압축 해제 오류] {e}")
                continue
        else:
            unpacked_data = data

        section_text = ""
        i = 0
        size = len(unpacked_data)

        while i < size:
            try:
                header = struct.unpack_from("<I", unpacked_data, i)[0]
                rec_type = header & 0x3ff
                rec_len = (header >> 20) & 0xfff
            except:
                break  # 데이터 끝에 도달하거나 깨졌을 경우

            if rec_type == 67:  # 문단 텍스트
                rec_data = unpacked_data[i+4:i+4+rec_len]
                try:
                    section_text += rec_data.decode('utf-16')
                except:
                    pass
                section_text += "\n"

            i += 4 + rec_len

        text += section_text
        text += "\n"

    return text

# 테스트
txt = get_hwp_text('testtest.hwp')

email = re.findall(email_pattern, txt)
person = re.findall(person_pattern, txt)
phonenum = re.findall(num_pattern, txt)
addr = re.findall(addr_pattern, txt)
card = re.findall(card_pattern, txt)


for content in [email, person, phonenum, addr, card]:
    if content:
        print(content)
