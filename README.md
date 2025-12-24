![](proman.png)

# ProMan v0.3 (PROject MANager)
## Description:
Keep track of project progress and financials with a log editor and a finance editor with in text reference media, all in one window.

## Features
- Edit and organize project logs
- Add and remove projects
- Finance editor with a built in deficit/surplus indicator which compares total spending with your set budget.
- Reference JPG's, PDF's, DOCX's, PNG's, XLSM's and more directly in the log text using: [ref:REF_ID] where REF_ID is the reference ID which shows up above the reference material after you add it to the Reference Media section in the project detail window.
  <img width="1152" height="773" alt="Proman_detail_0v3" src="https://github.com/user-attachments/assets/69b139c1-9936-4b0f-b64c-7c4ca8ea8a9a" />
- Keep track of spending with built in status on deficit/surplus with an overview of all purchases and of what for the specific entry day. The finance editor automatically scans for purchase information from your logs using 
  <img width="1142" height="750" alt="Proman_finances_0v3" src="https://github.com/user-attachments/assets/746a47ec-ecc3-4995-a96b-48b1232abb61" />
- Export full project with financial information, all logs and a description in a pre-programmed order into a DOCX file.


## Dependencies:
- ttkthemes, tkinter
- sqlite3
- Pillow
- EASVHS (modified)

## Todo:
- Want the ability to organize all my projects according to priority and date.
- Must enforce a standard date format and be able to sort logs and projects after date.
- Add tags.

