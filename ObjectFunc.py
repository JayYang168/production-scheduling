import numpy as np
class ObjFunc():
    def __init__(self,datapre):
        self.data = datapre.data
        self.car_type_exchange_matrix = datapre.car_type_exchange_matrix
        self.color_self_exchange_matrix = datapre.color_self_exchange_matrix
        self.color_exchange_matrix = datapre.color_exchange_matrix
        self.transmission_matrix = datapre.transmission_matrix
        self.colorContinutiyM = datapre.colorContinutiyM 
        self.numOfCar = datapre.numOfCar
        self.weldingTime = 80 #焊装耗时80s/车
        self.minimumServiceTime = 1800
        self.cleaningNozzleTime = 80 #清洗喷头耗时80s/次

    # f1:焊装车间装备切换次数
    def cal_f1(self,sol:list):
        f1 = 0
        for i in range(self.numOfCar-1):
            f1 += self.car_type_exchange_matrix[sol[i],sol[i+1]]
        # print('焊装车间装备切换次数:',f1)
        return f1/self.numOfCar

    def cal_f2(self,sol:list):
        f2 = 0
        record = 1 #连续次数
        for i in range(1,self.numOfCar):
            if self.colorContinutiyM[sol[i-1],sol[i]] and record < 5:
                record += 1
            else:
                f2 += record ** 2
                record = 1
                
        return 1/f2
    
# f3:总装车间，四驱车尽量连放，但连放次数<4，即最小化>=4的四驱车连放数
# 连续二两或者连续三辆四驱车被认为是最优的,和示例完全一样(被示例误导了)
    # 满足条件的连续四驱车和总的四驱车比例
    def cal_f3(self,sol:list):
        # 记录四驱车辆数
        fourNum = 0
        for i in range(self.numOfCar):
            if self.transmission_matrix[sol[i]]:
                fourNum += 1
        #不妨从后往前退
        f3 = 0 #记录不满足连续条件的四驱车数
        newsol = sol.copy()
        temp = [] #临时存储连续的四驱
        while len(newsol) > 0:
            carId = newsol.pop()
            # 如果是四驱车则添加
            if self.transmission_matrix[carId]:
                temp.append(carId)
            else:
                if len(temp) not in [2,3]:
                    f3 += len(temp)
                temp = []
        return f3/fourNum


    def cal_t1(self,sol:list):
        '''计算焊装车间等待时间'''
        beginTime = 0 #开始使用时间
        cumulativeWeldingTime = self.weldingTime
        for i in range(1,self.numOfCar):
            # 车辆类型发生改变
            if self.car_type_exchange_matrix[sol[i-1],sol[i]]:
                # 30min中内发生设备切换，需要等到第30min才可切换
                if cumulativeWeldingTime - beginTime < self.minimumServiceTime:
                    cumulativeWeldingTime = beginTime + self.minimumServiceTime
                    
                beginTime = cumulativeWeldingTime
            # 车辆类型未发生改变
            cumulativeWeldingTime += self.weldingTime
        cumulativeWeldingTime -= self.weldingTime * self.numOfCar #焊装设备等待时间
    
        return cumulativeWeldingTime

    def cal_t2(self,sol:list):
        cumulativeCleaningNozzleTime = 0.0 #额外的清洗时间
        i = 0
        # 这里只计算5的倍数
        while i < self.numOfCar-1:
            # 可能会和5的倍数重叠
            index = list(range(i,i+5)) #5的倍数生产
            count = 1
            for j in index[1:]:
                if j < self.numOfCar:
                    if self.color_exchange_matrix[sol[i],sol[j]] == 1:
                        cumulativeCleaningNozzleTime += self.cleaningNozzleTime
                    # 颜色连续结束
                    if self.colorContinutiyM[sol[i],sol[j]] == 0:
                        i = j
                        break
                    else:
                        count += 1
                    i = j
                else:
                    break
            if count == 5 and i < self.numOfCar-1:
                # 下一辆车也连续，不论是否连续都要清洗喷头，所以需要清洗喷头
                # if self.color_exchange_matrix[sol[i],sol[i+1]] == 0:
                #     cumulativeCleaningNozzleTime += self.cleaningNozzleTime
                cumulativeCleaningNozzleTime += self.cleaningNozzleTime
       
        return cumulativeCleaningNozzleTime

    # f3:总装车间，四驱车尽量连放，但连放次数<4，即最小化>=4的四驱车连放数
    def cal_f4(self,sol:list):
        f4 = self.cal_t1(sol) + self.cal_t2(sol)
        # 换成小时数
        return f4 / 3600

    def wObjFunc(self,sol:list):
        '''加权目标函数'''
        f = np.zeros(4)
        f[0] = self.cal_f1(sol) 
        f[1] = self.cal_f2(sol) 
        f[2] = self.cal_f3(sol) 
        f[3] = self.cal_f4(sol) 
        return f
