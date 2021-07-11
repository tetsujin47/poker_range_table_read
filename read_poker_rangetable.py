# -*- coding: utf-8 -*-
import cv2
import copy
from PIL import Image
import sys
import pyocr
import pyocr.builders
import re
import os
import argparse

RAISE_COLOR_BGR = []
CALL_COLOR_BGR = []
SPLIT_TABLEFILE_DIR = "handsell"
TRUMP_LIST = ["A","K","Q","J","T","9","8","7","6","5","4","3","2"]
TRUMP_NUM = 13
TRUMP_TABLE_NUM = TRUMP_NUM * TRUMP_NUM

class Args_processing_process:
    def __init__(self):
        pass

    def args_check(self):
        parser = argparse.ArgumentParser(description='ポーカーレンジ表を解析ソフト用の文字列データに変換する')
        parser.add_argument("-action","-a",choices=["raise", "call"], help="取得したいハンドレンジテーブルのレンジを指定する", required=True)
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-gto","-gto+",action="store_true",help="GTO+の文字列データで出力する")
        group.add_argument("-pio",action="store_true",help="PioSOLVERの文字列データで出力する")
        parser.add_argument("-img","-i",help="ハンドレンジ表の画像データ(png)のパスを指定する", required=True)
        parser.add_argument("-type","-t",choices=["snowie_mac", "snowie3_win","snowie4_win"], help="ハンドレンジ表の画像データの種類を選択する",required=True)
        parser.add_argument("-path","-p",help="Tesseract OCRの実行ファイルのパスを指定する。")
        args = parser.parse_args()
        
        if args.action == "raise":
            raise_bool = True
        elif args.action == "call":
            raise_bool = False
        else:
            raise_bool = None
        
        if args.gto == True:
            softname = "gto+"
        elif args.pio == True:
            softname = "pio"
        else:
            softname = None
        
        img = cv2.imread(args.img)
        if img is None:
            print('-imgに指定した画像データが正しく読み込めませんでした。')
            quit()
        
        if args.type == "snowie_mac":
            range_table_type = "snowie_mac"
        elif args.type == "snowie3_win":
            range_table_type = "snowie3_win"
        elif args.type == "snowie4_win":
            range_table_type = "snowie4_win"
        else:
            range_table_type = None
            
        tesseract_file = args.path
        
        return raise_bool,softname,img,tesseract_file,range_table_type

