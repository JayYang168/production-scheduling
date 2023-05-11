import numpy as np
import pandas as pd
# 数据预处理类
class DataPre():
    def __init__(self,data) -> None:
        '''数据预处理'''
        self.data = data[['车型','车身颜色','车顶颜色','变速器']].copy()
        self.colorMap()
        self.dataArray = self.data[['车型','车身颜色','车顶颜色','变速器']].to_numpy()
        self.numOfCar = self.data.shape[0]
        self.transmission_matrix = self.getTransM()
        self.car_type_exchange_matrix = self.getCarTypeExM()
        self.color_exchange_matrix = self.getColorExM()
        self.color_self_exchange_matrix = self.getSelfColorExM()
        self.adjM = self.adjacencyM()
        self.colorContinutiyM = self.getColorContinuity()
       

    def getTransM(self):
        '''将变速器为四驱的设置为1，两驱设置为0'''
        transmission_matrix = np.zeros(self.numOfCar)
        for i in range(self.numOfCar):
            if self.dataArray[i,-1] == '四驱':
                transmission_matrix[i] = 1
        return transmission_matrix

    def getCarTypeExM(self):
        '''获取车型变换矩阵'''
        car_type_exchange_matrix = np.zeros((self.numOfCar,self.numOfCar))
        for i in range(self.numOfCar):
            for j in range(self.numOfCar):
                if self.dataArray[i,0] != self.dataArray[j,0]:
                    car_type_exchange_matrix[i,j] = 1
        return car_type_exchange_matrix

    def colorMap(self):
        '''车顶颜色为无对比色时，认为车顶与车身颜色相同'''
        non_color = self.data['车顶颜色'] == '无对比颜色'
        self.data.loc[non_color,'车顶颜色'] = self.data.loc[non_color,'车身颜色']

    def getColorExM(self):
        '''获取连续两车之间的颜色切换矩阵'''
        color_exchange_matrix = np.zeros((self.numOfCar,self.numOfCar)) 
        for i in range(self.numOfCar):
            for j in range(self.numOfCar):
                if self.dataArray[i,1] != self.dataArray[j,2]:
                    color_exchange_matrix[i,j] = 1
        return color_exchange_matrix

    def getSelfColorExM(self):
        color_self_exchange_matrix = np.zeros(self.numOfCar)
        for i in range(self.numOfCar):
            if self.dataArray[i,2] != self.dataArray[i,1]:
                color_self_exchange_matrix[i] = 1
        return color_self_exchange_matrix

    # 首先要构建颜色连续矩阵
    def getColorContinuity(self):
        colorContinutiyM = np.zeros((self.numOfCar,self.numOfCar))
        for i in range(self.numOfCar):
            # '车型','车身颜色','车顶颜色','变速器'
            for j in range(self.numOfCar):
                if self.dataArray[i,2] == self.dataArray[i,1] and \
                    self.dataArray[i,1] == self.dataArray[j,2] and \
                        self.dataArray[j,2] == self.dataArray[j,1]:
                        colorContinutiyM[i,j] = 1
        return colorContinutiyM

    def adjacencyM(self):
        adjM = np.zeros((self.numOfCar,self.numOfCar))
        for i in range(self.numOfCar):
            for j in range(self.numOfCar):
                if i != j:
                    if self.dataArray[i,0] != self.dataArray[j,0]:
                        adjM[i,j] += 10
                    # 两车之间需清洗喷头，即车辆i的车身颜色和车辆j的车顶颜色不同
                    if self.dataArray[i,1] != self.dataArray[j,2]:
                        adjM[i,j] += 5
                    # 倾向于下一辆车同色
                    if self.dataArray[j,1] != self.dataArray[j,2]:
                        adjM[i,j] += 2.5
             
                    # 两车的车身颜色不同
                    if self.dataArray[i,1] != self.dataArray[j,1]:
                        adjM[i,j] += 2
                    # 两车的车顶颜色不同
                    if self.dataArray[i,2] != self.dataArray[j,2]:
                        adjM[i,j] += 1
                    # if self.dataArray[i,-1] != self.dataArray[j,-1]:
                    #     adjM[i,j] += 0.5
                    if self.dataArray[j,-1] == '四驱':
                        adjM[i,j] += 0.5
                    
                else:
                    adjM[i,j] = 20
        return adjM

