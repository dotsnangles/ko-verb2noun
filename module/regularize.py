import re
from jamo import h2j, j2h, j2hcj
from konlpy.tag import Kkma, Komoran

kkma = Kkma()
komoran = Komoran(userdic='module/userdic.txt')
tokenizer = komoran

irregular_conjugation_stems = ['걷', '긷', '깨닫', '눋', '닫', '듣', '묻', '붇', '싣', '일컫', '가깝', '가볍', '간지럽', '굽', '그립', '깁', '껄끄럽', '노엽', '더럽', '덥', '맵', '메스껍', '무겁', '반갑', '부끄럽', '사납', '서럽', '쑥스럽', '줍', '긋', '낫', '붓', '잇', '잣', '젓', '짓', ]

def verb_exception_handler(verb):
    if verb == '나서':
        return '나'
    if verb == '아니하':
        return '않'
    else:
        return verb
    
def verb_to_noun(verb):
    
    """
    한국어의 용언을 명사형으로 변환하는 함수입니다.
    용언(동사, 형용사)의 어간을 받아 명사형으로 반환합니다.
        
    """
    
    verb = verb_exception_handler(verb)

    eum = '음'  # 명사형 전성 어미 '음'
    m = h2j('음')[-1]  # 명사형 전성 어미 'ㅁ'

    d = h2j('ㄷ')  # ㄷ 불규칙 활용
    s = h2j('ㅅ')  # ㅅ 불규칙 활용
    b = h2j('ㅂ')  # ㅂ 불규칙 활용

    last_syllables = h2j(verb[-1])  # 용언의 마지막 자모군
    final = j2hcj(last_syllables[-1])  # 마지막 자모군의 끝글자

    pattern = re.compile(r'[ㅏ-ㅣ]')
    has_final = not bool(pattern.match(final))  # 마지막 자모군에 종성 존재 여부

    if has_final:  # 종성이 존재하는 경우
        if final == d and verb in irregular_conjugation_stems:  # ㄷ 불규칙 활용 적용
            modified = last_syllables[:-1] + h2j('ㄹ')
            return verb[:-1] + j2h(*modified) + eum
        elif final == s and verb in irregular_conjugation_stems:  # ㅅ 불규칙 활용 적용
            modified = last_syllables[:-1]
            return verb[:-1] + j2h(*modified) + eum
        if final == b and verb in irregular_conjugation_stems:  # ㅂ 불규칙 활용
            modified = h2j('우') + m
            return verb[:-1] + j2h(*last_syllables[:-1]) + j2h(*modified)
        else:  # 종성이 존재하나 불규칙 활용이 아닌 경우
            modified = last_syllables
            return verb[:-1] + j2h(*modified) + eum
    else:  # 종성이 존재하지 않는 경우
        modified = last_syllables + m
        return verb[:-1] + j2h(*modified)

def extract_keywords(sentence):
    
    """
    문장을 입력으로 받아서 형태소 분석을 수행하고, 명사(Noun)와 동사(Verb)를 추출하는 함수
    마지막 토큰이 명사형 혹은 동사의 어근이 아닌 경우 삭제합니다.
    tokenizer별 형태소 분류표: https://docs.google.com/spreadsheets/d/1OGAjUvalBuX-oZvZ_-9tEfYD2gQe7hTGsgUpiiBSXI8/edit#gid=0

    """
    words = sentence.split()
    
    words_w_pos = []
    for word in words:
        pos = tokenizer.pos(word)
        pos = [[word, tag] for word, tag in pos]
        words_w_pos.append(pos)

    endable_pos = ['VV', 'VA', 'VX', 'NNG', 'NNP']
    poppable = False
    for word_w_pos in words_w_pos:
        for pair in word_w_pos:
            if pair[1] in endable_pos:
                poppable = True
                break
        if poppable:
            break

    if poppable:
        for idx in range(len(words_w_pos)-1, -1, -1):
            while words_w_pos[idx][-1][1] not in endable_pos:
                words_w_pos[idx].pop(-1)
                if len(words_w_pos[idx]) < 1:
                    break
            if len(words_w_pos[idx]) > 0:
                break
        words_w_pos = [word_w_pos for word_w_pos in words_w_pos if word_w_pos != []]
        return words_w_pos
    else:
        return words_w_pos
    
def join_off_syllable(test_case):
    pattern = re.compile(r'[ㄱ-ㅎ]')
    searched = pattern.search(test_case)
    
    if searched:
        off_syllable_position, *_ = searched.span()
        former_syllables = h2j(test_case[off_syllable_position-1])
        if len(former_syllables) < 3:
            off_syllable = h2j(test_case[off_syllable_position])
            modified = former_syllables + off_syllable
            modified = j2h(*modified)
            result = test_case[:off_syllable_position-1] + modified + test_case[off_syllable_position+1:]
            return result
    else:
        return test_case
    
def join_all_off_syllables(test_case):
    while True:
        result = join_off_syllable(test_case)
        if test_case == result:
            return result
        else:
            test_case = result

def sentence_to_noun_verb(sentence):

    """
    "사다리가 쓰러져서" 문장을 "사다리가 쓰러짐" 문자열로 변환하는 함수
    extract_keywords를 통해 얻은 keywords_w_pos에 대한 표현 정규화 작업을 수행합니다.
    리스트의 마지막 요소가 동사의 어근인 경우만 해당 작업을 수행합니다. (['VV', 'VA', 'VX'])

    """
    words_w_pos = extract_keywords(sentence)

    if words_w_pos[-1][-1][1] in ['VV', 'VA', 'VX']:
        words_w_pos[-1][-1][0] = verb_to_noun(words_w_pos[-1][-1][0])
    
    result = [[word for word, tag in word_w_pos] for word_w_pos in words_w_pos]
    result = [''.join(el) for el in result]
    result = ' '.join(result)
    
    return  join_all_off_syllables(result)