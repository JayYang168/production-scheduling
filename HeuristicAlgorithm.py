import random
import numpy as np

class HeuristicAlgorithm():
    def __init__(self,datapre):
        self.data = datapre.data
        self.adjM = datapre.adjM #距离矩阵
        self.transmission_matrix = datapre.transmission_matrix #变速器转换矩阵
        self.numOfCar = datapre.numOfCar
        self.dataArray = datapre.dataArray


    def getNearestNeighbor(self,carId:int,leftCarId)->list:
        '''获取与当前车辆关系最近的邻居，并由近及远排序
        '''
        sortedIndex = np.argsort(self.adjM[carId,leftCarId])

        return sortedIndex

    def HH(self):
        carTypes = list(self.data['车型'].unique())
        random.shuffle(carTypes)
        lastAllSol = []
        self.flag = True #以一定概率选择是否牺牲颜色的连续性来优化时间
        if random.random() > 0.5:
            self.flag = False
        for i,car in enumerate(carTypes):
            # print('测试i',i)
            temp = self.data[self.data['车型'] == car].copy()
            leftCarId = temp.index.to_list()
            # print(leftCarId)
            if i == 0:
                candiIndexs = temp.drop_duplicates(keep='first').index.to_list()
                firstCarId = candiIndexs[random.randint(0,len(candiIndexs)-1)]
            else:
                # 离sol[-1]最近的一个
                nextCarIdIndexs = self.getNearestNeighbor(lastAllSol[-1],leftCarId)
                firstCarId = leftCarId[nextCarIdIndexs[0]]
            leftCarId.remove(firstCarId)
            carTypesol = self.HA(firstCarId,leftCarId)
            carTypesol = self.optimize(carTypesol)
            carTypesol = self.adjustFour(carTypesol) #four出现了问题
            carTypesol = self.singleFour(carTypesol)

            lastAllSol.extend(carTypesol)
        lastAllSol = self.adjustFour(lastAllSol)
        return lastAllSol

    def HA(self,firstCarId,leftCarId):
        '''不考虑焊装切换，这意味着先生产一种车型再生产另一种车型'''
        sol = [firstCarId]
        while len(leftCarId) > 0:
            nextCarIdIndexs = self.getNearestNeighbor(sol[-1],leftCarId)
            carId = leftCarId[nextCarIdIndexs[0]]
            sol.append(carId)
            leftCarId.remove(carId)

        return sol

    def optimize(self,sol):
        ### 以消耗一定颜色的连续性从而在时间上面进行进一步优化,87.798025
        ## BB->BB->BB->BB->AB
        tempdata = self.data.loc[sol]
        tempdata_drop_duplicates = tempdata[['车身颜色','车顶颜色']].drop_duplicates(keep='first')
        homochromatic = tempdata_drop_duplicates[tempdata_drop_duplicates['车身颜色'] == tempdata_drop_duplicates['车顶颜色']]
        hc  = homochromatic['车身颜色'].to_list()
        hfb = {}
        labels = [] #记录调整的颜色
        labelsUp = [] #记录下接分隔点
        for c in hc:
            temp = {}
            # 前接,需接4个同色
            indexs1 = (tempdata['车身颜色'] != c) & (tempdata['车顶颜色'] == c)
            front = indexs1[indexs1].index.to_list()
            temp['front'] = front
            # 后接，需接5个同色，优先两驱
            indexs2 = (tempdata['车身颜色'] == c) & (tempdata['车顶颜色'] != c)
            tempbehindData = tempdata[indexs2].sort_values(by='变速器',ascending=False)
            behind = tempbehindData.index.to_list()
            temp['behind'] = behind

            hfb[c] = temp


        if self.flag:
            for c in hc:
                temp = hfb[c]
                behindList = temp['behind'].copy()

                # 1.先标记，固定位置不动
                for carId in behindList:
                    sol.remove(carId)
                newsol = []
                r = 0
                for i in range(len(sol)):
                    if len(behindList) > 0:
                        if self.dataArray[sol[i],2] == self.dataArray[behindList[-1],1]:
                            if r % 5 == 0:
                                carId = behindList.pop()
                                labelsUp.append(carId)
                                labels.append(carId)
                                newsol.append(carId)
                            r += 1
                        elif r > 0:
                            newsol.extend(behindList)
                            newsol.extend(sol[i:])
                            behindList = []
                            break
                        newsol.append(sol[i])
                    else:
                        newsol.extend(sol[i:])
                        break
                newsol.extend(behindList)
                sol = newsol.copy()


        for c in hc:
            temp = hfb[c]
            frontList = temp['front'].copy()
            if len(frontList) > 0:
                if not self.flag:
                    frontList = frontList[:1]
                record =[]
                for carId in frontList:
                    for i in range(3,len(sol)):
                        if self.dataArray[sol[i],1] == c and\
                        self.dataArray[sol[i],2] == c and\
                        self.dataArray[sol[i],-1] == self.dataArray[carId,-1] and \
                        self.dataArray[sol[i-1],-1] == self.dataArray[carId,-1]:
                            record.append(sol[i-3:i+1])
                            sol = sol[:i-3] + sol[i+1:]
                            break
                for carId in frontList:
                    index = sol.index(carId)
                    if len(record) > 0:
                        temp = record.pop()
                        temp.reverse()
                        for num in temp:
                            sol.insert(index,num)
        return sol

    def adjustFour(self,sol):
        '''处理连续四驱'''

        # 把可以取出来的二驱取出来，车辆自身颜色不同
        recordCarIds = [] #非同色单个两驱,按索引从小到大排序
        if self.dataArray[sol[0],-1] == '两驱' and self.dataArray[sol[1],-1] == '四驱' and\
            self.dataArray[sol[0],1] != self.dataArray[sol[1],2]:
            recordCarIds.append(sol[0])
        for i in range(1,len(sol)-1):
            if self.dataArray[sol[i],1] != self.dataArray[sol[i],2] and \
                self.dataArray[sol[i],-1] == '两驱' and self.dataArray[sol[i+1],-1] == '两驱' and\
                    self.dataArray[sol[i],1] != self.dataArray[sol[i+1],2]:
                recordCarIds.append(sol[i])
        if self.dataArray[sol[-2],-1] == '四驱' and self.dataArray[sol[-1],-1] == '两驱':
            recordCarIds.append(sol[-1])

        #搜寻同色可取两驱
        labelSol = sol.copy()
        hlabels = [] #标记同色可取两驱车
        k = 1
        while k < len(labelSol):
            if self.dataArray[labelSol[k],1] == self.dataArray[labelSol[k],2] and\
                self.dataArray[labelSol[k-1],-1] == '两驱' and\
                self.dataArray[labelSol[k],-1] == '两驱':
                hlabels.append(labelSol[k])
                labelSol.pop(k)
            else:
                k +=1

        for i in range(3,len(sol)):
            if sum(self.transmission_matrix[sol[i-3:i+1]]) == 4 :
                # 先看同色有无最近
                flag = False
                if self.dataArray[sol[i-2],1] == self.dataArray[sol[i-1],2] and len(hlabels) > 0:
                    nextCarIdsh = self.getNearestNeighbor(sol[i-2],hlabels)
                    carId = hlabels[nextCarIdsh[0]]
                    flag = True
                    hlabels.remove(carId)
                # 异色
                if not flag and recordCarIds:
                    nextCarIds1 = self.getNearestNeighbor(sol[i-2],recordCarIds)
                    carId1 = recordCarIds[nextCarIds1[0]]
                    nextCarIds2 = self.getNearestNeighbor(recordCarIds,sol[i-1])
                    carId2 = recordCarIds[nextCarIds2[0]]
                    if self.adjM[sol[i-2],carId1] < self.adjM[carId2,sol[i-1]]:
                        carId = carId1
                    else:
                        carId = carId2
                    recordCarIds.remove(carId)

                carIdIndex = sol.index(carId)
                if i-1 < carIdIndex:
                    carIdIndex += 1
                sol.insert(i-1,carId)
                sol.pop(carIdIndex)
        return sol



    def singleFour(self,sol):
        '''处理单个四驱'''
        fours = []
        if self.dataArray[sol[0],-1] == '四驱' and\
            self.dataArray[sol[0],1] != self.dataArray[sol[1],2]:
            fours.append(sol[0])
        for i in range(1,len(sol)-1):
            if self.dataArray[sol[i],1] != self.dataArray[sol[i],2] and\
            self.dataArray[sol[i],-1] == '四驱' and \
            self.dataArray[sol[i-1],1] != self.dataArray[sol[i],2] and\
            self.dataArray[sol[i],1] != self.dataArray[sol[i+1],2]:
                fours.append(sol[i])
        if self.dataArray[sol[-1],-1] == '四驱' and \
            self.dataArray[sol[-2],1] != self.dataArray[sol[-1],2]:
            fours.append(sol[-1])

        # 记录不可移动的单个四驱车值
        fours1 = []
        if self.dataArray[sol[0],-1] == '四驱' and\
            self.dataArray[sol[0],1] == self.dataArray[sol[1],2]:
            fours1.append(sol[0])
        for i in range(1,len(sol)-1):
            if self.dataArray[sol[i-1],-1] == '两驱' and self.dataArray[sol[i],-1] == '四驱' \
                and self.dataArray[sol[i+1],-1] == '两驱':
                if self.dataArray[sol[i],1] == self.dataArray[sol[i+1],2] or\
                self.dataArray[sol[i-1],1] == self.dataArray[sol[i],2]:
                    fours1.append(sol[i])
        if self.dataArray[sol[-2],-1] == '两驱' and self.dataArray[sol[-1],-1] == '四驱'and\
            self.dataArray[sol[-2],1]!=self.dataArray[sol[-1],2]:
            fours1.append(sol[-1])


        #调整不可移动的单个四驱

        for carId in fours1:
            if len(fours) > 0:
                nextCarIds1 = self.getNearestNeighbor(carId,fours)
                carId1 = fours[nextCarIds1[0]]
                nextCarIds2 = self.getNearestNeighbor(fours,carId)
                carId2 = fours[nextCarIds2[0]]
                if self.adjM[carId,carId1] < self.adjM[carId2,carId]:
                    insertCarId = carId1
                else:
                    insertCarId = carId2
                sol.remove(insertCarId)
                fours.remove(insertCarId)
                insertCarIdIndex = sol.index(carId)
                if self.dataArray[sol[max(insertCarIdIndex-1,0)],1] == self.dataArray[carId,2]:
                    insertCarIdIndex += 1
                sol.insert(insertCarIdIndex,insertCarId)




        recordValues = [] #记录单个四驱的值
        if self.dataArray[sol[0],-1] == '四驱' and self.dataArray[sol[1],-1] == '两驱':
            recordValues.append(sol[0])
        for i in range(1,len(sol)-1):
            if self.dataArray[sol[i-1],-1] == '两驱' and self.dataArray[sol[i],-1] == '四驱' \
                and self.dataArray[sol[i+1],-1] == '两驱':
                recordValues.append(sol[i])

        if self.dataArray[sol[-2],-1] == '两驱' and self.dataArray[sol[-1],-1] == '四驱':
            recordValues.append(sol[-1])


       # 计算单个四驱的前后距离之和,然后排序，距离最小的先按时不动,这里出现了问题
        leftDis = []
        for carId in recordValues:
            carIdIndex = sol.index(carId)
            if self.dataArray[carId,1] == self.dataArray[carId,2]:
                dis = 0
            elif carIdIndex == 0:
                dis = 20
            elif carIdIndex == len(sol)-1:
                dis = 20
            else:
                dis = self.adjM[sol[carIdIndex-1],sol[carIdIndex]] + self.adjM[sol[carIdIndex],sol[carIdIndex+1]]
            leftDis.append(dis)
        leftDis = np.argsort(leftDis)
        sortedRecordValues = []
        for i in leftDis:
            sortedRecordValues.append(recordValues[i])

        # 如果只剩3个则组成[1,2,3]的阵型
        while len(sortedRecordValues) > 3:
            carId = sortedRecordValues.pop(0)
            insertCarId = sortedRecordValues.pop()
            sol.remove(insertCarId)
            carIdIndex = sol.index(carId)
            carIdIndex = min(len(sol),carIdIndex+1)
            sol.insert(carIdIndex,insertCarId)

        if len(sortedRecordValues) > 1:
            carId = sortedRecordValues.pop(0)
            while len(sortedRecordValues) > 0:
                insertCarId = sortedRecordValues.pop()
                sol.remove(insertCarId)
                carIdIndex = sol.index(carId)
                carIdIndex = min(len(sol),carIdIndex+1)
                sol.insert(carIdIndex,insertCarId)
        # 只有存在1个单个四驱的情况，
        elif len(sortedRecordValues) == 1:
            carId = sortedRecordValues[0]
            sol.remove(carId)
            flag = False
            for i in range(3,len(sol)-1):
                #i-2和i-1为四驱
                if sum(self.transmission_matrix[sol[i-3:i+1]]) == 2 and\
                    sum(self.transmission_matrix[sol[i-2:i]]) == 2 and\
                    self.dataArray[sol[i-1],1] != self.dataArray[sol[i-1],2]:
                    sol.insert(i-1,carId)
                    flag = True
                    sortedRecordValues.remove(carId)
                    break

            if not flag:
                sol.append(carId)
                sol = self.adjustFour(sol)

        return sol