class Image_processing_process:
    def __init__(self):
        pass

    def get_color_bgr(self,range_table_type):
        if range_table_type == "snowie_mac":
            raise_color_bgr = [153,227,177]
            call_color_bgr = [188,242,255]
        elif range_table_type == "snowie3_win":
            raise_color_bgr = [18,169,4]
            call_color_bgr = [111,221,255]
        elif range_table_type == "snowie4_win":
            raise_color_bgr = [153,227,177]
            call_color_bgr = [188,242,255]
        else:
            raise_color_bgr = []
            call_color_bgr = []
        return raise_color_bgr,call_color_bgr
        
        
    def image_split_processing(self,img,range_table_type):
        # BGR -> グレースケール
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # エッジ抽出 (Canny)
        edges = cv2.Canny(gray, 1, 100, apertureSize = 3)
        # 膨張処理
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.dilate(edges, kernel)
        contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rects = []
        
        if not os.path.isdir(SPLIT_TABLEFILE_DIR):
            os.makedirs(SPLIT_TABLEFILE_DIR)
        if  range_table_type != "snowie3_win":
            if not os.path.isdir(SPLIT_TABLEFILE_DIR + "2"):
                os.makedirs(SPLIT_TABLEFILE_DIR + "2")
        
        for cnt, hrchy in zip(contours, hierarchy[0]):
            if cv2.contourArea(cnt) < 400:
                continue  # 面積が小さいものは除く
            rect = cv2.minAreaRect(cnt)
            rect_points = cv2.boxPoints(rect).astype(int)
            rects.append(rect_points)

        top_left = rects[0][0]
        top_right = rects[0][1]
        bottom_left = rects[0][2]
        bottom_right = rects[0][3]

        cv2.imwrite('img.png', img[top_left[1]:bottom_left[1],top_left[0]:top_right[0]])
        x_one_sell = float((top_right[0] - top_left[0]) / 13)
        y_one_sell = float((bottom_left[1] - top_left[1]) / 13)
        
        return rects,x_one_sell,y_one_sell
        
    def output_split_image_file(self,img,rects,x_one_sell,y_one_sell,SPLIT_TABLEFILE_DIR,range_table_type):
        x_sell_num = TRUMP_NUM
        y_sell_num = TRUMP_NUM
        
        for y_sell in range(y_sell_num):
            for x_sell in range(x_sell_num):
                number = y_sell * y_sell_num + x_sell

                if os.name == "nt":
                    split_tablefile = ".\\" + SPLIT_TABLEFILE_DIR + "\\" + str(number) + ".png"
                else:
                    split_tablefile = "./" + SPLIT_TABLEFILE_DIR + "/" + str(number) + ".png"
                if range_table_type != "snowie3_win":
                    if os.name == "nt":
                        split_tablefile2 = ".\\" + SPLIT_TABLEFILE_DIR + "2\\" + str(number) + ".png"
                    else:
                        split_tablefile2 = "./" + SPLIT_TABLEFILE_DIR + "2/" + str(number) + ".png"

                if range_table_type == "snowie3_win":
                    top = int(rects[0][0][1]) + int(y_sell * y_one_sell) + int(y_one_sell / 5)
                    bottom = int(rects[0][0][1]) + int((y_sell+1) * y_one_sell) - int(y_one_sell / 5)
                    left = int(rects[0][0][0]) + int(x_sell * x_one_sell) + int(x_one_sell / 5)
                    right = int(rects[0][0][0]) + int((x_sell+1) * x_one_sell) - int(x_one_sell / 5)
                    cv2.imwrite(split_tablefile,img[top:bottom,left:right])
                else:
                    top = int(rects[0][0][1]) + int(y_sell * y_one_sell) + int(y_one_sell / 2)
                    top2 = int(rects[0][0][1]) + int(y_sell * y_one_sell) + int(3*y_one_sell / 5)
                    bottom = int(rects[0][0][1]) + int((y_sell+1) * y_one_sell)
                    left = int(rects[0][0][0]) + int(x_sell * x_one_sell)
                    right = int(rects[0][0][0]) + int((x_sell+1) * x_one_sell)
                    left2 = int(rects[0][0][0]) + int(x_sell * x_one_sell) + int(x_one_sell / 5)
                    right2 = int(rects[0][0][0]) + int((x_sell+1) * x_one_sell) - int(x_one_sell / 5)
                    cv2.imwrite(split_tablefile, img[top:bottom,left:right])
                    cv2.imwrite(split_tablefile2, img[top2:bottom,left2:right2])

    def image_ocr_processing(self,SPLIT_TABLEFILE_DIR,tesseract_file,raise_bool,range_table_type):
        rsise_ration_list = []
        call_ration_list = []
        
        raise_color_bgr,call_color_bgr = self.get_color_bgr(range_table_type)

        for location in range(0, TRUMP_TABLE_NUM):
            if os.name == "nt":
                img_file = ".\\" + SPLIT_TABLEFILE_DIR + "\\" + str(location) + ".png"
            else:
                img_file = "./" + SPLIT_TABLEFILE_DIR + "/" + str(location) + ".png"
            
            img = cv2.imread(img_file)
            h,w,c = img.shape
            raise_num = 0
            call_num = 0
    
            if raise_bool == True:
                for pixel in range(w):
                    if (raise_color_bgr[0] - 5) <= img[int(h / 10),pixel,0] <= (raise_color_bgr[0] + 5):
                        if (raise_color_bgr[1] - 5) <= img[int(h / 10),pixel,1] <= (raise_color_bgr[1] + 5):
                            if(raise_color_bgr[2] - 5) <= img[int(h / 10),pixel,2] <= (raise_color_bgr[2] + 5):
                                raise_num += 1
                rsise_ration_list.append(int((raise_num / w) * 100 + 0.5))
                raise_num = 0
            else:
                for pixel in range(w):
                    if (call_color_bgr[0] - 5) <= img[int(h / 10),pixel,0] <= (call_color_bgr[0] + 5):
                        if (call_color_bgr[1] - 5) <= img[int(h / 10),pixel,1] <= (call_color_bgr[1] + 5):
                            if(call_color_bgr[2] - 5) <= img[int(h / 10),pixel,2] <= (call_color_bgr[2] + 5):
                                call_num += 1
                call_ration_list.append(int((call_num / w) * 100 + 0.5))
                call_num = 0

        if os.name == "nt":
            if tesseract_file is not None:
                pyocr.tesseract.TESSERACT_CMD = tesseract_file
            else:
                pass
                #pyocr.tesseract.TESSERACT_CMD = 'C:\\Users\\ユーザ名\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe'
        
        tools = pyocr.get_available_tools()
        
        if len(tools) == 0:
            print("No OCR tool found")
            print("第四引数にtesseractコマンドのインストールパスを絶対パスで指定してください")
            sys.exit(1)

        tool = tools[0]
        lang = 'eng'
       
        row_list = []

        for location in range(0, TRUMP_TABLE_NUM):
            if os.name == "nt":
                if range_table_type == "snowie3_win":
                    target_file = ".\\" + SPLIT_TABLEFILE_DIR + "\\{}.png"
                else:
                    target_file = ".\\" + SPLIT_TABLEFILE_DIR + "2\\{}.png"
            else:
                if range_table_type == "snowie3_win":
                    target_file = "./" + SPLIT_TABLEFILE_DIR + "/{}.png"
                else:
                    target_file = "./" + SPLIT_TABLEFILE_DIR + "2/{}.png"

            text = tool.image_to_string(
            Image.open(target_file.format(location)),
            lang = lang,
            builder = pyocr.builders.DigitBuilder(tesseract_layout = 10)
            )
            text = re.sub(r'\D', '', text)
            
            if text == "" or text == '':
                row_list.append("-")
            else:
                row_list.append(text)
        return row_list,rsise_ration_list,call_ration_list

