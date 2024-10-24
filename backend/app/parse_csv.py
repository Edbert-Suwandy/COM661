import csv
from datetime import datetime 

def parse_csv(file_path: str):
    all = []
    with open(file_path, mode ='r')as file:
        csvFile = csv.reader(file)
        for lines in csvFile:
            try:
                date = datetime.strptime(lines[1],'%d/%m/%Y').isoformat()
            except:
                # set default value to 00/00/0000
                date = datetime.strptime("01/01/2000", '%d/%m/%Y').isoformat()

            gift_details = [{
                # need error handling
                "Date_of_Offer": date,
                "Offered_to": lines[2],
                "Offered_From": lines[4],
                "Description_of_Offer": lines[5],
                "Reason_for_offer": lines[6],
                "Details_of_c ontract": lines[7],
                "Estimated_Gift_Value": lines[8],
                "Action_Taken": lines[9],
                "timestamp": datetime.now().isoformat() 
            }] 
            out = {
                "Business_Area": lines[0],
                "Ultimate_Recipient": get_recipient(lines[2],lines[3]),
                "Gifts" : gift_details     
            }
            all.append(out)
        return all

# We want ultimate recipent
def get_recipient(recipient: str, ultimate_recipeint: str) -> str:
    if ultimate_recipeint:
        return ultimate_recipeint
    else:
        return recipient
