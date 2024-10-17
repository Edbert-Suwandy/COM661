import csv
import json

def parse_csv(file_path: str):
    all = []
    with open(file_path, mode ='r')as file:
        csvFile = csv.reader(file)
        for lines in csvFile:
            out = dict()
            out = {
                "Business Area": lines[0],
                "Date of Offer": lines[1],
                "Offered to": lines[2],
                "Ultimate Recipient": lines[3],
                "Offered From": lines[4],
                "Description of Offer": lines[5],
                "Reason for offer": lines[6],
                "Details of contract": lines[7],
                "Estimated Gift Value": lines[8],
                "Action Taken": lines[9]
            }
            all.append(out)
    return all