class Image_decision_process:
    def __init__(self):
        pass
        
    def image_decision(self,row_list,rsise_ration_list,call_ration_list,raise_bool,range_table_type):
        range_list = []

        for location in range(0, TRUMP_TABLE_NUM):
            q = location // TRUMP_NUM
            mod = location % TRUMP_NUM
            if q < mod:
                end_word = "s"
            elif mod < q:
                end_word = "o"
            else:
                end_word = ""

            if raise_bool == True:
                if rsise_ration_list[location] > 0:
                    if row_list[location] != "-":
                        if range_table_type != "snowie3_win":
                            if rsise_ration_list[location] - 5 < int(row_list[location]) < rsise_ration_list[location] + 5:
                                range_list.append(int(row_list[location]))
                            else:
                                self._output_error_message(q,mod,TRUMP_LIST,end_word)
                                range_list.append(int(row_list[location]))
                        else:
                            if rsise_ration_list[location] < 10:
                                range_list.append(int(row_list[location]))
                            else:
                                self._output_error_message(q,mod,TRUMP_LIST,end_word)
                                range_list.append(int(row_list[location]))
                    else:
                        if range_table_type != "snowie3_win":
                            if 90 > rsise_ration_list[location] > 2:
                                self._output_error_message(q,mod,TRUMP_LIST,end_word)
                                range_list.append(-1)
                            elif rsise_ration_list[location] >= 90:
                                range_list.append(100)
                            else:
                                range_list.append(-1)
                        else:
                            if rsise_ration_list[location] >= 90:
                                range_list.append(100)
                            else:
                                range_list.append(-1)
                else:
                    if row_list[location] != "-":
                        if range_table_type != "snowie3_win":
                            self._output_error_message(q,mod,TRUMP_LIST,end_word)
                            range_list.append(int(row_list[location]))
                        else:
                            range_list.append(int(row_list[location]))
                    else:
                        range_list.append(-1)
            else:
                if call_ration_list[location] > 0:
                    if row_list[location] != "-":
                        if range_table_type != "snowie3_win":
                            if call_ration_list[location] - 5 < 100 - int(row_list[location]) < call_ration_list[location] + 5:
                                range_list.append(100 - int(row_list[location]))
                            else:
                                self._output_error_message(q,mod,TRUMP_LIST,end_word)
                                range_list.append(100 - int(row_list[location]))
                        else:
                            if call_ration_list[location] >= 90:
                                range_list.append(100 - int(row_list[location]))
                            else:
                                range_list.append(-1)
                    else:
                        if range_table_type != "snowie3_win":
                            if 90 > call_ration_list[location] > 2:
                                self._output_error_message(q,mod,TRUMP_LIST,end_word)
                                range_list.append(-1)
                            elif call_ration_list[location] >= 90:
                                range_list.append(100)
                            else:
                                range_list.append(-1)
                        else:
                            if call_ration_list[location] >= 90:
                                range_list.append(100)
                            else:
                                range_list.append(-1)
                else:
                    range_list.append(-1)
        return range_list

    def _output_error_message(self,q,mod,TRUMP_LIST,end_word):
        if(q < mod):
            print("数字の識字に失敗した可能性があります" + str(TRUMP_LIST[q]) + str(TRUMP_LIST[mod]) + end_word)
        else:
            print("数字の識字に失敗した可能性があります" + str(TRUMP_LIST[mod]) + str(TRUMP_LIST[q]) + end_word)

