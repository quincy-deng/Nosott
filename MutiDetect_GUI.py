import glob
import os
import random
import subprocess

import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QFileDialog, QPushButton, QVBoxLayout,
                             QHBoxLayout, QFrame, QLabel, QMessageBox, QTableWidget,
                             QTableWidgetItem, QScrollArea)

temp_id = str(os.getpid()) + '_' + str(random.randint(0, 9999))
ab_database = "/home/dengqiuyang/biosoft/Kaptive/reference_database/Acinetobacter_baumannii_k_locus_primary_reference" \
              ".gbk "
kp_database = "/home/dengqiuyang/biosoft/Kaptive/reference_database/Klebsiella_k_locus_primary_reference.gbk"

abricate_res = 'output/summary_{}.tab'.format(temp_id)
kaptive_res = 'output/kaptive_{}_table.txt'.format(temp_id)
st_res = 'output/{}.tsv'.format(temp_id)
res_file = {'mlst': st_res, 'abricate': abricate_res, 'kaptive': kaptive_res}


class MultiDetect(QWidget):
    def __init__(self):
        super().__init__()
        self.tableview = QTableWidget()
        self.setWindowTitle('Multi Detect')
        self.smples = None
        self.process_id = {'kaptive': '荚膜型检测', 'mlst': 'ST型检测', 'abricate': '耐药/毒力基因检测'}

        # 控件
        self.btn1 = QPushButton('选择文件夹')
        self.label = QLabel('')
        self.sample_label = QLabel('')
        self.labe2 = QLabel('')
        self.execute_abricate = QPushButton('耐药/毒力基因检测')
        self.execute_mlst = QPushButton('ST型检测')
        self.excute_kaptive = QPushButton('荚膜型检测')

        # 槽函数
        self.btn1.clicked.connect(self.choose_dir)
        self.execute_abricate.clicked.connect(self.execute)
        self.execute_mlst.clicked.connect(self.execute)
        self.excute_kaptive.clicked.connect(self.execute)

        self.main_ui()

    def main_ui(self):
        layout = QHBoxLayout()

        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.Box)
        left_layout = QVBoxLayout(left_frame)

        w1 = QWidget()
        w1_layout = QHBoxLayout(w1)
        w1_layout.addWidget(self.btn1)
        left_layout.addWidget(w1)
        left_layout.addWidget(self.label)
        left_layout.addWidget(self.sample_label)

        # 功能选择模块
        left_layout.addStretch(1)
        self.excute_kaptive.setObjectName('kaptive')
        self.execute_mlst.setObjectName('mlst')
        self.execute_abricate.setObjectName('abricate')
        left_layout.addWidget(self.execute_mlst)
        left_layout.addWidget(self.excute_kaptive)
        left_layout.addWidget(self.execute_abricate)
        left_layout.addWidget(self.labe2)
        # left_layout.addStretch(3)

        right_frame = QFrame()
        right_layout = QHBoxLayout(right_frame)
        right_widget = QScrollArea()
        right_layout.addWidget(right_widget)
        scroll_layout = QHBoxLayout(right_widget)
        scroll_layout.addWidget(self.tableview)
        # right_layout.addWidget(right_widget)
        # right_layout.addWidget(self.tableview)
        right_frame.setFrameShape(QFrame.Box)

        layout.addWidget(left_frame)
        layout.addWidget(right_frame)
        layout.setStretchFactor(left_frame, 3)
        layout.setStretchFactor(right_frame, 7)
        self.setLayout(layout)

    def choose_dir(self):
        selected_dir = QFileDialog.getExistingDirectory(self, '选择文件夹', './')
        if selected_dir:
            self.label.setText(selected_dir)
            samples = glob.glob('{}/*.fasta'.format(selected_dir)) + glob.glob('{}/*.fna'.format(selected_dir))
            sample_names = [os.path.basename(i) for i in samples]
            if len(samples) == 0:
                self.sample_label.setText('指定文件夹下没有fasta文件')
                self.sample_label.setStyleSheet('color:rgb(255, 120, 255)')
            else:
                self.sample_label.setText('\n'.join(sample_names))
                self.sample_label.setStyleSheet('color:rgb(0, 0, 0)')
                self.smples = samples
        else:
            self.label.setText('未选择文件夹,请指定')

    def execute(self):
        if self.smples:
            subprocess1 = self.sender().objectName()
            self.excute_kaptive.setEnabled(False)
            self.execute_mlst.setEnabled(False)
            self.execute_abricate.setEnabled(False)
            self.labe2.setText('执行 {} 中...'.format(self.process_id[subprocess1]))
            # noinspection PyAttributeOutsideInit
            self.thread = Thread(self.smples, subprocess1)
            self.thread.signal.connect(self.set_btn)
            self.thread.start()
        else:
            QMessageBox.information(self, '错误', '未指定文件夹或指定文件夹没有fasta样本')

    def set_btn(self, idd, msg):
        self.excute_kaptive.setEnabled(True)
        self.execute_mlst.setEnabled(True)
        self.execute_abricate.setEnabled(True)
        if idd == 1:
            self.labe2.setText('{} 执行完成!'.format(self.process_id[msg]))
            if os.path.isfile(res_file[msg]):
                if msg == 'mlst':
                    df = pd.read_table(res_file[msg],
                                       names=['File', 'scheme', 'ST'] + ['gene_' + str(i) for i in range(1, 8)])
                else:
                    df = pd.read_table(res_file[msg])
                row, col = df.shape
                self.tableview.setRowCount(row)
                self.tableview.setColumnCount(col)
                self.tableview.setHorizontalHeaderLabels(df.columns.tolist())
                for i in range(row):
                    for j in range(col):
                        self.tableview.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))

        if idd == 0:
            err = msg.split("::")
            # time.sleep(2)
            self.labe2.setText("运行{}出错:{}".format(err[0], err[1]))


