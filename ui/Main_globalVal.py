import json
path = 'ui/a.json'
def _init():  # 初始化
    global label_output, color_output
    label_output = []  # 标签
    color_output = []  # 预测框颜色
    # elif flag == '1':
    #     conf_thres = 0.25  # 置信度阈值
    #     iou_thres = 0.45  # 交并比阈值
    #     # dict_iouANDconf["conf"] = 0.25
    #     # dict_iouANDconf["iou"] = 0.45


# 用来设置主界面显示预测框数值
def set_value(label, color):
    # 定义全局变量
    global label_output, color_output
    label_output.append(label)
    color_output.append(color)


# 设置置信度、交并比阈值
def set_confANDiou(conf, iou):
    a = {"conf": conf, "iou": iou}
    a_json = json.dumps(a)
    with open(path, 'w') as f:
        f.write(a_json)

# 获得置信度、交并比阈值
def get_confANDiou(flag):
    with open(path, 'r') as f:
        data = json.load(f)
    if flag == '0':
        return data['conf']
    elif flag == '1':
        return data['iou']

def get_value():
    # 获得一个全局变量，不存在则提示读取对应变量失败
    try:
        # global label_output, color_output
        return label_output, color_output
    except:
        print('----------------------读取失败----------------------')


# class GlobalVal:
#     dict_iouANDconf = {}
#     def _init(self):  # 初始化
#
#         self.dict_iouANDconf["conf"] = 0.25
#         self.dict_iouANDconf["iou"] = 0.45
#
#     def set_dict_iouANDconf(self, key, value):
#         self.dict_iouANDconf[key] = value
#
#     def get_dict_iouANDconf(self, key):
#         try:
#             return self.dict_iouANDconf[key]
#         except:
#             print('----------------------读取失败----------------------')



if __name__ == '__main__':
    pass
