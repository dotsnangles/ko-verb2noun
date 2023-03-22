import os
import pandas as pd
from transformers import ElectraTokenizer

# 사용 방법
# 터미널에서 python main_generate_ner_data.py 실행 후 안내에 따라 인과 객체 엑셀 파일이 존재하는 폴더명을 입력
# 개체명 인식 훈련을 위한 데이터가 csv 양식으로 ner_data_gen_results에 저장됩니다.

def main():
    # Load Tokenizer
    ckpt = 'monologg/koelectra-base-v3-discriminator'
    tokenizer = ElectraTokenizer.from_pretrained(ckpt)

    # Load Data
    DATA_PATH = input('인과 객체 엑셀 파일이 존재하는 폴더명을 입력하세요\n')
    print('개체명 인식 데이터를 생성합니다.')

    sheets = sorted([os.path.join(DATA_PATH, sheet) for sheet in os.listdir(DATA_PATH)])
    col_num_count = lambda sheet: len(pd.read_excel(sheet).columns)
    col_nums = [col_num_count(sheet) for sheet in sheets]

    dfs = [pd.read_excel(sheet, names=[f'Col {i}' for i in range(col_num)]) for sheet, col_num in zip(sheets, col_nums)]

    df2lst = [df.values.tolist() for df in dfs]

    raw_data = []
    for item in df2lst:
        raw_data.extend(item)

    # Delete Duplicate Objects and Split Sentences
    dups_removed = []
    for lst in raw_data:
        temp = []
        for el in lst:
            if type(el) == str and el not in temp:
                temp.append(el.strip())
        dups_removed.append(temp)

    # split by space
    tokens_lst = [[el.split() for el in lst] for lst in dups_removed]

    ## Generate Labels
    labels_lst = []
    for sample in tokens_lst:
        labels4sample = []
        for idx, tokens in enumerate(sample):
            if idx == 0:
                labels4sample.append(['O' for _ in range(len(tokens))])
            else:
                labels = ['E_B'] + ['E_I' for _ in range(len(tokens)-1)]
                labels4sample.append(labels)
        labels_lst.append(labels4sample)
    test_tokens, test_labels = tokens_lst[0], labels_lst[0]

    # 원문의 라벨은 현재 O로 통일되어 있습니다. 객체의 패턴이 원문에서 발견되면 상응하도록 원문의 라벨을 수정합니다.
    position_pairs_lst = []
    for tokens in tokens_lst:
        source = tokens[0]
        len_source = len(source)
        markers = tokens[1:]

        position_pairs = []
        for idx, _ in enumerate(source):
            for marker in markers:
                len_marker = len(marker)
                if source[idx:idx+len_marker] == marker:
                    position_pairs.append([idx, idx+len_marker])

        position_pairs_lst.append(position_pairs)

    for labels, position_pairs in zip(labels_lst, position_pairs_lst):
        source_labels = labels[0]
        for pair in position_pairs:
            start = pair[0]
            end = pair[1]
            source_labels[start] = 'E_B'
            if end-start > 1:
                source_labels[start+1:end] = ['E_I' for _ in range(end-start-1)]

    # 다음 작업을 진행하기 위해 리스트의 양식을 정리합니다.
    tokens_lst = [el for tokens in tokens_lst for el in tokens]
    labels_lst = [el for labels in labels_lst for el in labels]

    # Electra 토크나이저를 사용해 토큰화를 진행하고 라벨을 조정합니다.
    def tokenize_and_preserve_labels(tokens_lst, labels_lst):
        tokenized_sentence = []
        labels = []
        for word, label in zip(tokens_lst, labels_lst):
            tokenized_word = tokenizer.tokenize(word)
            n_subwords = len(tokenized_word)

            tokenized_sentence.extend(tokenized_word)

            if label[-1] == 'B' and n_subwords > 1:
                tail = list(label)
                tail[-1] = 'I'
                tail = ''.join(tail)
                labels.extend([label] + [tail]*(n_subwords-1))
            else:
                labels.extend([label] * n_subwords)

        return tokenized_sentence, labels

    tokenized_texts_and_labels = [
                                [*tokenize_and_preserve_labels(words, labs)]
                                for words, labs in zip(tokens_lst, labels_lst)
                                ]

    # None 값을 추가해 샘플 사이의 구분자로 사용합니다.
    for tokens, labels in tokenized_texts_and_labels:
        tokens.append(None)
        labels.append(None)

    # 추후 사용을 위해 데이터프레임을 생성하고 저장합니다.
    data = {
        'tokens': [],
        'labels': []
    }

    for tokens, labels in tokenized_texts_and_labels:
        data['tokens'].extend(tokens)
        data['labels'].extend(labels)
        
    data_df = pd.DataFrame(data)

    data_df.to_csv(f'./ner_data_gen_results/ner_data.csv', index=False, encoding='utf-8-sig')
    
if __name__ == '__main__':
    main()