import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment
import numpy as np
import pandas as pd
import re
from io import BytesIO
from itemcodeoffsets import keyword_to_offset_dict

def process_FOF(workbook, fof_sheets):   
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
                    # match base keyword
                    base_keyword = re.match(r'([^\d]+)\s*(\d*)', keyword_cell).groups()[0]
                    base_keyword = base_keyword.strip()
                    # fetch item code associated with keyword instance
                    item_code = row[1].value 

                    # Check if there is an offset needed for this keyword
                    if base_keyword in keyword_to_offset_dict:
                        # Apply offset relative to 'X' item code associated with the keyword in the item code offset dictionary
                        offset_dict = keyword_to_offset_dict[base_keyword]
                        # Check if the item code is in the offset dictionary for this keyword
                        if item_code in offset_dict:
                            offset = offset_dict[item_code]
                            target_row = mappings[base_keyword] + offset + 1
                            print(f'Target row for {base_keyword} with item code {item_code} is {target_row}')
                        else:
                            # add the amount to an array of keywords with invalid item codes, but do not print this amount in the excel sheet
                            print(f'Item code {item_code} is not in the offset dictionary for {base_keyword}')
                            continue
                    else:
                        # For keywords without offsets
                        target_row = mappings[base_keyword] + 1 
                    print(f'final target row: {target_row},for {base_keyword} with item code {item_code} ')
                    # Amounts are in the third column (Column C)
                    amount_cell = row[2].value
                    target_worksheet.cell(row=target_row, column=sheet_index, value=amount_cell)
                    
        for col in range(1, target_worksheet.max_column + 1):
                col_letter = get_column_letter(col)
                target_worksheet.column_dimensions[col_letter].width = 25  # Approximate conversion

        # Set text wrap for row 9
        for col in range(1, target_worksheet.max_column + 1):
            cell = target_worksheet.cell(row=9, column=col)
            cell.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')

        # Rename the worksheet
        target_worksheet.title = "FOF_Data"
    