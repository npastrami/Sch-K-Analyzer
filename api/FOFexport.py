import openpyxl
from openpyxl.utils import get_column_letter
import numpy as np
import pandas as pd
import re
from io import BytesIO
from itemcodeoffsets import keyword_to_offset_dict

def process_FOF(workbook, fof_sheets):
        print(f'Preparing FOF Main')
        print(fof_sheets)
        
        # Based off 2022 IRS Intructions for K-1 (1065)
        mappings = {
            "ordinary business income": 20,
            "net rental real estate income": 21, 
            "other net rental income": 22,
            "guarenteed payments for services": 23,
            "guarenteed payments for capital": 24,
            "total guarenteed payments": 25, 
            "interest income": 26,                       
            "ordinary dividends": 27, 
            "qualified dividends": 28, 
            "dividend equivalents": 29, 
            "royalties": 30,                       
            "net short-term capital gain": 31, 
            "net long-term capital gain": 32,                      
            "collectibles": 33, 
            "unrecaptured section": 34,                        
            "net section": 35, 
            "other income": 36, 
            "section": 46,                         
            "other deductions": 47, 
            "self-employment earnings": 71, 
            "credits": 75, 
            "alternatice minimum tax": 92, 
            "tax-exempt income and nondeductible expenses": 99, 
            "distributions": 103, 
            "other information": 107, 
            "foreign taxes paid or accrued": 142,
            "withdrawls and distributions": 184,
            "partner's share of net unrecognized section": 160,  
        }
        
        target_worksheet = workbook["Sheet1"]
        starting_col = 5

        for sheet_index, fof_sheet in enumerate(fof_sheets, start=starting_col):
            # Extracting the sheet name and removing the 'FOF_' prefix
            sheet_title = fof_sheet.title.replace("FOF_", "")
            col_letter = get_column_letter(sheet_index)
            target_worksheet[f'{col_letter}9'] = sheet_title

            for row in fof_sheet.iter_rows(min_row=3):
                keyword_cell = row[0].value
                if keyword_cell and any(keyword in keyword_cell for keyword in mappings.keys()):
                    # Split the keyword and get the instance number if present
                    base_keyword, instance = re.match(r'([^\d]+)\s*(\d*)', keyword_cell).groups()
                    base_keyword = base_keyword.strip()
                    print(base_keyword)
                    instance_number = int(instance) if instance else 1

                    # Check if there is an offset needed for this keyword
                    if base_keyword in keyword_to_offset_dict:
                        print(keyword_to_offset_dict)
                        # Apply offsets for keywords that have them
                        offset_dict = keyword_to_offset_dict[base_keyword]
                        offset_key = list(offset_dict.keys())[instance_number - 1]
                        target_row = mappings[base_keyword] + offset_dict[offset_key] + 1
                    else:
                        # For keywords without offsets
                        target_row = mappings[base_keyword] + 1 

                    # Amounts are in the third column (Column C)
                    amount_cell = row[2].value
                    target_worksheet.cell(row=target_row, column=sheet_index, value=amount_cell)
    