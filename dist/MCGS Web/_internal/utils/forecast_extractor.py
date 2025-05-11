import cv2
import pytesseract
import numpy as np
import re
from typing import Union
from pprint import pprint

class ForecastDataExtractor:
    def __init__(self, tesseract_path: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        kernel = np.ones((1, 1), np.uint8)
        gray = cv2.dilate(gray, kernel, iterations=1)
        gray = cv2.erode(gray, kernel, iterations=1)
        return gray
        
    def extract_text(self, image: np.ndarray) -> str:
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, config=custom_config)

        replacements = {
            'Shif- Daa': 'Shift Data',
            'Producion': 'Production',
            'Lengththh':'Length',
            'Lengthth':'Length',
            'Lengthh':'Length',
            'Lengh': 'Length',
            'Lengt':'Length',
            'Leng':'Length',
            'Lengththh':'',
            'Lengthth':'',
            'Lengthh':'',
            'Lengh': '',
            'Lengt':'',
            'Leng':'',
            'Forec':'Forecast',
            'Forecastast':'Forecast',
            'E flicency': 'Efficiency',
            'Metre': ' ',
            'Metr':' ',
            'Metn':' ',
            'rpir':' ',
            'casti':'cast',
            'casta:':'cast',
            'rpm': ' ',
            'rpr':' ',
            'Out':'Cut',
            'pr' :' ',
            ' r ':' ',
            ' i ':' 1 ',
            ' t ':' ',
            ' l ':' ',
            't r':' ',
            '%': ' ',
            'Pick': ' ',
            ' h ':' ',
            '_':' '
        }
        for wrong, right in replacements.items():
            text = text.replace(wrong, right)

        text = re.sub(r'[^\w\s\d.:%-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def parse_matrix_data(self, text: str) -> dict:
        matrix_data = {}

        shifts = re.findall(r'Shift\s+([AB](?:\s+[AB])*)', text)
        matrix_data["Shift"] = shifts[0].split() if shifts else []

        def extract_datetime(label):
            match = re.findall(rf'{label}\s*((?:\d{{4}}-\d+-\d+ \d+:\d+:\d+\s+){{1,10}})', text)
            if match:
                raw_items = match[0].strip().split()
                return [f"{raw_items[i]} {raw_items[i+1]}" for i in range(0, len(raw_items), 2)]
            return []

        def extract_end_times(label):
            match = re.search(r'End\s+\w*\s+((?:\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}\s*){1,10})', text)
            if match:
                raw_items = match[0].strip().split()
                return [f"{raw_items[i]} {raw_items[i+1]}" for i in range(0, len(raw_items), 2)]
            return []

        def extract_numbers(label):
            pattern = rf'{label}\s+((?:[\d.]+\s*){{1,10}})'
            match = re.search(pattern, text)
            if match:
                return [float(val) if '.' in val else int(val) for val in match.group(1).split()]
            return []

        def extract_text_field(label):
            pattern = rf'{label}\s+([A-Z0-9]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else ""
         
        def extract_forecast_datetime(label):
            pattern = rf'{re.escape(label)}\s+(\d{{1,2}}-\d{{1,2}}-\d{{1,4}} \d{{1,2}}:\d{{1,2}}:\d{{1,2}})'
            match = re.search(pattern, text)
            return match.group(1) if match else ''

        def extract_single(label):
            match = re.search(rf'{label}\s+([\d.:-]+)', text)
            return match.group(1) if match else ""

        matrix_data["Start"] = extract_datetime("Start")
        matrix_data["End"] = extract_end_times("End")

        fields = [
            ("Production_FabricLength", "Production"),
            ("Production_Quantity", "Production"),
            ("Speed", "Speed"),
            ("Efficiency", "Efficiency"),
            ("TotalTimes", "Total Times"),
            ("H1Times", "H1 Times"),
            ("H2Times", "H2 Times"),
            ("WarpTimes", "Warp Times"),
            ("OtherTimes", "Other Times"),
            ("Weaving_Length", "Weaving"),
            ("Cut_Length", "Cut"),
            ("Weaving_Forecast", "Weaving Forecast"),
            ("Warp_Remain", "Warp Remain"),
            ("Warp_Length", "Warp"),
            ("Warp_Forecast", "Warp Forecast"),
            ("Device_Name","Device Name"),
            ("Loom_Num","Loom Num"),
        ]

        # Handle production separately
        try :
            prod_matches = re.findall(r'Production\s+((?:[\d.]+\s+){5,10})', text)
            if len(prod_matches) >= 2:
                matrix_data["Production_FabricLength"] = [float(val) for val in prod_matches[0].split()]
                matrix_data["Production_Quantity"] = [int(val) for val in prod_matches[1].split()]
            # print(matrix_data["Production_FabricLength"], type(matrix_data["Production_FabricLength"]),len(matrix_data["Production_FabricLength"]),"-"*10)
            # print(matrix_data["Production_Quantity"], type(matrix_data["Production_Quantity"]),len(matrix_data["Production_Quantity"]),"-"*10)
            
            if len(matrix_data["Production_FabricLength"])<2:
                fabric_match = re.search(r'(?<!3K\s)Production\s+((?:[\d.]+\s+){3,10})', text)
                if fabric_match:
                    matrix_data["Production_FabricLength"] = [float(val) for val in fabric_match.group(1).split()]

            # Extract 3K Production Quantity
            if len(matrix_data["Production_Quantity"])<2:
                quantity_match = re.search(r'3K\s+Production\s+((?:\d+\s+){3,10})', text)
                if quantity_match:
                    matrix_data["Production_Quantity"] = [int(val) for val in quantity_match.group(1).split()]
        
        except Exception as e:
            print(f"Error in Data Extractor: {e}")

        for key, label in fields[2:]:  # Skip first two Production
            if key in ["Weaving_Forecast", "Warp_Forecast"]:
                matrix_data[key] = extract_forecast_datetime(label)
            elif key in ["Weaving_Length", "Cut_Length", "Warp_Remain", "Warp_Length"]:
                matrix_data[key] = extract_single(label)
            elif key in ["Loom_Num","Device_Name"]:
                matrix_data[key]=extract_text_field(label)   
            else:
                matrix_data[key] = extract_numbers(label)

        return matrix_data

    def extract_from_image(self, image_input: Union[str, np.ndarray]) -> dict:
        if isinstance(image_input, str):
            image = cv2.imread(image_input)
        else:
            image = image_input

        processed = self.preprocess_image(image)
        text = self.extract_text(processed)
        return self.parse_matrix_data(text),text