def execute_shell_command(commandline):
    ret = subprocess.Popen(commandline, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = ret.communicate()
    ret.wait()
    if ret.returncode == 0:
        return 'ok'
    else:
        stderr = str(result[0], encoding='utf8')
        return stderr


def execute_abricate(filenames):
    commandline_abricate = 'conda run -n abricate abricate {} >output/results_{}.tab;conda run -n abricate ' \
                           'abricate --summary output/results_{}.tab >output/summary_{}.tab'.format(
                            ' '.join(filenames), temp_id, temp_id, temp_id)
    return execute_shell_command(commandline_abricate)


def execute_mlst(filenames):
    command_mlst = 'conda run -n mlst mlst -q {} >output/{}.tsv'.format(' '.join(filenames), temp_id)
    return execute_shell_command(command_mlst)


class Thread(QThread):
    _signal = pyqtSignal(int, str)

    def __init__(self, samples, process):
        super().__init__()
        self.samples = samples
        self.process = process

    def run(self):
        if self.process == 'kaptive':
            res = self.execute_kaptive()
            if res != 'ok':
                self._signal.emit(0, 'kaptive::{}'.format(res))
            else:
                self._signal.emit(1, 'kaptive')

        elif self.process == 'mlst':
            res = execute_mlst(self.samples)
            if res != 'ok':
                self._signal.emit(0, 'mlst::{}'.format(res))
            else:
                self._signal.emit(1, 'mlst')

        elif self.process == 'abricate':
            res = execute_abricate(self.samples)
            if res != 'ok':
                self._signal.emit(0, 'abricate::{}'.format(res))
            else:
                self._signal.emit(1, 'abricate')

    def execute_kaptive(self):
        res_st = execute_mlst(self.samples)
        if res_st != 'ok':
            return "mlst::{}".format(res_st)
        df = pd.read_table('output/{}.tsv'.format(temp_id),
                           names=['File', 'scheme', 'ST'] + ['gene_' + str(i) for i in range(1, 8)])
        ab_files = list(df['File'].loc[df['scheme'].str.contains('abaumannii')])
        kp_files = list(df['File'].loc[df['scheme'].str.contains('kpneumoniae')])
        if len(ab_files + kp_files) == 0:
            return "mlst::{}".format('fasta文件中没有鲍曼不动杆菌或者肺炎克雷伯')

        if len(ab_files) > 0:
            command_kaptive = 'conda run -n abricate ~/bin/kaptive.py --threads 1 -a {} -k {} -o output/kaptive_{}'.format(
                ' '.join(ab_files), ab_database, temp_id)
            return execute_shell_command(command_kaptive)

    @property
    def signal(self):
        return self._signal