class Output_result_process:
    def __init__(self):
        pass
        
    def output_result(self,range_list,softname):
        gto_range_output_list = []
        pio_range_output_list = []
        if softname == "gto+" or softname is None:
            for y_axis in range(TRUMP_NUM):
                for x_axis in range(TRUMP_NUM):
                    end_word = self._suits_check(y_axis,x_axis)
                    if 100 > range_list[y_axis * TRUMP_NUM + x_axis] > 0:
                        if y_axis >= x_axis:
                            gto_range_output_list.append("[" + str(range_list[y_axis * TRUMP_NUM + x_axis]) + "]" + TRUMP_LIST[x_axis] + TRUMP_LIST[y_axis] + end_word + "[/" + str(range_list[y_axis * TRUMP_NUM + x_axis]) + "]")
                        else:
                            gto_range_output_list.append("[" + str(range_list[y_axis * TRUMP_NUM + x_axis]) + "]" + TRUMP_LIST[y_axis] + TRUMP_LIST[x_axis] + end_word + "[/" + str(range_list[y_axis * TRUMP_NUM + x_axis]) + "]")
                    if 100 == range_list[y_axis * TRUMP_NUM + x_axis]:
                        if y_axis >= x_axis:
                            gto_range_output_list.append(TRUMP_LIST[x_axis] + TRUMP_LIST[y_axis] + end_word)
                        else:
                            gto_range_output_list.append(TRUMP_LIST[y_axis] + TRUMP_LIST[x_axis] + end_word)
            print("GTO+のハンドレンジ出力結果")
            print(','.join(map(str, gto_range_output_list)))
        if softname == "pio" or softname is None:
            for y_axis in range(TRUMP_NUM):
                for x_axis in range(TRUMP_NUM):
                    end_word = self._suits_check(y_axis,x_axis)
                    if 100 > range_list[y_axis * TRUMP_NUM + x_axis] > 0:
                        if y_axis >= x_axis:
                            pio_range_output_list.append(TRUMP_LIST[x_axis] + TRUMP_LIST[y_axis] + end_word + ":" + str(range_list[y_axis * TRUMP_NUM + x_axis] / 100))
                        else:
                            pio_range_output_list.append(TRUMP_LIST[y_axis] + TRUMP_LIST[x_axis] + end_word + ":" + str(range_list[y_axis * TRUMP_NUM + x_axis] / 100))
                    if 100 == range_list[y_axis * TRUMP_NUM + x_axis]:
                        if y_axis >= x_axis:
                            pio_range_output_list.append(TRUMP_LIST[x_axis] + TRUMP_LIST[y_axis] + end_word)
                        else:
                            pio_range_output_list.append(TRUMP_LIST[y_axis] + TRUMP_LIST[x_axis] + end_word)
            print("PioSOLVERのハンドレンジ出力結果")
            print(','.join(map(str, pio_range_output_list)))

    def _suits_check(self,y_axis,x_axis):
        if y_axis < x_axis:
            end_word = "s"
        elif x_axis < y_axis:
            end_word = "o"
        else:
            end_word = ""
        return end_word

def main():
    # 各種インスタンス生成
    args_processing_process = Args_processing_process()
    image_processing_process = Image_processing_process()
    image_decision_process = Image_decision_process()
    output_result_process = Output_result_process()

    # コマンド引数の処理
    raise_bool,softname,img,tesseract_file,range_table_type = args_processing_process.args_check()
    # 入力画像の分割処理
    rects,x_one_sell,y_one_sell = image_processing_process.image_split_processing(img,range_table_type)
    # 分割した入力画像をディレクトリに格納
    image_processing_process.output_split_image_file(img,rects,x_one_sell,y_one_sell,SPLIT_TABLEFILE_DIR,range_table_type)
    # 画像処理の識別処理(OCR,色検出)
    row_list,rsise_ration_list,call_ration_list = image_processing_process.image_ocr_processing(SPLIT_TABLEFILE_DIR,tesseract_file,raise_bool,range_table_type)
    # 画像識別結果の判定処理
    range_list = image_decision_process.image_decision(row_list,rsise_ration_list,call_ration_list,raise_bool,range_table_type)
    # 結果の出力処理
    output_result_process.output_result(range_list,softname)

if __name__ == "__main__":
    main()
        



