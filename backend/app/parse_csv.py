import csv
import time

def parse_csv(file_path: str):
    all = []
    with open(file_path, mode ='r')as file:
        csvFile = csv.reader(file)
        for lines in csvFile:
            gift_details = [{
                "Date_of_Offer": lines[1],
                "Offered_to": lines[2],
                "Offered_From": lines[4],
                "Description_of_Offer": lines[5],
                "Reason_for_offer": lines[6],
                "Details_of_contract": lines[7],
                "Estimated_Gift_Value": lines[8],
                "Action_Taken": lines[9],
                "timestamp": time.time()
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