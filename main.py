import pickle
import pandas as pd
from tqdm import tqdm
from DataPre import DataPre
from HeuristicAlgorithm import HeuristicAlgorithm
from ObjectFunc import ObjFunc
path = r'D:\硕士学习\雪浪云比赛\汽车排产\git\data'


import os 
path = r'D:\硕士学习\雪浪云比赛\汽车排产\git\data'
files = os.listdir(path)
files = [int(file.split('.')[0].split('_')[-1]) for file in files]
files.sort()

for num in tqdm(files):
    output_hal = open(r'D:\硕士学习\雪浪云比赛\参数集\{}.pkl'.format(num),'wb')
    # 读取数据
    data = pd.read_csv(path+'\data_{}.csv'.format(num))
    # 数据预处理
    preData = DataPre(data)
    # 算法排产
    ha = HeuristicAlgorithm(preData)
    sol = ha.HH()
    objFunc = ObjFunc(preData)
    
    print('\n {}数据集目标函数值:{}'.format(num,objFunc.wObjFunc(sol)),'\n')
    # 保存解
    save_file = r'D:\硕士学习\雪浪云比赛\汽车排产\git\detailed_results\{}.csv'.format(num)
    data.loc[sol].to_csv(save_file,index=None)
    break

