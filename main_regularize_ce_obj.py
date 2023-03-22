import os
import pandas as pd
from module.regularize import sentence_to_noun_verb

# 사용 방법
# 터미널에서 python main_regularize_ce_obj.py 실행 후 안내에 따라 인과 객체 엑셀 파일이 존재하는 폴더명을 입력
# 원문을 제외한 인과 객체들에 대하여 표현 정규화 작업을 진행한 후 
# ce_obj_reg_results 폴더에 원본과 작업을 마친 데이터를 csv 양식으로 저장합니다.

def main():
    DATA_PATH = input('인과 객체 엑셀 파일이 존재하는 폴더명을 입력하세요\n')
    print('표현 정규화 작업을 시작합니다.')

    sheets = sorted([os.path.join(DATA_PATH, sheet) for sheet in os.listdir(DATA_PATH)])
    col_num_count = lambda sheet: len(pd.read_excel(sheet).columns)
    col_nums = [col_num_count(sheet) for sheet in sheets]

    dfs = [pd.read_excel(sheet, names=[f'Col {i}' for i in range(col_num)]) for sheet, col_num in zip(sheets, col_nums)]
    ce_chains_dfs = [df.iloc[:, 1:] for df in dfs]

    ce_chains_regularized_dfs = [ce_chains.applymap(lambda x: sentence_to_noun_verb(x) if type(x) == str else x) for ce_chains in ce_chains_dfs]

    for sheet, ce_chains_df in zip(sheets, ce_chains_dfs):
        file_name = sheet.split('/')[-1].split('.')[0]
        ce_chains_df.to_csv(f'./ce_obj_reg_results/{file_name}_original.csv', index=False, encoding='utf-8-sig')
        
    for sheet, ce_chains_regularized_df in zip(sheets, ce_chains_regularized_dfs):
        file_name = sheet.split('/')[-1].split('.')[0]
        ce_chains_regularized_df.to_csv(f'./ce_obj_reg_results/{file_name}_regularized.csv', index=False, encoding='utf-8-sig')
    
if __name__ == '__main__':
    main()