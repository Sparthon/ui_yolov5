"""
1.该图形检测界面总共包括文件为：
    ui.Main、ui.Main_detect、ui.Main_globalVal、Main_run
2.该界面目前仅检测图片，可以将原图与结果对比，同时输出预测框的文字信息，可以选择不同模型进行检测，同时可以实时删除模型，不需要重新启动程序。
3.该界面采用多线程将检测功能与主界面分离，防止因检测时间过长导致主界面卡死
4.该界面目前功能较少，ui不够美观，同时鲁棒性与稳定性不足，检测一定次数可能会卡死(已解决，采用信号来处理)，同时仅能检测特定数据集（筷子）,并且只能一张一张检测（改个代码的事）。
5.该界面为本人毕设顺手做的内容，并不是毕设本身，仅是方便自己查看检测效果。同时熟悉Python语言
"""

import os
import sys
from threading import Thread

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtCore import QObject, pyqtSignal  # 用信号来处理多线程问题
from PyQt5.QtWidgets import QTextBrowser

# import ui.Main_detect
# 导入模型
from ui.Main import Ui_MainWindow  # 导入detec_ui的界面
from ui.Main_detect import parse_opt, main, get_label_color  # 不能修改全局变量的值
from ui import Main_globalVal


# 自定义信号源对象类型，一定要继承自 QObject
class MySignals(QObject):
    # 定义一种信号，两个参数 类型分别是： QTextBrowser 和 字符串
    # 调用 emit方法 发信号时，传入参数 必须是这里指定的 参数类型
    # text_print = pyqtSignal(QTextBrowser,str)
    #
    # # 还可以定义其他种类的信号
    # update_table = pyqtSignal(str)
    text_print = pyqtSignal(QTextBrowser, list)


