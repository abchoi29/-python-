import olefile, re
import zlib
import struct




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

patterns = {
    'email' : r'[\w\.-]+@[\w\.-]+',
    'person' : r'\d{6}[-]\d{7}\b',
    'num' : r'\b(01[016789]-?\d{4}-?\d{4}|0\d{1,2}-?\d{3}-?\d{4})\b',
    'addr' : r'([가-힣]{2,6}(시|도)\s?[가-힣]{1,4}(군|구|시)\s?[가-힣0-9\-]+(읍|리|로|길)\s?\d{1,4})',
    'card' : r'\b(?:\d{4}-){3}\d{4}\b'
}

txt = get_hwp_text('testtest.hwp')

result = {}
for key, pattern in patterns.items():
    matches = re.findall(pattern, txt)
    result[key] = matches                 #result 딕셔너리 구조 :{'email': ['test@example.com'], 'person': ['900101-1234567'] ...}


summary = []                           #summury는 각 카테고리의 개수정보 포함한 리스트 (ex)['email: 2개', 'person: 1개', 'card: 1개']
total_count = 0

for category, items in result.items():          
    if items:
        count = len(items)
        summary.append(f"{category}: {count}개")
        total_count += count


if total_count > 0:
    print(f"{total_count}개의 민감정보가 식별되었습니다.")
    for i in summary:                    # summary 출력결과 :' email: 2개  person: 1개  card: 1개'
        print(i,' ', end='')
    print('\n')            

    for key, value in result.items():        #민감정보 상세 내용 출력
        if value:
            print(f"{key}: {','.join(value)}")
        else:
            pass
else:
    print("민감정보가 없습니다.")