class UI_Logic_Window(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(UI_Logic_Window, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.init_slots()  # 控件绑定相关操作
        # 实例化
        self.global_ms = MySignals()
        self.global_ms.text_print.connect(self.printUI)  # 自定义信号的处理函数

    def printUI(self, fb, list_text):
        # label_x, color_y = ui.Main_detect.get_label_color()
        # label_color = zip(label_x, color_y)
        # list_label_color = list(label_color)
        for i in list_text:
            fb.append(f'<font color="{i[1]}">{i[0]}</font>')  # f"<font color:rgb{i[1]}>{i[0]}</font>"
        fb.ensureCursorVisible()

    # 控件绑定相关操作
    def init_slots(self):
        # global weight_global
        self.ui.pushButton.clicked.connect(self.detect)  # 图片检测 需要多线程
        self.ui.pushButton_2.clicked.connect(self.button_image_open)  # 添加图片
        self.ui.pushButton_3.clicked.connect(self.button_image_detect_save)  # 图片保存
        # search models automatically
        # 初始化
        self.ui.comboBox.clear()
        self.pt_list = os.listdir('./weights_py')  # 自动搜索权重
        self.pt_list = [file for file in self.pt_list if file.endswith('.pt')]
        self.pt_list.sort(key=lambda x: int(x[5:-3]))  # 排序  os.path.getsize('./weights_py/' + x)
        # 添加权重文件
        self.ui.comboBox.clear()
        self.ui.comboBox.addItems(self.pt_list)
        self.qtimer_search = QTimer(self)  # 定时更新权重
        self.qtimer_search.timeout.connect(lambda: self.search_pt())  # 周期性地进行检测模型文件操作
        self.qtimer_search.start(2000)
        self.model_type = self.ui.comboBox.currentText()
        self.weight_global = "./weights_py/%s" % self.model_type  # 更换权重
        self.ui.comboBox.currentTextChanged.connect(self.change_model)  # 更换权重控件

        # IoU滑动块与Conf滑动块
        Main_globalVal.set_confANDiou(0.25, 0.45)  # 初始化
        self.ui.horizontalSlider_IoU.valueChanged.connect(lambda x: self.change_val(x, 'horizontalSlider_IoU'))
        self.ui.doubleSpinBox_IoU.valueChanged.connect(lambda x: self.change_val(x, 'doubleSpinBox_IoU'))
        self.ui.horizontalSlider_Conf.valueChanged.connect(lambda x: self.change_val(x, 'horizontalSlider_Conf'))
        self.ui.doubleSpinBox_Conf.valueChanged.connect(lambda x: self.change_val(x, 'doubleSpinBox_Conf'))

    # 滑动块值与数值相互转化
    def change_val(self, x, flag):
        if flag == 'doubleSpinBox_Conf':
            self.ui.horizontalSlider_Conf.setValue(int(x * 100))
        elif flag == 'horizontalSlider_Conf':
            self.ui.doubleSpinBox_Conf.setValue(x / 100)
            # self.det_thread.conf_thres = x / 100
            # Main_globalVal.set_value_conf(x / 100)  # 当控件变化时改变全局变量值
            # conf = get_value('1')
            # print(f"置信度值：{conf}")
        elif flag == 'doubleSpinBox_IoU':
            self.ui.horizontalSlider_IoU.setValue(int(x * 100))
        elif flag == 'horizontalSlider_IoU':
            self.ui.doubleSpinBox_IoU.setValue(x / 100)
            # self.det_thread.iou_thres = x / 100
            # Main_globalVal.set_value_iou(x / 100)  # 当控件变化时改变全局变量值
            # iou = get_value('2')
        else:
            pass
        Main_globalVal.set_confANDiou(self.ui.doubleSpinBox_Conf.value(), self.ui.doubleSpinBox_IoU.value())

    # 搜索权重
    def search_pt(self):
        pt_list = os.listdir('./weights_py')
        pt_list = [file for file in pt_list if file.endswith('.pt')]
        pt_list.sort(key=lambda x: int(x[5:-3]))

        if pt_list != self.pt_list:
            self.pt_list = pt_list
            self.ui.comboBox.clear()
            self.ui.comboBox.addItems(self.pt_list)

    # 更换权重
    def change_model(self):
        self.model_type = self.ui.comboBox.currentText()
        self.weight_global = "./weights_py/%s" % self.model_type
        print("weight_global:", self.weight_global)

    # 设置需要检测的图片
    def button_image_open(self):
        name_list = []
        try:
            # 单个图片
            self.img_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "打开图片",
                                                                         r"./img",
                                                                         "*.bmp;;*.png;;*.jpg;;All Files(*)")
            # # 一个文件夹内的图片
            # self.img_name = QtWidgets.QFileDialog.getExistingDirectory(self, "打开图片",
            #                                                          r"D:\PyProject_All\YOLOv5_Project\yolov5\dataset\chopstick_Supervised_3\bad")
        except OSError as reason:
            print('文件打开出错啊！核对路径是否正确' + str(reason))
        else:
            # 判断图片是否为空
            if not self.img_name:
                QtWidgets.QMessageBox.warning(self, u"Warning", u"打开图片失败", buttons=QtWidgets.QMessageBox.Ok,
                                              defaultButton=QtWidgets.QMessageBox.Ok)
        # 打印检测图片，与label绑定起来
        jpg = QtGui.QPixmap(self.img_name).scaled(self.ui.label.width(), self.ui.label.height())
        self.ui.label.setPixmap(jpg)
        self.ui.label.setScaledContents(True)

    # 设置需要保存的地址
    def button_image_detect_save(self):
        print('button_image_save')
        self.save_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "选择文件夹", "runs/detect")
        print("选择的文件夹路径：", self.save_dir)

    # 检测函数
    def detect(self):
        self.ui.textBrowser.clear()  # 清空文本框
        try:
            source = self.img_name.replace('/', '\\')
        except:
            QtWidgets.QMessageBox.warning(self, u"Warning", u"请先选择要检测的图片文件",
                                          buttons=QtWidgets.QMessageBox.Ok,
                                          defaultButton=QtWidgets.QMessageBox.Ok)
            pass
        try:
            if self.save_dir:
                save_dir = self.save_dir
            else:
                save_dir = './runs/detect'  # 若文件保存路径为空，默认路径
        except:
            QtWidgets.QMessageBox.warning(self, u"Warning", u"请先选择要保存的图片文件夹",
                                          buttons=QtWidgets.QMessageBox.Ok,
                                          defaultButton=QtWidgets.QMessageBox.Ok)
            return

        # 调用main()检测图片,并打印输出
        # 创建新的线程去执行发送方法，
        # 服务器慢，只会在新线程中阻塞
        # 不影响主线程
        if source:
            self.ui.pushButton.setEnabled(False)  # 当点击后应禁用，等结果输出再解锁
            self.ui.comboBox.setEnabled(False)
            weight = self.weight_global
            thread = Thread(target=self.threadSend,
                            args=(save_dir, source, weight))
            thread.start()
        else:
            QtWidgets.QMessageBox.warning(self, u"Warning", u"没选择图片",
                                          buttons=QtWidgets.QMessageBox.Ok,
                                          defaultButton=QtWidgets.QMessageBox.Ok)
            return

    # 显示预测内容
    def textBro(self):
        # for x in list1:  # 以简单循环输出列表
        #     print(x)
        # 将标签跟预测框颜色合在一起

        label_x, color_y = get_label_color()
        label_color = zip(label_x, color_y)
        list_label_color = list(label_color)
        # for i in list_label_color:
        #     self.ui.textBrowser.append(f'<font color="{i[1]}">{i[0]}</font>')  # f"<font color:rgb{i[1]}>{i[0]}</font>"
        #     print(type(i[0]), ' and ', type(i[1]))  # <class 'str'>  and  <class 'str'>
        # self.ui.textBrowser.ensureCursorVisible()
        self.global_ms.text_print.emit(self.ui.textBrowser, list_label_color)

    # 新线程入口函数
    def threadSend(self, save_dir, source, weight):
        try:
            opt = parse_opt()
            opt.weights = weight
            print(opt.weights)
            opt.source = source
            opt.project = save_dir
            ###
            save_img = main(opt)  # 路径
            # print("_________________________________--")
            self.textBro()  # 显示预测内容函数入口
            ###
            print(save_img)
            # print(type(save_img))  # <class 'str'>
            jpg = QtGui.QPixmap(save_img).scaled(self.ui.label_2.width(), self.ui.label_2.height())
            self.ui.label_2.setPixmap(jpg)
            self.ui.label_2.setScaledContents(True)
            self.ui.pushButton.setEnabled(True)  # 当处理完后应将按钮解锁
            self.ui.comboBox.setEnabled(True)
        except:
            QtWidgets.QMessageBox.warning(self, u"Warning", u"检测失败",
                                          buttons=QtWidgets.QMessageBox.Ok,
                                          defaultButton=QtWidgets.QMessageBox.Ok)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    current_ui = UI_Logic_Window()
    current_ui.show()
    sys.exit(app.exec_())
